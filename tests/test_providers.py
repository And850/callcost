import json

import httpx
import pytest

from callcost.providers.gemini import GeminiProvider
from callcost.providers.lmstudio import LMStudioProvider
from callcost.schemas import Config, Dataset, LMStudioSettings, LocalConfig, RunSettings


class Fragments(httpx.SyncByteStream):
    def __init__(self, body):
        self.body = body

    def __iter__(self):
        # Splits UTF-8 characters, JSON strings and SSE delimiters.
        for i in range(0, len(self.body), 3):
            yield self.body[i:i + 3]


def sse(events):
    return b''.join(('data: ' + json.dumps(e, ensure_ascii=False) + '\r\n\r\n').encode() for e in events)


def test_gemini_stream_usage_thinking_and_exact_payload(config_data, prompt_data, tmp_path):
    config_data['configurations'][0]['thinking'] = {'budget': 0}
    config = Config.model_validate(config_data)
    body = sse([
        {'candidates': [{'content': {'parts': [{'text': 'private thought', 'thought': True}]}}]},
        {'candidates': [{'content': {'parts': [{'text': 'Answer: 雪4'}]}}]},
        {'candidates': [{'finishReason': 'STOP'}], 'modelVersion': 'gemini-test-001',
         'usageMetadata': {'promptTokenCount': 100, 'candidatesTokenCount': 4, 'thoughtsTokenCount': 6}},
    ])
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(200, stream=Fragments(body))
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        provider = GeminiProvider(config.configurations[0], config.run, client, 'secret')
        result = provider.generate(Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'call')
    sent = json.loads(requests[0].content)
    assert sent['generationConfig']['thinkingConfig'] == {'thinkingBudget': 0}
    assert 'scoring' not in json.dumps(sent)
    assert result.status == 'completed'
    assert result.answer == 'Answer: 雪4'
    assert result.output_tokens == 4 and result.thinking_tokens == 6
    assert result.billable_output_tokens == 10
    assert result.list_price_cost == '0.00018'
    assert result.response_payload_bytes == len(body)
    assert result.request_payload_bytes == len(requests[0].content)
    assert result.ttft_s is not None
    assert result.decode_tokens_per_second is None
    assert (tmp_path / 'call.response.bin').read_bytes() == body
    assert 'secret' not in (tmp_path / 'call.request.json').read_text()


@pytest.mark.parametrize('status,events', [(429, []), (200, [{'candidates': [{'content': {'parts': [{'text': 'partial'}]}}]}])])
def test_failures_not_retried_or_disguised_as_success(config_data, prompt_data, tmp_path, status, events):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(status, stream=Fragments(sse(events)))
    config = Config.model_validate(config_data)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'call')
    assert len(calls) == 1
    assert result.status == 'error'
    assert result.list_price_cost is None
    assert result.latency_s is not None


def test_missing_gemini_usage_is_not_zero(config_data, prompt_data, tmp_path):
    config = Config.model_validate(config_data)
    body = sse([{'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '4'}]}}]}])
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Fragments(body)))) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'call')
    assert result.status == 'completed'
    assert result.input_tokens is None and result.list_price_cost is None


def local_config():
    return LocalConfig(id='q4', provider='lmstudio', model_key='test@4bit',
                       expected_quantisation='4bit', model_files=['/tmp/test.4bit.gguf'])


