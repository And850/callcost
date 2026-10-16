"""Provider observations. Nullable measurements never mean zero."""

from dataclasses import dataclass, field


@dataclass
class CallResult:
    status: str = 'error'
    error: str | None = None
    answer: str = ''
    started_at: str | None = None
    started_monotonic: float | None = None
    ended_monotonic: float | None = None
    latency_s: float | None = None
    ttft_s: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None
    thinking_tokens_source: str | None = None
    reasoning_content_observed: bool = False
    billable_output_tokens: int | None = None
    cached_input_tokens: int | None = None
    decode_tokens_per_second: float | None = None
    provider_ttft_s: float | None = None
    request_payload_bytes: int = 0
    response_payload_bytes: int = 0
    list_price_cost: str | None = None
    currency: str | None = None
    model_reported: str | None = None
    finish_reason: str | None = None
    truncated: bool | None = None
    missing: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


CALL_FIELDS = [
    'call_id', 'schedule_index', 'segment_id', 'configuration_id', 'configuration_label', 'comparison_role', 'provider', 'prompt_id', 'task_type', 'repeat',
    'phase', 'cache_stratum', 'load_id', 'model_files', 'quantisation',
    *CallResult.__dataclass_fields__, 'memory_peak_rss_bytes', 'memory_missing_reason',
    'memory_peak_footprint_bytes', 'footprint_missing_reason', 'loaded_weight_bytes',
    'swapins_pages', 'swapouts_pages', 'pageouts_pages', 'swapins_bytes', 'swapouts_bytes', 'pageouts_bytes',
    'swapping_occurred', 'swap_missing_reason', 'knee_eligible',
    'swap_volume_bytes', 'swap_used_before_bytes', 'swap_used_after_bytes',
    'compressed_memory_before_bytes', 'compressed_memory_after_bytes',
    'swap_observation_missing', 'swap_snapshot_before', 'swap_snapshot_after',
    'energy_j', 'energy_missing_reason', 'energy_scope', 'conditions',
    'answer_sha256', 'varies_from_first_answer', 'raw_request', 'raw_response',
]
