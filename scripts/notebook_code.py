# Jupyter Notebook Code Blocks for AMD GPU Cloud Execution
# Copy and paste these cells into your cloud Jupyter Notebook.

import contextlib
import gc
import json
import time

import ipywidgets as widgets
import torch
from IPython.display import clear_output, display
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


# ==========================================
# CELL 1: ENVIRONMENT & GPU SYSTEM CHECK
# ==========================================
def run_system_check():
    print("=== AMD ROCm / CUDA System Check ===")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"Total VRAM: {total_mem:.2f} GB")
    else:
        print("⚠️ Running in CPU mode. Large models will execute slowly.")


# ==========================================
# CELL 2: DYNAMIC GPU VRAM MANAGER
# ==========================================
class VRAMManager:
    _loaded_models = {}

    @classmethod
    def get_vram_usage(cls):
        """Returns allocated and reserved GPU memory in GB."""
        if not torch.cuda.is_available():
            return 0.0, 0.0
        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        return allocated, reserved

    @classmethod
    def print_vram_status(cls, label=""):
        alloc, res = cls.get_vram_usage()
        prefix = f"[{label}] " if label else ""
        print(f"{prefix}Allocated VRAM: {alloc:.2f} GB | Reserved: {res:.2f} GB")
        print(f"Active Models in VRAM: {list(cls._loaded_models.keys())}")

    @classmethod
    def clean_cache(cls):
        """Forces garbage collection and empties GPU cache."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @classmethod
    def register(cls, name, model, tokenizer):
        cls._loaded_models[name] = {"model": model, "tokenizer": tokenizer}

    @classmethod
    def unload(cls, name):
        """Unloads a specific model from GPU memory."""
        if name in cls._loaded_models:
            print(f"🧹 Offloading model '{name}' from VRAM...")
            # Move to CPU first to break CUDA links, then delete
            with contextlib.suppress(Exception):
                cls._loaded_models[name]["model"].to("cpu")
            del cls._loaded_models[name]["model"]
            del cls._loaded_models[name]["tokenizer"]
            del cls._loaded_models[name]
            cls.clean_cache()
            print(f"✓ '{name}' unloaded.")

    @classmethod
    def unload_all_except(cls, keep_name):
        """Unloads all models except the target model to prevent OOM."""
        to_unload = [n for n in cls._loaded_models if n != keep_name]
        for name in to_unload:
            cls.unload(name)
        cls.clean_cache()


# ==========================================
# CELL 3: DYNAMIC MODEL LOADER
# ==========================================
MODEL_PATHS = {
    "minimax-m3": "MiniMax/Minimax-M3",
    "kimi-k2p7-code": "MoonshotAI/Kimi-K2P7-Code",
    "gemma-4-31b-it": "google/gemma-4-31b-it",
    "gemma-4-26b-a4b-it": "google/gemma-4-26b-a4b-it",
    "gemma-4-31b-it-nvfp4": "google/gemma-4-31b-it-nvfp4",
}


class ModelLoader:
    @staticmethod
    def load(model_name: str, quantize_4bit: bool = True):
        # 1. Return immediately if already loaded
        if model_name in VRAMManager._loaded_models:
            return (
                VRAMManager._loaded_models[model_name]["model"],
                VRAMManager._loaded_models[model_name]["tokenizer"],
            )

        # 2. Make room by unloading other models
        VRAMManager.unload_all_except(model_name)
        VRAMManager.print_vram_status(f"Pre-Load {model_name}")

        huggingface_path = MODEL_PATHS.get(model_name, model_name)
        print(f"⏳ Loading '{model_name}' ({huggingface_path})...")

        # Configure 4-bit quantization for AMD GPUs to save memory
        bnb_config = None
        if quantize_4bit and torch.cuda.is_available():
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )

        try:
            tokenizer = AutoTokenizer.from_pretrained(huggingface_path)
            model = AutoModelForCausalLM.from_pretrained(
                huggingface_path,
                quantization_config=bnb_config,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            )
            VRAMManager.register(model_name, model, tokenizer)
            print(f"✓ '{model_name}' loaded successfully!")
            VRAMManager.print_vram_status(f"Post-Load {model_name}")
            return model, tokenizer
        except Exception as e:
            print(f"⚠️ Failed loading quantized {model_name}: {e}")
            if quantize_4bit:
                print("Retrying load without quantization...")
                return ModelLoader.load(model_name, quantize_4bit=False)
            raise e


# ==========================================
# CELL 4: COGNITIVE SLM ROUTER CLASSIFIER
# ==========================================
class TaskClassifier:
    @staticmethod
    def classify_regex(prompt: str) -> str:
        """Fallback regex classifier if the SLM fails to generate clean JSON."""
        prompt_lower = prompt.lower()
        if any(
            kw in prompt_lower
            for kw in ["code", "function", "regex", "bug", "implement", "loop", "api", "endpoint"]
        ):
            return "coding"
        if any(
            kw in prompt_lower
            for kw in [
                "solve",
                "equation",
                "derivative",
                "integral",
                "matrix",
                "calculate",
                "limit",
            ]
        ):
            return "math"
        if any(
            kw in prompt_lower
            for kw in [
                "summarize",
                "literature review",
                "explain",
                "compare",
                "research",
                "historical",
            ]
        ):
            return "research"
        return "casual_chat"

    @staticmethod
    def classify_with_slm(prompt: str) -> dict:
        """Loads the fine-tuned Llama 3.2 1B router model, runs inference to get routing JSON, and unloads it."""
        router_model_name = "llama-router"
        adapter_path = "./Multi_Model_Router_Llama3_QLoRA_Finetuning.ipynb/final_model"
        base_model_path = "meta-llama/Llama-3.2-1B"

        # 1. Load the routing SLM (unloading other models automatically to save VRAM)
        if router_model_name not in VRAMManager._loaded_models:
            VRAMManager.unload_all_except(router_model_name)
            VRAMManager.print_vram_status("Pre-Load Router SLM")

            # Configure 4-bit loading for Llama 3.2
            bnb_config = None
            if torch.cuda.is_available():
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                )

            tokenizer = AutoTokenizer.from_pretrained(adapter_path)
            tokenizer.pad_token = tokenizer.eos_token

            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                quantization_config=bnb_config,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            )
            model = PeftModel.from_pretrained(base_model, adapter_path)
            model.eval()
            VRAMManager.register(router_model_name, model, tokenizer)
            print("✓ Router SLM loaded successfully with fine-tuned adapter!")
            VRAMManager.print_vram_status("Post-Load Router SLM")
        else:
            model = VRAMManager._loaded_models[router_model_name]["model"]
            tokenizer = VRAMManager._loaded_models[router_model_name]["tokenizer"]

        # 2. Format with the Instruction template Llama was trained on
        instruction_prompt = f"""### Instruction:
You are an intelligent AI model router.

Analyze the user's request and decide:
1. Task category
2. Best model to handle the request
3. Backup model if the first model fails

Return only JSON output.

### User Request:
{prompt}

### Response:
"""
        inputs = tokenizer(instruction_prompt, return_tensors="pt")
        input_len = inputs["input_ids"].shape[1]
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        try:
            with torch.no_grad():
                outputs = model.generate(
                    **inputs, max_new_tokens=100, temperature=0.1, do_sample=True
                )
            output_text = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()

            # Parse decision
            decision = json.loads(output_text)
            return {
                "category": decision.get("task_type", "casual_chat"),
                "primary_model": decision.get("primary_model", "minimax-m3"),
                "fallback_model": decision.get("fallback_model", "gemma-4-26b-a4b-it"),
            }
        except Exception as e:
            print(f"⚠️ SLM router parsing failed: {e}. Falling back to default rules.")
            category = TaskClassifier.classify_regex(prompt)
            # Default model mapping fallback
            primary = "minimax-m3"
            if category == "coding":
                primary = "kimi-k2p7-code"
            elif category == "math":
                primary = "gemma-4-31b-it"
            elif category == "research":
                primary = "gemma-4-26b-a4b-it"
            return {
                "category": category,
                "primary_model": primary,
                "fallback_model": "gemma-4-26b-a4b-it",
            }


# ==========================================
# CELL 5: THE ROUTING & EXECUTION ENGINE
# ==========================================
class RoutingEngine:
    # Virtual token pricing for analytics (USD per 1M tokens)
    PRICING = {
        "minimax-m3": 0.15,
        "kimi-k2p7-code": 0.35,
        "gemma-4-26b-a4b-it": 0.80,
        "gemma-4-31b-it": 1.20,
        "gemma-4-31b-it-nvfp4": 1.00,
    }

    @classmethod
    def execute(cls, prompt: str) -> dict:
        start_time = time.time()

        # 1. Query the fine-tuned SLM to make the routing decision
        print("🧠 Querying Fine-Tuned Router SLM for decision...")
        decision = TaskClassifier.classify_with_slm(prompt)
        category = decision["category"]
        target_model = decision["primary_model"]
        fallback_model = decision["fallback_model"]

        # Strip provider prefixes if model names match local mappings
        target_model = target_model.replace("ollama:", "").replace("fireworks:", "")
        fallback_model = fallback_model.replace("ollama:", "").replace("fireworks:", "")

        # Guard mapping to ensure local model names match exactly
        if target_model == "mixtral" or target_model not in MODEL_PATHS:
            target_model = "kimi-k2p7-code" if category == "coding" else "gemma-4-31b-it"
        if fallback_model == "qwen" or fallback_model not in MODEL_PATHS:
            fallback_model = "gemma-4-26b-a4b-it"

        print(
            f"\n[Decision] Category: '{category}' | Primary: '{target_model}' | Fallback: '{fallback_model}'"
        )

        # 2. Load the execution model (this unloads the router SLM from VRAM)
        fallback_used = False
        try:
            model, tokenizer = ModelLoader.load(target_model)
        except Exception as e:
            print(
                f"⚠️ Primary model '{target_model}' failed to load: {e}. Switching to fallback..."
            )
            target_model = fallback_model
            fallback_used = True
            model, tokenizer = ModelLoader.load(target_model)

        # 3. Generate response
        inputs = tokenizer(prompt, return_tensors="pt")
        input_len = inputs["input_ids"].shape[1]
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        try:
            with torch.no_grad():
                outputs = model.generate(
                    **inputs, max_new_tokens=256, temperature=0.2, do_sample=True
                )
            output_text = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
            output_len = outputs[0].shape[0] - input_len
        except Exception as run_err:
            print(f"❌ Primary execution failed: {run_err}")
            if not fallback_used:
                print("Executing fallback model chain...")
                target_model = fallback_model
                fallback_used = True
                model, tokenizer = ModelLoader.load(target_model)
                inputs = tokenizer(prompt, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs, max_new_tokens=256, temperature=0.2, do_sample=True
                    )
                output_text = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
                output_len = outputs[0].shape[0] - input_len
            else:
                raise run_err

        latency_ms = (time.time() - start_time) * 1000

        # Calculate Metrics
        total_tokens = input_len + output_len
        rate = cls.PRICING.get(target_model, 1.0) / 1000000.0
        cost_usd = total_tokens * rate

        # Baseline Comparison (always using Gemma-4-31B-it as baseline)
        baseline_rate = cls.PRICING["gemma-4-31b-it"] / 1000000.0
        baseline_cost = total_tokens * baseline_rate
        savings_usd = max(0.0, baseline_cost - cost_usd)
        savings_pct = (savings_usd / baseline_cost * 100) if baseline_cost > 0 else 0.0

        return {
            "prompt": prompt,
            "response": output_text.strip(),
            "category": category,
            "model_used": target_model,
            "fallback_used": fallback_used,
            "input_tokens": input_len,
            "output_tokens": output_len,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "savings_usd": savings_usd,
            "savings_pct": savings_pct,
        }


# ==========================================
# CELL 6: TEST SUITE RUNNER
# ==========================================
TESTS = [
    "Hello there! Introduce yourself and list your capabilities.",
    "Solve for x: x^2 - 5x + 6 = 0.",
    "Write a quick python function to reverse a string.",
    "Summarize the primary biological functions of the cell membrane.",
    "Explain the concept of quantum superposition in simple terms.",
]


def run_notebook_test_suite():
    results = []
    for i, test in enumerate(TESTS):
        print(f"\n--- Run {i+1}/{len(TESTS)} ---")
        res = RoutingEngine.execute(test)
        results.append(res)
        print(f"Output: {res['response'][:100]}...")
        print(f"Metrics: Latency={res['latency_ms']:.0f}ms | Savings={res['savings_pct']:.1f}%")

    print("\n" + "=" * 40 + "\nAggregated Metrics:")
    total_cost = sum(r["cost_usd"] for r in results)
    total_saved = sum(r["savings_usd"] for r in results)
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    print(f"Average Latency: {avg_latency:.1f} ms")
    print(f"Total Combined Cost: ${total_cost:.6f}")
    print(f"Total Money Saved: ${total_saved:.6f}")


# ==========================================
# CELL 7: INTERACTIVE NOTEBOOK WIDGET CONSOLE
# ==========================================
def display_widget_console():
    console_title = widgets.HTML("<h3>🧠 AMD Intelligent Router Console</h3>")
    prompt_input = widgets.Textarea(
        value="Solve the equation 2x + 10 = 20.",
        placeholder="Enter your instruction here...",
        description="Prompt:",
        layout=widgets.Layout(width="100%", height="85px"),
    )
    run_button = widgets.Button(
        description="Route & Execute", button_style="success", icon="rocket"
    )
    output_console = widgets.Output()

    def handle_click(b):
        with output_console:
            clear_output()
            user_prompt = prompt_input.value.strip()
            if not user_prompt:
                print("Error: Input prompt cannot be empty.")
                return

            print("⏳ Processing prompt in AMD model router...")
            result = RoutingEngine.execute(user_prompt)

            clear_output()
            print(f"### CLASSIFIED CATEGORY: {result['category'].upper()}")
            print(
                f"ROUTED TO: {result['model_used'].upper()} (Fallback Used: {result['fallback_used']})"
            )
            print("=" * 50)
            print(f"RESPONSE:\\n{result['response']}")
            print("=" * 50)
            print(
                f"Tokens: Input={result['input_tokens']} | Output={result['output_tokens']} | Total={result['total_tokens']}"
            )
            print(f"Latency: {result['latency_ms']:.0f} ms")
            print(
                f"Estimated Cost: ${result['cost_usd']:.6f} (Savings: {result['savings_pct']:.1f}%)"
            )

            alloc_vram, res_vram = VRAMManager.get_vram_usage()
            print(
                f"\n[GPU VRAM Status] Allocated: {alloc_vram:.2f} GB | Reserved: {res_vram:.2f} GB"
            )

    run_button.on_click(handle_click)
    display(console_title, prompt_input, run_button, output_console)