def test_lmstudio_explicit_load_stream_and_unload(tmp_path, prompt_data):
    paths = []
    body = sse([
        {'type': 'chat.start', 'model_instance_id': 'instance'},
        {'type': 'reasoning.delta', 'content': 'thinking'},
        {'type': 'message.delta', 'content': ''},
        {'type': 'message.delta', 'content': 'Answer: 4'},
        {'type': 'chat.end', 'result': {'model_instance_id': 'instance',
            'output': [{'type': 'message', 'content': 'Answer: 4'}],
            'stats': {'input_tokens': 9, 'total_output_tokens': 5, 'reasoning_output_tokens': 2,
                      'tokens_per_second': 21.5, 'time_to_first_token_seconds': 0.2}}},
    ])
    def handle(request):
        paths.append(request.url.path)
        if request.url.path.endswith('/models'):
            return httpx.Response(200, json={'models': [{'key': 'test@4bit', 'format': 'mlx', 'quantization': {'name': '4bit'}, 'loaded_instances': []}]})
        if request.url.path.endswith('/load'):
            return httpx.Response(200, json={'instance_id': 'instance', 'status': 'loaded', 'load_time_seconds': 0.3, 'load_config': {'context_length': 4096}})
        if request.url.path.endswith('/unload'):
            assert json.loads(request.content) == {'instance_id': 'instance'}
            return httpx.Response(200, json={'instance_id': 'instance'})
        payload = json.loads(request.content)
        assert payload['model'] == 'instance' and payload['store'] is False
        assert payload['temperature'] == 0 and payload['max_output_tokens'] == 1024
        return httpx.Response(200, stream=Fragments(body))
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        p = LMStudioProvider(local_config(), LMStudioSettings(), RunSettings(), client)
        load = p.prepare()
        result = p.generate(Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'call')
        p.close()
    assert load['provider_load_s'] == 0.3
    assert result.status == 'completed' and result.answer == 'Answer: 4'
    assert result.output_tokens == 3 and result.thinking_tokens == 2
    assert result.decode_tokens_per_second == 21.5
    assert paths == ['/api/v1/models', '/api/v1/models/load', '/api/v1/chat', '/api/v1/models/unload']


def test_local_quantisation_mismatch_prevents_load():
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={'models': [{'key': 'test@4bit', 'format': 'mlx', 'quantization': {'name': '8bit'}, 'loaded_instances': []}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match='quantisation'):
            LMStudioProvider(local_config(), LMStudioSettings(), RunSettings(), client).prepare()
    assert len(requests) == 1


def test_gemini_zero_thinking_from_complete_accounting(config_data, prompt_data, tmp_path):
    event = {'candidates': [{'content': {'parts': [{'text': 'Answer: 4'}]}, 'finishReason': 'STOP'}],
             'usageMetadata': {'promptTokenCount': 20, 'candidatesTokenCount': 4, 'totalTokenCount': 24}}
    config = Config.model_validate(config_data)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Fragments(sse([event]))))) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'zero')
    assert result.thinking_tokens == 0
    assert result.thinking_tokens_source.startswith('totalTokenCount -')
    assert result.billable_output_tokens == 4


def test_grouped_mlx_alias_loads_only_matching_selected_variant(tmp_path):
    config = LocalConfig(id='local', provider='lmstudio', model_key='qwen/model@4bit',
                         expected_quantisation='4bit', model_files=['weights.safetensors'])
    requests = []
    def handle(request):
        requests.append(request)
        if request.method == 'GET':
            return httpx.Response(200, json={'models': [{'key': 'qwen/model', 'format': 'mlx',
                'variants': ['qwen/model@4bit', 'qwen/model@8bit'], 'selected_variant': 'qwen/model@4bit',
                'quantization': {'name': '4bit'}, 'loaded_instances': []}]})
        return httpx.Response(200, json={'instance_id': 'loaded', 'status': 'loaded',
                                        'load_config': {'context_length': 4096}})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        LMStudioProvider(config, LMStudioSettings(), RunSettings(), client).prepare()
    assert json.loads(requests[1].content)['model'] == 'qwen/model'
    requests.clear()
    config.model_key = 'qwen/model@8bit'
    config.expected_quantisation = '8bit'
    with httpx.Client(transport=httpx.MockTransport(handle)) as client, pytest.raises(ValueError, match='selected'):
        LMStudioProvider(config, LMStudioSettings(), RunSettings(), client).prepare()
    assert len(requests) == 1


