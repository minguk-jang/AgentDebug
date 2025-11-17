"""Pytest configuration and fixtures"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_trace_success(fixtures_dir):
    """Load successful trace fixture"""
    with open(fixtures_dir / "sample_trace_success.json", "r") as f:
        return json.load(f)


@pytest.fixture
def sample_trace_failure(fixtures_dir):
    """Load failed trace fixture"""
    with open(fixtures_dir / "sample_trace_failure.json", "r") as f:
        return json.load(f)


@pytest.fixture
def sample_trace_minimal(fixtures_dir):
    """Load minimal trace fixture"""
    with open(fixtures_dir / "sample_trace_minimal.json", "r") as f:
        return json.load(f)


@pytest.fixture
def sample_trace_plaintext(fixtures_dir):
    """Load plain text trace fixture"""
    with open(fixtures_dir / "sample_trace_plaintext.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for error detection"""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "error_detected": False,
                        "error_type": "no_error",
                        "evidence": "No errors detected",
                        "reasoning": "The module performed correctly"
                    })
                }
            }
        ]
    }


@pytest.fixture
def mock_decomposer_response():
    """Mock OpenAI API response for module decomposition"""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "memory": "Previously I searched for headphones.",
                        "reflection": "The results show good options within budget.",
                        "plan": "I will select the best value option.",
                        "action": "click[2]"
                    })
                }
            }
        ]
    }
