import logging

import httpx

from app import config

logger = logging.getLogger(__name__)


class HuggingFaceClient:
    @staticmethod
    async def chat_completion(prompt: str, model: str) -> dict:
        """Calls Hugging Face Serverless Inference API (OpenAI compatible) and returns text + exact token counts."""
        # Using the active endpoint
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {"Authorization": f"Bearer {config.HF_TOKEN}", "Content-Type": "application/json"}

        # Standard chat completions request structure
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1000,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            text = choices[0].get("message", {}).get("content", "") if choices else ""

            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            return {
                "text": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }

    @staticmethod
    async def check_health() -> bool:
        """Verifies authentication key and connectivity to Hugging Face API."""
        if not config.HF_TOKEN:
            return False
        try:
            url = "https://router.huggingface.co/v1/models"
            headers = {"Authorization": f"Bearer {config.HF_TOKEN}"}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
