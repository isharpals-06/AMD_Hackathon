import os
import sys
import shutil
import subprocess

def windows_to_wsl_path(win_path: str) -> str:
    clean_path = win_path.replace("\\", "/")
    if len(clean_path) > 1 and clean_path[1] == ":":
        drive = clean_path[0].lower()
        return f"/mnt/{drive}{clean_path[2:]}"
    return clean_path

def main():
    print("=== Cross-Platform Ollama Model Builder ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    adapter_file = os.path.join(base_dir, "adapter_model.safetensors")
    config_file = os.path.join(base_dir, "adapter_config.json")
    
    if not os.path.exists(adapter_file):
        print(f"[ERROR] Could not find adapter model file at: {adapter_file}")
        sys.exit(1)
        
    if not os.path.exists(config_file):
        print(f"[ERROR] Could not find adapter config file at: {config_file}")
        sys.exit(1)
        
    # Create temporary adapter directory
    temp_adapter_dir = os.path.join(base_dir, "temp_adapter_dir")
    os.makedirs(temp_adapter_dir, exist_ok=True)
    
    # Copy and rename files as expected by Ollama's Go client
    shutil.copy2(adapter_file, os.path.join(temp_adapter_dir, "model.safetensors"))
    shutil.copy2(config_file, os.path.join(temp_adapter_dir, "adapter_config.json"))
    
    # Read base Modelfile template
    modelfile_path = os.path.join(base_dir, "Modelfile")
    if not os.path.exists(modelfile_path):
        print(f"[ERROR] Could not find Modelfile template at: {modelfile_path}")
        sys.exit(1)
        
    with open(modelfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Generate both Windows and WSL absolute paths to attempt
    abs_dir_path = os.path.abspath(temp_adapter_dir)
    windows_style = abs_dir_path.replace("\\", "\\\\") # Escape backslashes for Go quoted string
    wsl_style = windows_to_wsl_path(abs_dir_path)
    
    # Try the default first based on system platform
    paths_to_try = []
    if sys.platform == "win32":
        paths_to_try = [windows_style, wsl_style]
    else:
        paths_to_try = [wsl_style, windows_style]

    build_success = False
    temp_modelfile = os.path.join(base_dir, "Modelfile.tmp")

    for attempt_path in paths_to_try:
        print(f"\n[INFO] Attempting build with adapter directory path: {attempt_path}")
        
        # Replace or add ADAPTER command in Modelfile content
        lines = content.splitlines()
        found_adapter = False
        for i, line in enumerate(lines):
            if line.strip().startswith("ADAPTER"):
                lines[i] = f'ADAPTER "{attempt_path}"'
                found_adapter = True
                break
        if not found_adapter:
            lines.append(f'ADAPTER "{attempt_path}"')
            
        modelfile_content = "\n".join(lines) + "\n"
        
        try:
            with open(temp_modelfile, "w", encoding="utf-8") as f:
                f.write(modelfile_content)
            
            cmd = ["ollama", "create", "llama3-router", "-f", temp_modelfile]
            print(f"[INFO] Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("[SUCCESS] Model created successfully!")
            print(result.stdout)
            build_success = True
            break
        except subprocess.CalledProcessError as e:
            print("[WARNING] Failed with this path configuration.")
            print(f"Stdout: {e.stdout.strip()}")
            print(f"Stderr: {e.stderr.strip()}")
        except FileNotFoundError:
            print("[ERROR] 'ollama' command not found. Please ensure Ollama is installed and added to system PATH.")
            break
            
    # Cleanup temporary directory and files
    if os.path.exists(temp_modelfile):
        os.remove(temp_modelfile)
    if os.path.exists(temp_adapter_dir):
        shutil.rmtree(temp_adapter_dir)
        print("[INFO] Cleaned up temporary adapter directory.")
        
    if build_success:
        print("[INFO] Build process complete.")
        sys.exit(0)
    else:
        print("\n[ERROR] All adapter path options failed. Make sure Ollama service is running and accessible.")
        sys.exit(1)

if __name__ == "__main__":
    main()
