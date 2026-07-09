"""
Unit tests for app.services.executor — ModelExecutor.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.executor import ModelExecutor

ROUTING = {
    "primary_model": "ollama:minimax-m3",
    "fallback_model": "ollama:gemma-4-26b-a4b-it",
    "timeout_seconds": 15,
    "max_retries": 1,
}

MOCK_RESPONSE = {
    "text": "Test response text",
    "input_tokens": 10,
    "output_tokens": 20,
    "total_tokens": 30,
}


@pytest.mark.unit
class TestModelExecutor:
    """Tests for ModelExecutor.execute()"""

    @pytest.mark.asyncio
    async def test_primary_model_success(self):
        """When primary model succeeds, fallback should NOT be used."""
        with patch(
            "app.services.executor.ModelExecutor.call_model",
            new_callable=AsyncMock,
            return_value=MOCK_RESPONSE,
        ):
            result = await ModelExecutor.execute("Test prompt", ROUTING)

        assert result["status"] == "success"
        assert result["result"] == "Test response text"
        assert result["fallback_model_used"] is False
        assert result["final_model_used"] == ROUTING["primary_model"]
        assert result["tokens"]["total"] == 30
        assert result["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_fallback_triggered_on_primary_failure(self):
        """When primary fails, fallback should be called and used."""
        call_count = 0

        async def mock_call(model_string: str, prompt: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Primary model unavailable")
            return MOCK_RESPONSE

        with patch("app.services.executor.ModelExecutor.call_model", side_effect=mock_call):
            result = await ModelExecutor.execute("Test prompt", ROUTING)

        assert result["status"] == "success_via_fallback"
        assert result["fallback_model_used"] is True
        assert result["final_model_used"] == ROUTING["fallback_model"]
        assert len(result["attempts"]) >= 1

    @pytest.mark.asyncio
    async def test_both_models_fail_returns_failed_status(self):
        """When both primary and fallback fail, status should be 'failed'."""
        with patch(
            "app.services.executor.ModelExecutor.call_model",
            new_callable=AsyncMock,
            side_effect=ConnectionError("All models down"),
        ):
            result = await ModelExecutor.execute("Test prompt", ROUTING)

        assert result["status"] == "failed"
        assert result["error_message"] is not None
        assert len(result["attempts"]) >= 1

    @pytest.mark.asyncio
    async def test_result_has_all_required_fields(self):
        """Execute must always return all required keys."""
        with patch(
            "app.services.executor.ModelExecutor.call_model",
            new_callable=AsyncMock,
            return_value=MOCK_RESPONSE,
        ):
            result = await ModelExecutor.execute("Test prompt", ROUTING)

        required_fields = [
            "status", "result", "final_model_used", "fallback_model_used",
            "tokens", "cost_usd", "latency_ms", "error_message", "attempts",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_cost_is_zero_on_failure(self):
        """No cost should be incurred if both models fail."""
        with patch(
            "app.services.executor.ModelExecutor.call_model",
            new_callable=AsyncMock,
            side_effect=Exception("All down"),
        ):
            result = await ModelExecutor.execute("Test prompt", ROUTING)

        assert result["cost_usd"] == 0.0


@pytest.mark.unit
class TestCallModel:
    """Tests for ModelExecutor.call_model() provider dispatch."""

    @pytest.mark.asyncio
    async def test_ollama_provider_dispatches_correctly(self):
        with patch(
            "app.services.executor.OllamaClient.generate",
            new_callable=AsyncMock,
            return_value=MOCK_RESPONSE,
        ) as mock_gen:
            result = await ModelExecutor.call_model("ollama:minimax-m3", "Hello")
            mock_gen.assert_called_once_with("Hello", "minimax-m3")

    @pytest.mark.asyncio
    async def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported model provider"):
            await ModelExecutor.call_model("unknown_provider:some-model", "Hello")
