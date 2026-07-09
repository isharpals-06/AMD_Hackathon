import pytest
from unittest.mock import patch, AsyncMock
from app.services.router import RoutingEngine
from app.services.executor import ModelExecutor

def test_routing_engine_rules():
    """Verify RoutingEngine returns correct rules for predefined categories."""
    from app import config
    math_rules = RoutingEngine.get_routing("math")
    assert math_rules["primary_model"] == (config.MATH_PRIMARY_MODEL or "ollama:gemma-4-31b-it")
    assert math_rules["fallback_model"] == (config.MATH_FALLBACK_MODEL or "ollama:gemma-4-31b-it-nvfp4")

    unknown_rules = RoutingEngine.get_routing("unknown_category")
    assert unknown_rules["primary_model"] == (config.CASUAL_PRIMARY_MODEL or "ollama:minimax-m3")

def test_routing_engine_cost_calculation():
    """Verify cost calculation is accurate for inputs and outputs."""
    # minimax-m3 pricing is $0.15/1M tokens ($0.00000015/token)
    cost = RoutingEngine.calculate_cost("ollama:minimax-m3", 1000, 2000)
    expected_cost = (1000 * 0.15 / 1000000.0) + (2000 * 0.15 / 1000000.0)
    assert abs(cost - expected_cost) < 1e-9

@pytest.mark.asyncio
@patch("app.services.executor.ModelExecutor.call_model")
async def test_executor_primary_success(mock_call):
    """Verify ModelExecutor returns result from primary model on success."""
    mock_call.return_value = {
        "text": "Correct Math Answer",
        "input_tokens": 12,
        "output_tokens": 8,
        "total_tokens": 20
    }
    
    routing = {
        "primary_model": "ollama:gemma-4-31b-it",
        "fallback_model": "ollama:gemma-4-31b-it-nvfp4"
    }
    
    result = await ModelExecutor.execute("Compute 2+2", routing)
    
    assert result["status"] == "success"
    assert result["result"] == "Correct Math Answer"
    assert result["final_model_used"] == "ollama:gemma-4-31b-it"
    assert result["fallback_model_used"] is False

@pytest.mark.asyncio
@patch("app.services.executor.ModelExecutor.call_model")
async def test_executor_fallback_success(mock_call):
    """Verify ModelExecutor falls back to secondary model if primary fails."""
    # Make the first call fail, and the second call succeed
    mock_call.side_effect = [
        Exception("Primary model OOM or timeout"),
        {
            "text": "Fallback Math Answer",
            "input_tokens": 15,
            "output_tokens": 10,
            "total_tokens": 25
        }
    ]
    
    routing = {
        "primary_model": "ollama:gemma-4-31b-it",
        "fallback_model": "ollama:gemma-4-31b-it-nvfp4"
    }
    
    result = await ModelExecutor.execute("Compute 2+2", routing)
    
    assert result["status"] == "success_via_fallback"
    assert result["result"] == "Fallback Math Answer"
    assert result["final_model_used"] == "ollama:gemma-4-31b-it-nvfp4"
    assert result["fallback_model_used"] is True
