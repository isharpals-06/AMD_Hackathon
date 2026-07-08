import httpx
import logging
from app import config

logger = logging.getLogger(__name__)

class HuggingFaceClient:
    @staticmethod
    async def generate(prompt: str, model_id: str) -> dict:
        """
        Calls HuggingFace Serverless Inference API and returns response text + token estimates.
        Requires a free HF token in the environment variables.
        """
        url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        
        # Get token from environment
        hf_token = config.FIREWORKS_API_KEY # We can reuse or define HF_TOKEN in config
        hf_token_val = getattr(config, "HF_TOKEN", "") or hf_token
        
        headers = {}
        if hf_token_val:
            headers["Authorization"] = f"Bearer {hf_token_val}"
            
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 800,
                "temperature": 0.2,
                "return_full_text": False
            },
            "options": {
                "use_cache": True,
                "wait_for_model": True
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # HF Serverless returns a list of completions
                text = ""
                if isinstance(data, list) and len(data) > 0:
                    text = data[0].get("generated_text", "")
                elif isinstance(data, dict):
                    text = data.get("generated_text", "")
                    
                # Serverless API does not return exact tokens usage, we estimate (4 chars per token)
                input_tokens = len(prompt) // 4
                output_tokens = len(text) // 4
                total_tokens = input_tokens + output_tokens
                
                return {
                    "text": text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                }
        except Exception as e:
            logger.error(f"Hugging Face Inference API failed for model {model_id}: {e}")
            raise e

    @staticmethod
    async def check_health() -> bool:
        """Simple connection test to HuggingFace Inference API."""
        try:
            url = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
