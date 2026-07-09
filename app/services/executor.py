import logging
import time

from app.services.fireworks_client import FireworksClient
from app.services.huggingface_client import HuggingFaceClient
from app.services.ollama_client import OllamaClient
from app.services.router import RoutingEngine

logger = logging.getLogger(__name__)

# Fireworks model map
FIREWORKS_MODEL_MAP = {
    "mixtral": "accounts/fireworks/models/mixtral-8x7b-instruct",
    "qwen-72b": "accounts/fireworks/models/qwen2p5-72b-instruct",
}


class ModelExecutor:
    @staticmethod
    async def call_model(model_string: str, prompt: str) -> dict:
        """Helper to direct prompts to the correct client class."""
        provider, model_name = model_string.split(":", 1)

        if provider == "ollama":
            # For local models, we pass the name directly (e.g. qwen:7b)
            return await OllamaClient.generate(prompt, model_name)

        elif provider == "fireworks":
            # Map shorthand model name to Fireworks catalog path
            full_model_path = FIREWORKS_MODEL_MAP.get(model_name, model_name)
            return await FireworksClient.chat_completion(prompt, full_model_path)

        elif provider == "huggingface":
            return await HuggingFaceClient.chat_completion(prompt, model_name)

        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    @classmethod
    async def execute(cls, prompt: str, routing: dict) -> dict:
        """Executes a request, applying retry and fallback logic."""
        primary = routing["primary_model"]
        fallback = routing["fallback_model"]

        start_time = time.time()
        fallback_used = False
        final_model = primary
        result_text = ""
        tokens = {"input": 0, "output": 0, "total": 0}
        error_message = None
        attempts = []

        # 1. Attempt primary model
        try:
            logger.info(f"Calling primary model: {primary}")
            response = await cls.call_model(primary, prompt)
            result_text = response["text"]
            tokens = {
                "input": response["input_tokens"],
                "output": response["output_tokens"],
                "total": response["total_tokens"],
            }
            status = "success"
        except Exception as e:
            logger.error(f"Primary model {primary} failed: {e}. Retrying with fallback...")
            attempts.append({"model": primary, "status": "failed", "error": str(e)})

            # 2. Attempt fallback model
            fallback_used = True
            final_model = fallback
            try:
                logger.info(f"Calling fallback model: {fallback}")
                response = await cls.call_model(fallback, prompt)
                result_text = response["text"]
                tokens = {
                    "input": response["input_tokens"],
                    "output": response["output_tokens"],
                    "total": response["total_tokens"],
                }
                status = "success_via_fallback"
            except Exception as e_fallback:
                logger.critical(f"Fallback model {fallback} also failed: {e_fallback}")
                attempts.append({"model": fallback, "status": "failed", "error": str(e_fallback)})
                status = "failed"
                error_message = f"Primary failed: {e}. Fallback failed: {e_fallback}"

        latency_ms = int((time.time() - start_time) * 1000)

        # Calculate cost
        cost_usd = (
            RoutingEngine.calculate_cost(final_model, tokens["input"], tokens["output"])
            if status != "failed"
            else 0.0
        )

        return {
            "status": status,
            "result": result_text,
            "final_model_used": final_model,
            "fallback_model_used": fallback_used,
            "tokens": tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "error_message": error_message,
            "attempts": attempts,
        }
