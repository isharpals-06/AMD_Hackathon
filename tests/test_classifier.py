from unittest.mock import patch

import pytest

from app.services.classifier import TaskClassifier


@pytest.mark.asyncio
async def test_regex_classification():
    """Verify Tier 3 Regex classification maps keywords correctly."""
    classifier = TaskClassifier(persist_directory=":memory:")

    assert classifier.classify_regex("Solve 3x + 5 = 20") == "math"
    assert classifier.classify_regex("Write a python function to fetch pages") == "coding"
    assert classifier.classify_regex("Summarize the causes of inflation") == "research"
    assert classifier.classify_regex("How's the weather today?") == "casual_chat"


@pytest.mark.asyncio
@patch("app.services.ollama_client.OllamaClient.generate")
async def test_slm_classification_success(mock_generate):
    """Verify Tier 1 SLM classification maps decision JSON accurately."""
    mock_generate.return_value = {
        "text": '{"task_type": "coding", "primary_model": "ollama:kimi-k2p7-code", "fallback_model": "ollama:gemma-4-31b-it"}',
        "input_tokens": 10,
        "output_tokens": 15,
        "total_tokens": 25,
    }

    classifier = TaskClassifier(persist_directory=":memory:")
    decision = await classifier.classify("Write a python script")

    assert decision["category"] == "coding"
    assert decision["primary_model"] == "ollama:kimi-k2p7-code"
    assert decision["fallback_model"] == "ollama:gemma-4-31b-it"


@pytest.mark.asyncio
@patch("app.services.ollama_client.OllamaClient.generate")
async def test_slm_classification_fallback_to_regex(mock_generate):
    """Verify SLM failures fall back cleanly to regex (when Chroma is offline)."""
    # Force SLM generate to raise an error
    mock_generate.side_effect = Exception("Ollama connection failed")

    # We patch ChromaDB availability to False to force regex fallback
    with patch("app.services.classifier.CHROMADB_AVAILABLE", False):
        classifier = TaskClassifier(persist_directory=":memory:")
        decision = await classifier.classify("Solve the derivative of cos(x)")

        assert decision["category"] == "math"
        assert decision["primary_model"] == "ollama:gemma-4-31b-it"
