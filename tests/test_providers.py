import json

import httpx
import pytest

from callcost.providers.gemini import GeminiProvider
from callcost.providers.lmstudio import LMStudioProvider
from callcost.schemas import Config, Dataset, LocalConfig, LMStudioSettings, RunSettings


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
    config_data['configurations'][0]['thinking'] = {'budget': 128}
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
    assert sent['generationConfig']['thinkingConfig'] == {'thinkingBudget': 128}
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
    return LocalConfig(id='q4', provider='lmstudio', model_key='test@q4_k_m',
                       expected_quantisation='Q4_K_M', model_files=['/tmp/test.Q4_K_M.gguf'])


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
            return httpx.Response(200, json={'models': [{'key': 'test@q4_k_m', 'quantization': {'name': 'Q4_K_M'}, 'loaded_instances': []}]})
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
        return httpx.Response(200, json={'models': [{'key': 'test@q4_k_m', 'quantization': {'name': 'Q8_0'}, 'loaded_instances': []}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match='quantisation'):
            LMStudioProvider(local_config(), LMStudioSettings(), RunSettings(), client).prepare()
    assert len(requests) == 1