def test_captured_mlx_pilot_stream_verifies_zero_thinking(tmp_path):
    from pathlib import Path

    from callcost.schemas import Prompt
    from callcost.thinking import verify_thinking_off
    body = (Path(__file__).parent / 'fixtures/lmstudio-0.4.24-mlx4bit.sse').read_bytes()
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Fragments(body)))) as client:
        provider = LMStudioProvider(local_config(), LMStudioSettings(), RunSettings(), client)
        provider.instance_id = 'qwen/qwen3.5-9b'
        prompt = Prompt(id='fixture', task_type='pilot', prompt='held-out fixture',
                        scoring={'type': 'numeric_final_line', 'expected': '12'})
        result = provider.generate(prompt, tmp_path, 'captured')
    assert verify_thinking_off(result)['verified']
    assert result.thinking_tokens == 0 and result.output_tokens == 68 and result.input_tokens == 38
    assert result.answer.endswith('Answer: 12')


def test_gemini_level_is_sent_without_budget_and_thoughts_are_billed(config_data, prompt_data, tmp_path):
    config_data['configurations'][0]['thinking'] = {'thinking_level': 'low'}
    config_data['configurations'][0]['model'] = 'gemini-3.8-flash'
    config = Config.model_validate(config_data)
    def handle(request):
        payload = json.loads(request.content)
        assert payload['generationConfig']['thinkingConfig'] == {'thinkingLevel': 'low'}
        event = {'candidates': [{'content': {'parts': [{'thought': True, 'text': 'reasoning'},
                                                        {'text': 'Answer: 4'}]}, 'finishReason': 'STOP'}],
                 'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 4,
                                   'thoughtsTokenCount': 6, 'totalTokenCount': 20}}
        return httpx.Response(200, stream=Fragments(sse([event])))
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'level')
    assert result.answer == 'Answer: 4' and result.reasoning_content_observed
    assert result.thinking_tokens == 6 and result.billable_output_tokens == 10
    assert result.list_price_cost == '0.000045'


@pytest.mark.parametrize('code', [500, 503])
def test_cloud_transient_retries_preserve_attempts(config_data, prompt_data, tmp_path, monkeypatch, code):
    import time
    waits = []
    monkeypatch.setattr(time, 'sleep', waits.append)
    count = 0
    def handle(request):
        nonlocal count
        count += 1
        if count < 3:
            return httpx.Response(code, stream=Fragments(b'busy'))
        return httpx.Response(200, stream=Fragments(sse([{'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'Answer: 4'}]}}], 'usageMetadata': {'promptTokenCount': 2, 'candidatesTokenCount': 3, 'thoughtsTokenCount': 1}}])))
    config = Config.model_validate(config_data)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'retry-call')
    assert result.status == 'completed' and count == 3
    assert waits == [10, 30]
    attempts = json.loads((tmp_path / 'retry-call.attempts.json').read_text())
    assert len(attempts) == 3 and attempts[0]['error'] and attempts[0]['started_at']
    assert attempts[-1]['latency_s'] == result.latency_s
    assert (tmp_path / 'retry-call.attempt-1.response.bin').exists()


def test_cloud_retry_exhaustion(config_data, prompt_data, tmp_path, monkeypatch):
    import time
    waits = []
    monkeypatch.setattr(time, 'sleep', waits.append)
    config = Config.model_validate(config_data)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503, stream=Fragments(b'busy')))) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'exhausted')
    assert result.status == 'error'
    assert waits == [10, 30, 90, 270]
    assert len(json.loads((tmp_path / 'exhausted.attempts.json').read_text())) == 5


@pytest.mark.parametrize('http_status,error_status', [(401,'UNAUTHENTICATED'),(403,'PERMISSION_DENIED'),(402,'PAYMENT_REQUIRED'),(429,'RESOURCE_EXHAUSTED'),(503,'RESOURCE_EXHAUSTED')])
def test_cloud_never_retries_auth_billing_quota(config_data, prompt_data, tmp_path, monkeypatch, http_status, error_status):
    import time
    waits, calls = [], []
    monkeypatch.setattr(time, 'sleep', waits.append)
    def handle(request):
        calls.append(request)
        return httpx.Response(http_status, stream=Fragments(json.dumps({'error': {'status': error_status}}).encode()))
    config = Config.model_validate(config_data)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = GeminiProvider(config.configurations[0], config.run, client, 'key').generate(
            Dataset.model_validate(prompt_data).prompts[0], tmp_path, 'forbidden')
    assert result.status == 'error' and len(calls) == 1 and waits == []
