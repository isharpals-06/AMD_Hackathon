"""
Unit tests for app.services.router — RoutingEngine.
"""
from __future__ import annotations

import pytest

from app.services.router import RoutingEngine

VALID_TASK_TYPES = ["math", "coding", "research", "casual_chat"]


@pytest.mark.unit
class TestGetRouting:
    """Tests for RoutingEngine.get_routing()"""

    @pytest.mark.parametrize("task_type", VALID_TASK_TYPES)
    def test_returns_dict_for_valid_task_types(self, task_type: str):
        result = RoutingEngine.get_routing(task_type)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("task_type", VALID_TASK_TYPES)
    def test_routing_has_required_keys(self, task_type: str):
        result = RoutingEngine.get_routing(task_type)
        assert "primary_model" in result
        assert "fallback_model" in result
        assert "timeout_seconds" in result
        assert "max_retries" in result

    @pytest.mark.parametrize("task_type", VALID_TASK_TYPES)
    def test_models_are_non_empty_strings(self, task_type: str):
        result = RoutingEngine.get_routing(task_type)
        assert isinstance(result["primary_model"], str) and result["primary_model"]
        assert isinstance(result["fallback_model"], str) and result["fallback_model"]

    def test_unknown_task_type_falls_back_to_casual_chat(self):
        """Unknown task types must not crash — should return casual_chat rules."""
        result = RoutingEngine.get_routing("totally_unknown_type_xyz")
        casual = RoutingEngine.get_routing("casual_chat")
        assert result["primary_model"] == casual["primary_model"]

    def test_math_uses_correct_primary_model(self):
        result = RoutingEngine.get_routing("math")
        assert "gemma-4-31b-it" in result["primary_model"]

    def test_coding_uses_correct_primary_model(self):
        result = RoutingEngine.get_routing("coding")
        assert "kimi-k2p7-code" in result["primary_model"]


@pytest.mark.unit
class TestCalculateCost:
    """Tests for RoutingEngine.calculate_cost()"""

    def test_zero_tokens_returns_zero_cost(self):
        cost = RoutingEngine.calculate_cost("ollama:minimax-m3", 0, 0)
        assert cost == 0.0

    def test_known_model_returns_positive_cost(self):
        cost = RoutingEngine.calculate_cost("ollama:gemma-4-31b-it", 1000, 500)
        assert cost > 0.0

    def test_unknown_model_returns_zero_cost(self):
        """Unknown models should default to 0 cost (not crash)."""
        cost = RoutingEngine.calculate_cost("ollama:unknown-model-xyz", 1000, 1000)
        assert cost == 0.0

    def test_cost_scales_with_tokens(self):
        """Doubling tokens should double cost."""
        cost_1k = RoutingEngine.calculate_cost("ollama:gemma-4-31b-it", 500, 500)
        cost_2k = RoutingEngine.calculate_cost("ollama:gemma-4-31b-it", 1000, 1000)
        assert abs(cost_2k - cost_1k * 2) < 1e-9

    def test_more_expensive_model_costs_more(self):
        tokens = (1000, 500)
        cheap = RoutingEngine.calculate_cost("ollama:minimax-m3", *tokens)
        expensive = RoutingEngine.calculate_cost("ollama:gemma-4-31b-it", *tokens)
        assert expensive > cheap
