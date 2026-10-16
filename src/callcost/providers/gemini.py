"""Gemini generateContent streaming with explicit thinking and list prices."""

from decimal import Decimal

from callcost.providers.streaming import append_answer, stream_request
from callcost.schemas import render_prompt, token_count


class GeminiProvider:
    def __init__(self, configuration, run, client, api_key):
        if not api_key:
            raise ValueError(f'Missing credential environment variable {configuration.api_key_env}')
        self.configuration = configuration
        self.run = run
        self.client = client
        self.api_key = api_key

    def prepare(self):
        return None

    def close(self):
        pass

    def generate(self, prompt, raw_directory, call_id):
        setting = self.configuration.thinking
        thinking = ({'thinkingLevel': setting.thinking_level} if setting.thinking_level is not None
                    else {'thinkingBudget': setting.budget})
        payload = {
            'contents': [{'role': 'user', 'parts': [{'text': render_prompt(prompt)}]}],
            'generationConfig': {'temperature': self.run.temperature,
                                 'maxOutputTokens': self.run.max_output_tokens,
                                 'candidateCount': 1, 'thinkingConfig': thinking},
        }
        result = stream_request(
            self.client,
            f'https://generativelanguage.googleapis.com/v1beta/models/{self.configuration.model}:streamGenerateContent?alt=sse',
            payload, {'x-goog-api-key': self.api_key}, raw_directory, call_id,
            self._consume, timeout=self.run.timeout_seconds)
        usage = result.usage
        result.input_tokens = token_count(usage.get('promptTokenCount'))
        result.output_tokens = token_count(usage.get('candidatesTokenCount'))
        result.thinking_tokens = token_count(usage.get('thoughtsTokenCount'))
        if result.thinking_tokens is not None:
            result.thinking_tokens_source = 'usageMetadata.thoughtsTokenCount'
        elif 'thoughtsTokenCount' not in usage:
            total = token_count(usage.get('totalTokenCount'))
            tools = token_count(usage.get('toolUsePromptTokenCount', 0))
            if all(x is not None for x in (total, tools, result.input_tokens, result.output_tokens)):
                residual = total - tools - result.input_tokens - result.output_tokens
                if residual >= 0:
                    result.thinking_tokens = residual
                    result.thinking_tokens_source = 'totalTokenCount - promptTokenCount - candidatesTokenCount - toolUsePromptTokenCount'
        result.cached_input_tokens = token_count(usage.get('cachedContentTokenCount'))
        if result.output_tokens is not None and result.thinking_tokens is not None:
            result.billable_output_tokens = result.output_tokens + result.thinking_tokens
        pricing = self.configuration.pricing
        result.currency = pricing.currency
        if result.input_tokens is not None and result.billable_output_tokens is not None:
            cost = (result.input_tokens * pricing.input_per_million
                    + result.billable_output_tokens * pricing.output_per_million) / Decimal(1_000_000)
            result.list_price_cost = str(cost)
        else:
            result.missing['list_price_cost'] = 'Provider token usage incomplete'
        for field in ('input_tokens', 'output_tokens', 'thinking_tokens', 'cached_input_tokens'):
            if getattr(result, field) is None:
                result.missing[field] = 'Not reported by provider'
        result.missing['decode_tokens_per_second'] = 'Server decode timing not exposed by Gemini'
        return result

    @staticmethod
    def _consume(event, now, result):
        if event.get('error'):
            if event['error'].get('status') in ('RESOURCE_EXHAUSTED', 'PAYMENT_REQUIRED'):
                result.provider_error_status = event['error']['status']
            elif event['error'].get('code') == 402:
                result.provider_error_status = 'PAYMENT_REQUIRED'
            result.error = 'Provider reported a streaming error'
        if 'modelVersion' in event:
            result.model_reported = event['modelVersion']
        if 'usageMetadata' in event:
            # Counts are cumulative. Adding each event would overstate costs.
            result.usage.update(event['usageMetadata'])
        if event.get('promptFeedback', {}).get('blockReason'):
            result.finish_reason = event['promptFeedback']['blockReason']
            result.status = 'completed'
            result.truncated = False
        for candidate in event.get('candidates', []):
            if candidate.get('index', 0) != 0:
                raise ValueError('Unexpected extra response candidate')
            for part in candidate.get('content', {}).get('parts', []):
                if part.get('thought') and part.get('text'):
                    result.reasoning_content_observed = True
                if 'text' in part and not part.get('thought', False):
                    append_answer(part['text'], now, result)
            if candidate.get('finishReason'):
                result.finish_reason = candidate['finishReason']
                result.truncated = result.finish_reason == 'MAX_TOKENS'
                result.status = 'completed'
