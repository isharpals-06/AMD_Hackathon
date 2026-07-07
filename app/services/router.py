class RoutingEngine:
    # Model pricing constants for virtual cost tracking (USD per 1M tokens)
    MODEL_PRICING = {
        "ollama:minimax-m3": (0.15, 0.15),
        "ollama:kimi-k2p7-code": (0.35, 0.35),
        "ollama:gemma-4-26b-a4b-it": (0.80, 0.80),
        "ollama:gemma-4-31b-it": (1.20, 1.20),
        "ollama:gemma-4-31b-it-nvfp4": (1.00, 1.00)
    }

    @staticmethod
    def get_routing(task_type: str) -> dict:
        """Returns the routing instructions (primary, fallback, timeout) for a task type."""
        routing_rules = {
            "math": {
                "primary_model": "ollama:gemma-4-31b-it",
                "fallback_model": "ollama:gemma-4-31b-it-nvfp4",
                "timeout_seconds": 25,
                "max_retries": 1
            },
            "coding": {
                "primary_model": "ollama:kimi-k2p7-code",
                "fallback_model": "ollama:gemma-4-31b-it",
                "timeout_seconds": 25,
                "max_retries": 1
            },
            "research": {
                "primary_model": "ollama:gemma-4-26b-a4b-it",
                "fallback_model": "ollama:gemma-4-31b-it",
                "timeout_seconds": 25,
                "max_retries": 1
            },
            "casual_chat": {
                "primary_model": "ollama:minimax-m3",
                "fallback_model": "ollama:gemma-4-26b-a4b-it",
                "timeout_seconds": 15,
                "max_retries": 1
            }
        }
        
        # Fallback to general rules if unknown task type is passed
        return routing_rules.get(task_type, routing_rules["casual_chat"])

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculates cost in USD based on model parameters and token count."""
        price_rates = cls.MODEL_PRICING.get(model, (0.0, 0.0))
        input_cost = (input_tokens * price_rates[0]) / 1000000.0
        output_cost = (output_tokens * price_rates[1]) / 1000000.0
        return input_cost + output_cost

