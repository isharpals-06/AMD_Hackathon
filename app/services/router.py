import logging
import os
from typing import Any

import yaml

from app import config

logger = logging.getLogger(__name__)


class RoutingEngine:
    # Class-level cache for rules and pricing
    _cached_rules: dict[str, Any] | None = None
    _cached_pricing: dict[str, tuple[float, float]] | None = None

    @classmethod
    def _load_rules(cls) -> tuple[dict, dict]:
        """Loads routing rules and pricing from configs/routing_rules.yaml."""
        if cls._cached_rules is not None and cls._cached_pricing is not None:
            return cls._cached_rules, cls._cached_pricing

        # Default fallback routing rules matching original implementation
        fallback_rules = {
            "math": {
                "primary_model": "ollama:gemma-4-31b-it",
                "fallback_model": "ollama:gemma-4-31b-it-nvfp4",
                "timeout_seconds": 25,
                "max_retries": 1,
            },
            "coding": {
                "primary_model": "ollama:kimi-k2p7-code",
                "fallback_model": "ollama:gemma-4-31b-it",
                "timeout_seconds": 25,
                "max_retries": 1,
            },
            "research": {
                "primary_model": "ollama:gemma-4-26b-a4b-it",
                "fallback_model": "ollama:gemma-4-31b-it",
                "timeout_seconds": 25,
                "max_retries": 1,
            },
            "casual_chat": {
                "primary_model": "ollama:minimax-m3",
                "fallback_model": "ollama:gemma-4-26b-a4b-it",
                "timeout_seconds": 15,
                "max_retries": 1,
            },
        }

        fallback_pricing = {
            "ollama:minimax-m3": (0.15, 0.15),
            "ollama:kimi-k2p7-code": (0.35, 0.35),
            "ollama:gemma-4-26b-a4b-it": (0.80, 0.80),
            "ollama:gemma-4-31b-it": (1.20, 1.20),
            "ollama:gemma-4-31b-it-nvfp4": (1.00, 1.00),
        }

        # Resolve path to configs/routing_rules.yaml
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yaml_path = os.path.join(base_dir, "configs", "routing_rules.yaml")

        if not os.path.exists(yaml_path):
            logger.warning(
                f"Routing rules config not found at {yaml_path}. Using hardcoded fallbacks."
            )
            cls._cached_rules = fallback_rules
            cls._cached_pricing = fallback_pricing
            return cls._cached_rules, cls._cached_pricing

        try:
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            rules_data = data.get("routing_rules", {})
            pricing_data = data.get("model_pricing", {})

            # Map pricing dictionary to input/output tuples
            pricing = {}
            for model_name, prices in pricing_data.items():
                input_p = prices.get("input_per_1m", 0.15)
                output_p = prices.get("output_per_1m", 0.15)
                pricing[model_name] = (input_p, output_p)

            cls._cached_rules = rules_data
            cls._cached_pricing = pricing
            logger.info(
                "Loaded routing rules and model pricing from configs/routing_rules.yaml successfully."
            )
        except Exception as e:
            logger.error(f"Error loading routing rules YAML: {e}. Falling back to default values.")
            cls._cached_rules = fallback_rules
            cls._cached_pricing = fallback_pricing

        return cls._cached_rules, cls._cached_pricing

    @classmethod
    def get_routing(cls, task_type: str) -> dict:
        """Returns the routing instructions (primary, fallback, timeout) for a task type."""
        rules, _ = cls._load_rules()

        # Fallback to general rules if unknown task type is passed
        routing = rules.get(task_type, rules.get("casual_chat", {}))

        # Override primary and fallback models with environment variables to enforce cloud-only execution (per user directive)
        if task_type == "math":
            routing = {
                **routing,
                "primary_model": config.MATH_PRIMARY_MODEL or routing.get("primary_model"),
                "fallback_model": config.MATH_FALLBACK_MODEL or routing.get("fallback_model"),
            }
        elif task_type == "coding":
            routing = {
                **routing,
                "primary_model": config.CODING_PRIMARY_MODEL or routing.get("primary_model"),
                "fallback_model": config.CODING_FALLBACK_MODEL or routing.get("fallback_model"),
            }
        elif task_type == "research":
            routing = {
                **routing,
                "primary_model": config.RESEARCH_PRIMARY_MODEL or routing.get("primary_model"),
                "fallback_model": config.RESEARCH_FALLBACK_MODEL or routing.get("fallback_model"),
            }
        elif task_type == "casual_chat":
            routing = {
                **routing,
                "primary_model": config.CASUAL_PRIMARY_MODEL or routing.get("primary_model"),
                "fallback_model": config.CASUAL_FALLBACK_MODEL or routing.get("fallback_model"),
            }
        else:
            routing = {
                **routing,
                "primary_model": config.CASUAL_PRIMARY_MODEL or routing.get("primary_model"),
                "fallback_model": config.CASUAL_FALLBACK_MODEL or routing.get("fallback_model"),
            }

        return routing.copy()

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculates cost in USD based on model parameters and token count."""
        _, pricing = cls._load_rules()
        if model in pricing:
            price_rates = pricing[model]
        elif model.startswith("huggingface:"):
            price_rates = (0.15, 0.15)
        else:
            price_rates = (0.0, 0.0)
        input_cost = (input_tokens * price_rates[0]) / 1000000.0
        output_cost = (output_tokens * price_rates[1]) / 1000000.0
        return input_cost + output_cost
