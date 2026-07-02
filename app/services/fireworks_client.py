import httpx
from app import config

class FireworksClient:
    @staticmethod
    async def chat_completion(prompt: str, model: str) -> dict:
        """Calls Fireworks API chat completion and returns text + exact token counts."""
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.FIREWORKS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Fireworks uses standard OpenAI chat messages structure
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=config.FIREWORKS_TIMEOUT) as client:
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
                "total_tokens": total_tokens
            }
            
    @staticmethod
    async def check_health() -> bool:
        """Verifies authentication key and connectivity to Fireworks API."""
        if not config.FIREWORKS_API_KEY:
            return False
        try:
            # Quick check with a tiny model or endpoint
            url = "https://api.fireworks.ai/inference/v1/models"
            headers = {"Authorization": f"Bearer {config.FIREWORKS_API_KEY}"}
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
