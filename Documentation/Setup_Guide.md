# 🚀 Developer Setup Guide
**Project:** Intelligent Multi-Model Fallback Router  

---

## 1. Prerequisites (AMD GPU ROCm Stack)
Ensure your host machine is running Linux (Ubuntu 22.04 recommended) with compatible AMD GPU drivers and the ROCm toolkit installed.

### Install ROCm PyTorch
Install PyTorch compiled with ROCm support:
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
```

---

## 2. Virtual Environment Setup
1.  Clone the repository and navigate to the project directory.
2.  Create and activate a python virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/env/activate
    ```
3.  Install python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## 3. Ollama & HuggingFace Setup
1.  Install Ollama locally following instructions at [ollama.com](https://ollama.com).
2.  Download the base models:
    ```bash
    ollama pull llama3.2:1b
    ollama pull nomic-embed-text
    ```
3.  Compile your fine-tuned router model in Ollama (works cross-platform on Windows and Linux/WSL):
    ```bash
    python scripts/build_router.py
    ```

---

## 4. Run Backend & Database Initialization
1.  Initialize your SQLite database metrics schema:
    ```bash
    python scripts/init_db.py
    ```
2.  Start the FastAPI backend server:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

---

## 5. React Dashboard Initialization
1.  Create a React+Vite app in your workspace:
    ```bash
    npm create vite@latest frontend -- --template react
    cd frontend
    npm install
    ```
2.  Run the local development server:
    ```bash
    npm run dev
    ```
