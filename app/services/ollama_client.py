import httpx
import logging
from app import config

logger = logging.getLogger(__name__)

class OllamaClient:
    _last_loaded_model = None

    @classmethod
    async def unload_model(cls, model_name: str) -> bool:
        """Forces Ollama to unload a model from GPU VRAM immediately by setting keep_alive to 0."""
        if not model_name:
            return False
        logger.info(f"Unloading model '{model_name}' from Ollama VRAM...")
        url = f"{config.OLLAMA_URL}/api/generate"
        payload = {
            "model": model_name,
            "keep_alive": 0
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
                return True
        except Exception as e:
            logger.error(f"Failed to unload Ollama model {model_name}: {e}")
            return False

    @classmethod
    async def generate(cls, prompt: str, model: str = None) -> dict:
        """Calls Ollama generate endpoint and manages VRAM swaps."""
        model_name = model or config.OLLAMA_MODEL
        
        # Explicit VRAM Management: Unload the previously used model if it's different
        if cls._last_loaded_model and cls._last_loaded_model != model_name:
            logger.info(f"VRAM Manager: Swapping '{cls._last_loaded_model}' out of VRAM for '{model_name}'")
            await cls.unload_model(cls._last_loaded_model)
            
        cls._last_loaded_model = model_name
        
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
        # Try newer /api/embed first
        embed_url = f"{config.OLLAMA_URL}/api/embed"
        embed_payload = {
            "model": config.OLLAMA_EMBED_MODEL,
            "input": text
        }
        
        async with httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT) as client:
            try:
                response = await client.post(embed_url, json=embed_payload)
                if response.status_code == 200:
                    data = response.json()
                    # /api/embed returns "embeddings" (a list of vectors)
                    embeddings_list = data.get("embeddings", [])
                    if embeddings_list:
                        return embeddings_list[0]
            except Exception as e:
                logger.warning(f"Ollama /api/embed failed, trying fallback: {e}")
                
            # Fallback to older /api/embeddings
            url = f"{config.OLLAMA_URL}/api/embeddings"
            payload = {
                "model": config.OLLAMA_EMBED_MODEL,
                "prompt": text
            }
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

