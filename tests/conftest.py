import pytest


@pytest.fixture
def config_data():
    return {"schema_version": 1, "configurations": [{
        "id": "cloud", "provider": "gemini", "model": "gemini-test",
        "thinking": {"budget": 0},
        "pricing": {"currency": "USD", "input_per_million": "1.5",
                    "output_per_million": "3", "source_url": "https://example.org/prices",
                    "checked_on": "2026-10-15"},
    }]}


@pytest.fixture
def prompt_data():
    return {"schema_version": 1, "prompts": [{
        "id": "math-1", "task_type": "maths", "prompt": "What is 2 + 2? End with Answer: <number>",
        "scoring": {"type": "numeric_final_line", "expected": "4", "absolute_tolerance": "0"},
    }]}
