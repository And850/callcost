"""LM Studio native REST v1. A load selects installed weights, not precision."""

import time
import uuid

from callcost.providers.streaming import append_answer, stream_request
from callcost.schemas import nonnegative_number, render_prompt, token_count


class LMStudioProvider:
    def __init__(self, configuration, settings, run, client, api_key=None):
        self.configuration = configuration
        self.settings = settings
        self.run = run
        self.client = client
        self.headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
        self.instance_id = None

    def prepare(self):
        response = self.client.get(self.settings.base_url + '/api/v1/models', headers=self.headers,
                                   timeout=self.run.timeout_seconds)
        response.raise_for_status()
        models = response.json()['models']
        matches = [m for m in models if m['key'] == self.configuration.model_key
                   or self.configuration.model_key in m.get('variants', [])]
        if len(matches) != 1:
            raise ValueError('Exact installed model variant not found uniquely')
        model = matches[0]
        quant = (model.get('quantization') or {}).get('name')
        if model['key'] != self.configuration.model_key:
            quant = self.configuration.model_key.rsplit('@', 1)[-1]
        if not quant or quant.casefold() != self.configuration.expected_quantisation.casefold():
            raise ValueError('Installed quantisation does not match configuration')
        if any(m.get('loaded_instances') for m in models):
            raise ValueError('Unload existing LM Studio model instances before benchmarking')
        start = time.perf_counter()
        response = self.client.post(self.settings.base_url + '/api/v1/models/load', headers=self.headers,
                                    json={'model': self.configuration.model_key,
                                          'context_length': self.settings.context_length,
                                          'echo_load_config': True}, timeout=self.run.timeout_seconds)
        duration = time.perf_counter() - start
        response.raise_for_status()
        data = response.json()
        self.instance_id = data['instance_id']
        if data.get('status') != 'loaded':
            raise ValueError('LM Studio did not confirm model load')
        if data.get('load_config', {}).get('context_length') != self.settings.context_length:
            raise ValueError('LM Studio did not confirm the requested context length')
        return {'load_id': uuid.uuid4().hex, 'configuration_id': self.configuration.id,
                'request_wall_s': duration, 'provider_load_s': nonnegative_number(data.get('load_time_seconds')),
                'instance_id': self.instance_id, 'load_config': data['load_config'], 'listed_model': model,
                'cache_control': 'not_exposed_by_documented_rest_v1', 'cache_state': 'unknown'}

    def close(self):
        if self.instance_id:
            response = self.client.post(self.settings.base_url + '/api/v1/models/unload', headers=self.headers,
                                        json={'instance_id': self.instance_id}, timeout=self.run.timeout_seconds)
            response.raise_for_status()
            self.instance_id = None

    def generate(self, prompt, raw_directory, call_id):
        if self.instance_id is None:
            raise ValueError('Model must be explicitly loaded before measurement')
        payload = {'model': self.instance_id, 'input': render_prompt(prompt), 'stream': True,
                   'store': False, 'temperature': self.run.temperature,
                   'max_output_tokens': self.run.max_output_tokens}
        if self.configuration.reasoning is not None:
            payload['reasoning'] = self.configuration.reasoning
        result = stream_request(self.client, self.settings.base_url + '/api/v1/chat', payload,
                                self.headers, raw_directory, call_id, self._consume,
                                timeout=self.run.timeout_seconds)
        result.input_tokens = token_count(result.usage.get('input_tokens'))
        total = token_count(result.usage.get('total_output_tokens'))
        result.thinking_tokens = token_count(result.usage.get('reasoning_output_tokens'))
        if total is not None and result.thinking_tokens is not None and total >= result.thinking_tokens:
            result.output_tokens = total - result.thinking_tokens
        result.decode_tokens_per_second = nonnegative_number(result.usage.get('tokens_per_second'))
        result.provider_ttft_s = nonnegative_number(result.usage.get('time_to_first_token_seconds'))
        result.list_price_cost = '0'
        result.missing['currency'] = 'No local API charge; not an electricity or hardware price'
        for field in ('input_tokens', 'output_tokens', 'thinking_tokens', 'decode_tokens_per_second', 'truncated'):
            if getattr(result, field) is None:
                result.missing[field] = 'Not reported by native REST response'
        return result

    def _consume(self, event, now, result):
        kind = event.get('type')
        if kind == 'chat.start':
            if event['model_instance_id'] != self.instance_id:
                raise ValueError('Unexpected model instance in stream')
        elif kind == 'model_load.start':
            result.error = 'Unexpected model load inside measured call'
        elif kind == 'message.delta':
            append_answer(event['content'], now, result)
        elif kind == 'error':
            result.error = 'Provider reported a streaming error'
        elif kind == 'chat.end':
            final = event['result']
            result.model_reported = final['model_instance_id']
            if result.model_reported != self.instance_id:
                raise ValueError('Unexpected model instance in final response')
            answer = ''.join(item['content'] for item in final['output'] if item['type'] == 'message')
            if answer != result.answer:
                raise ValueError('Streamed text differs from final answer')
            result.usage = final.get('stats', {})
            result.status = 'completed'
