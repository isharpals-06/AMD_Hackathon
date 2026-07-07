import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Set up paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_NAME = "meta-llama/Llama-3.2-1B"
ADAPTER_DIR = os.path.join(BASE_DIR, "Multi_Model_Router_Llama3_QLoRA_Finetuning.ipynb", "final_model")
OUTPUT_DIR = os.path.join(BASE_DIR, "Multi_Model_Router_Llama3_QLoRA_Finetuning.ipynb", "merged_model")

def main():
    print(f"Loading base model: {BASE_MODEL_NAME}...")
    try:
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="cpu"  # Safer to merge on CPU to avoid running out of GPU memory
        )
    except Exception as e:
        print(f"Error loading base model: {e}")
        print("Please make sure you have hf transformers installed and access to meta-llama/Llama-3.2-1B on HuggingFace.")
        sys.exit(1)

    print(f"Loading LoRA adapter from: {ADAPTER_DIR}...")
    try:
        model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    except Exception as e:
        print(f"Error loading adapter: {e}")
        sys.exit(1)

    print("Merging LoRA adapters into base model weights...")
    merged_model = model.merge_and_unload()

    print(f"Saving merged 16-bit model to: {OUTPUT_DIR}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    merged_model.save_pretrained(OUTPUT_DIR)
    
    # Save the tokenizer too
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print("✓ Success! Merged model saved successfully.")
    print(f"You can now find the full model files in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
