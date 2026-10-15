"""Strict, versioned inputs. Scoring rules never become model instructions."""

import json
import math
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

import yaml
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

Name = Annotated[str, Field(min_length=1, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')]
PositiveInt = Annotated[StrictInt, Field(gt=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class AutomaticCheck(StrictModel):
    type: Literal['substring', 'regex', 'valid_json', 'max_words']
    value: str | StrictInt | None = Field(default=None, validation_alias=AliasChoices('value', 'pattern'))
    case_sensitive: bool = True

    @model_validator(mode='after')
    def check_value(self):
        if self.type == 'max_words':
            if type(self.value) is not int or self.value < 0:
                raise ValueError('max_words requires a nonnegative integer value')
        elif self.type != 'valid_json' and (not isinstance(self.value, str) or not self.value):
            raise ValueError('Substring and regex checks require a non-empty string value')
        if self.type == 'regex':
            re.compile(self.value)
        return self


class Criterion(StrictModel):
    id: Name
    description: Annotated[str, Field(min_length=1)]
    automatic: AutomaticCheck | None = None
    human: bool = False

    @model_validator(mode='after')
    def one_judge(self):
        if (self.automatic is not None) == self.human:
            raise ValueError('Each criterion must have exactly one automatic or human check')
        return self


class Checklist(StrictModel):
    type: Literal['checklist']
    items: Annotated[list[Criterion], Field(min_length=1)]

    @model_validator(mode='after')
    def unique_ids(self):
        require_unique([item.id for item in self.items])
        return self


class NumericRule(StrictModel):
    type: Literal['numeric_final_line']
    expected: Decimal
    absolute_tolerance: Annotated[Decimal, Field(ge=0)] = Decimal('0')


class ExpectedAnswer(StrictModel):
    type: Literal['expected_answer']
    expected: str


class Source(StrictModel):
    dataset: str
    revision: str
    row_index: Annotated[StrictInt, Field(ge=0)]
    url: str


class Prompt(StrictModel):
    id: Name
    task_type: Name
    prompt: Annotated[str, Field(min_length=1)]
    input: str | None = None
    scoring: Annotated[Checklist | NumericRule | ExpectedAnswer, Field(discriminator='type')]
    source: Source | None = None


class Dataset(StrictModel):
    schema_version: Literal[1]
    prompts: Annotated[list[Prompt], Field(min_length=1)]

    @model_validator(mode='after')
    def unique_ids(self):
        require_unique([p.id for p in self.prompts])
        return self


class RunSettings(StrictModel):
    repeats: Annotated[StrictInt, Field(ge=5)] = 5
    warmup_runs: Annotated[StrictInt, Field(ge=0)] = 2
    temperature: Annotated[float, Field(ge=0, le=2)] = 0
    max_output_tokens: PositiveInt = 1024
    shuffle_seed: StrictInt = 2027
    timeout_seconds: Annotated[float, Field(gt=0)] = 180
    cooldown_seconds: Annotated[float, Field(ge=0)] = 0


class EnergySettings(StrictModel):
    mode: Literal['off', 'optional_powermetrics', 'required_powermetrics'] = 'optional_powermetrics'
    sample_ms: PositiveInt = 250
    idle_baseline_seconds: Annotated[float, Field(gt=0)] = 10


class MeasurementSettings(StrictModel):
    memory_sample_ms: PositiveInt = 100
    # Explicit process roots allow identification when a worker is reparented.
    lmstudio_process_ids: list[PositiveInt] = Field(default_factory=list)
    energy: EnergySettings = Field(default_factory=EnergySettings)


class LMStudioSettings(StrictModel):
    base_url: str = 'http://127.0.0.1:1234'
    context_length: PositiveInt = 4096
    cache_policy: Literal['disable_if_supported_else_split'] = 'disable_if_supported_else_split'
    api_key_env: Name | None = None

    @field_validator('base_url')
    @classmethod
    def local_only(cls, value):
        parsed = urlparse(value)
        if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('LM Studio must run on this Mac over loopback')
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise ValueError('Use a loopback origin without credentials, query or path')
        return value.rstrip('/')


class LocalConfig(StrictModel):
    id: Name
    label: Annotated[str, Field(min_length=1)] | None = None
    comparison_role: Literal['quantisation_series', 'production_reference'] = 'quantisation_series'
    provider: Literal['lmstudio']
    model_key: Annotated[str, Field(min_length=1)]
    expected_quantisation: Annotated[str, Field(min_length=1)]
    model_files: Annotated[list[Path], Field(min_length=1)]
    reasoning: Literal['off'] = 'off'
    model_format: Literal['mlx', 'gguf'] = 'mlx'


class Thinking(StrictModel):
    budget: Annotated[StrictInt, Field(ge=0, le=0)] | None = None
    thinking_level: Literal['low', 'medium', 'high'] | None = None

    @model_validator(mode='after')
    def one_control(self):
        if (self.budget is None) == (self.thinking_level is None):
            raise ValueError('Set exactly one thinking control: budget: 0 or thinking_level')
        return self


class Pricing(StrictModel):
    currency: Annotated[str, Field(pattern=r'^[A-Z]{3}$')]
    input_per_million: Annotated[Decimal, Field(ge=0)]
    output_per_million: Annotated[Decimal, Field(ge=0)]
    source_url: Annotated[str, Field(pattern=r'^https://')]
    checked_on: date


class GeminiConfig(StrictModel):
    id: Name
    provider: Literal['gemini']
    model: Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    api_key_env: Name = 'GEMINI_API_KEY'
    thinking: Thinking
    pricing: Pricing

    @model_validator(mode='after')
    def model_thinking_control(self):
        if self.model == 'gemini-3.8-flash' and self.thinking.thinking_level is None:
            raise ValueError('gemini-3.8-flash requires thinking_level; thinking cannot be disabled')
        return self


class Config(StrictModel):
    schema_version: Literal[1]
    run: RunSettings = Field(default_factory=RunSettings)
    measurement: MeasurementSettings = Field(default_factory=MeasurementSettings)
    lmstudio: LMStudioSettings = Field(default_factory=LMStudioSettings)
    configurations: Annotated[list[Annotated[LocalConfig | GeminiConfig, Field(discriminator='provider')]], Field(min_length=1)]

    @model_validator(mode='after')
    def unique_ids(self):
        require_unique([c.id for c in self.configurations])
        formats = {c.model_format for c in self.configurations if isinstance(c, LocalConfig)}
        if len(formats) > 1:
            raise ValueError('Do not mix MLX and GGUF within an experiment')
        return self


def require_unique(values):
    if len(values) != len(set(values)):
        raise ValueError('Duplicate IDs are not allowed')


def _mapping(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate mapping key: {key}')
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    pass


def _yaml_mapping(loader, node):
    return _mapping([(loader.construct_object(k), loader.construct_object(v)) for k, v in node.value])


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _yaml_mapping)


def load_document(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    data = json.loads(text, object_pairs_hook=_mapping) if path.suffix == '.json' else yaml.load(text, Loader=UniqueLoader)
    if not isinstance(data, dict):
        raise ValueError('Document root must be a mapping')
    return data


def render_prompt(prompt: Prompt) -> str:
    return prompt.prompt if prompt.input is None else f'{prompt.prompt}\n\nInput:\n{prompt.input}'


def token_count(value):
    """Reject bools, negative values and approximations rather than invent usage."""
    return value if type(value) is int and value >= 0 else None


def nonnegative_number(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None
