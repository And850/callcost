"""Verify observed behaviour, not just the requested thinking setting."""

import re


def verify_thinking_off(result, *, require_answer=True):
    if result.status != 'completed' or (require_answer and not result.answer):
        raise ValueError('Thinking-off verification requires a completed response (and non-empty pilot)')
    if result.thinking_tokens != 0:
        raise ValueError('Thinking-off verification did not establish zero reasoning tokens')
    if result.reasoning_content_observed or re.search(r'<\s*/?\s*think\b', result.answer, re.IGNORECASE):
        raise ValueError('Thinking content observed despite thinking-off setting')
    return {'verified': True, 'reasoning_tokens': 0, 'tokens_source': result.thinking_tokens_source,
            'reasoning_content_observed': False, 'think_tags_observed': False}


def verify_cloud_thinking(result, level, *, require_answer=True):
    if result.status != 'completed' or (require_answer and not result.answer):
        raise ValueError('Cloud pilot requires a completed, nonempty answer')
    if result.thinking_tokens is None:
        raise ValueError('Cloud thinking-token accounting unavailable')
    return {'verified': True, 'requested_level': level, 'disabled': False,
            'verification_scope': 'request level recorded; token accounting observed, effective internal level not exposed',
            'reasoning_tokens': result.thinking_tokens, 'tokens_source': result.thinking_tokens_source,
            'reasoning_content_observed': result.reasoning_content_observed}
