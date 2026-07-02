class RoutingEngine:
    # Model pricing constants for Cost Calculator
    # Price per 1k tokens: (Input Price, Output Price)
    MODEL_PRICING = {
        "ollama:qwen": (0.0, 0.0),
        "fireworks:mixtral": (0.0005, 0.0015),
        "fireworks:qwen-72b": (0.0003, 0.0010)
    }

    @staticmethod
    def get_routing(task_type: str) -> dict:
        """Returns the routing instructions (primary, fallback, timeout) for a task type."""
        routing_rules = {
            "math": {
                "primary_model": "fireworks:qwen-72b",
                "fallback_model": "fireworks:mixtral",
                "timeout_seconds": 15,
                "max_retries": 1
            },
            "coding": {
                "primary_model": "fireworks:mixtral",
                "fallback_model": "fireworks:qwen-72b",
                "timeout_seconds": 15,
                "max_retries": 1
            },
            "research": {
                "primary_model": "fireworks:mixtral",
                "fallback_model": "ollama:qwen",
                "timeout_seconds": 15,
                "max_retries": 1
            },
            "casual_chat": {
                "primary_model": "ollama:qwen",
                "fallback_model": "fireworks:mixtral",
                "timeout_seconds": 10,
                "max_retries": 1
            }
        }
        
        # Fallback to general rules if unknown task type is passed
        return routing_rules.get(task_type, routing_rules["casual_chat"])

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculates cost in USD based on model parameters and token count."""
        price_rates = cls.MODEL_PRICING.get(model, (0.0, 0.0))
        input_cost = (input_tokens * price_rates[0]) / 1000.0
        output_cost = (output_tokens * price_rates[1]) / 1000.0
        return input_cost + output_cost
