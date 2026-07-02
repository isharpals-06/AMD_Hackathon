import httpx
from app import config

class OllamaClient:
    @staticmethod
    async def generate(prompt: str, model: str = None) -> dict:
        """Calls Ollama generate endpoint and returns output + exact tokens used."""
        model_name = model or config.OLLAMA_MODEL
        url = f"{config.OLLAMA_URL}/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Ollama returns prompt_eval_count (input tokens) and eval_count (output tokens)
            input_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)
            total_tokens = input_tokens + output_tokens
            
            return {
                "text": data.get("response", ""),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }

    @staticmethod
    async def get_embedding(text: str) -> list:
        """Generates embedding vector for a string using local embed model."""
        url = f"{config.OLLAMA_URL}/api/embeddings"
        payload = {
            "model": config.OLLAMA_EMBED_MODEL,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
            
    @staticmethod
    async def check_health() -> bool:
        """Verifies connection to local Ollama service."""
        try:
            url = f"{config.OLLAMA_URL}/api/tags"
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
