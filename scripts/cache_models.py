# Cache Gated Model Weights on AMD Cloud GPU Instance
# Run this script on the AMD Cloud instance to pre-download all 5 target models.

import os

from transformers import AutoModelForCausalLM, AutoTokenizer

# List of target Hugging Face models
MODEL_IDS = [
    "meta-llama/Llama-3.2-1B",  # Base model for the router SLM
    "MiniMax/Minimax-M3",
    "MoonshotAI/Kimi-K2P7-Code",
    "google/gemma-4-26b-a4b-it",
    "google/gemma-4-31b-it",
    "google/gemma-4-31b-it-nvfp4",
]


def cache_models():
    print("=== AMD Cloud HF Model Cache Tool ===")
    print("Pre-downloading model weights to local HuggingFace cache folder...\n")

    # Check if HuggingFace token is present (Gemma requires authentication)
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("⚠️ Warning: HF_TOKEN environment variable is not set.")
        print(
            "Note: Gated models (like Gemma and Llama) require a HuggingFace access token to download."
        )
        print(
            "Please run 'huggingface-cli login' or set HF_TOKEN before running this script if you get access errors.\n"
        )

    for model_id in MODEL_IDS:
        print(f"⏳ Downloading weights for: {model_id}...")
        try:
            # Download and cache the tokenizer
            AutoTokenizer.from_pretrained(model_id, token=hf_token)
            # Download and cache model weights (only metadata/safetensors, no execution)
            AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="cpu",  # Load on CPU to avoid allocating memory during download
                low_cpu_mem_usage=True,
                token=hf_token,
            )
            print(f"✓ {model_id} cached successfully!\n")
        except Exception as e:
            print(f"❌ Failed to cache {model_id}: {e}\n")


if __name__ == "__main__":
    cache_models()
