# AMD Multi-Model Router — Developer Makefile
# Usage: make <target>

.PHONY: help build up down restart logs ps shell-backend shell-ollama \
        pull-models dev-backend dev-frontend clean \
        test lint format type-check \
        pipeline pipeline-list promote \
        mlflow-ui generate-dataset

# ─── Variables ────────────────────────────────────────────────────────────────
COMPOSE       := docker compose
COMPOSE_DEV   := docker compose -f docker-compose.yml -f docker-compose.dev.yml
BACKEND_SVC   := backend
FRONTEND_SVC  := frontend
OLLAMA_SVC    := ollama

# Models required by the router
OLLAMA_MODELS := qwen:7b nomic-embed-text llama3-router

# ─── Default: show help ───────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  AMD Multi-Model Router — available targets"
	@echo "  ─────────────────────────────────────────────────────────────"
	@echo "  Docker"
	@echo "    make build          Build all Docker images (production)"
	@echo "    make up             Start all services (detached)"
	@echo "    make up-dev         Start with hot-reload dev overrides"
	@echo "    make down           Stop and remove containers"
	@echo "    make restart        Rebuild images and restart all services"
	@echo "    make logs           Tail logs from all services"
	@echo "    make ps             Show running container status"
	@echo ""
	@echo "  Model Management"
	@echo "    make pull-models    Pull required Ollama models"
	@echo ""
	@echo "  Shell Access"
	@echo "    make shell-backend  Open shell inside the backend container"
	@echo "    make shell-ollama   Open shell inside the Ollama container"
	@echo ""
	@echo "  Local Dev (no Docker)"
	@echo "    make dev-backend    Run FastAPI server locally (requires venv)"
	@echo "    make dev-frontend   Run Vite dev server locally"
	@echo ""
	@echo "  Code Quality"
	@echo "    make lint           Run black + isort + ruff checks"
	@echo "    make format         Auto-format with black + isort"
	@echo "    make type-check     Run mypy type checking"
	@echo "    make test           Run full test suite with coverage"
	@echo ""
	@echo "  ML Pipeline"
	@echo "    make generate-dataset  Generate synthetic training data"
	@echo "    make pipeline          Run full ML pipeline (validate→train→register)"
	@echo "    make pipeline-list     List registered model versions"
	@echo "    make mlflow-ui         Start MLflow UI (http://localhost:5000)"
	@echo ""
	@echo "    make clean          Remove all containers, volumes, and images"
	@echo "  ─────────────────────────────────────────────────────────────"
	@echo ""

# ─── Docker targets ───────────────────────────────────────────────────────────
build:
	$(COMPOSE) build --no-cache

up:
	$(COMPOSE) up -d

up-dev:
	$(COMPOSE_DEV) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) build
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

# ─── Model management ─────────────────────────────────────────────────────────
pull-models:
	@echo "Pulling Ollama models: $(OLLAMA_MODELS)"
	@for model in $(OLLAMA_MODELS); do \
		echo "  → Pulling $$model ..."; \
		$(COMPOSE) exec $(OLLAMA_SVC) ollama pull $$model; \
	done
	@echo "All models pulled successfully."

# ─── Shell access ─────────────────────────────────────────────────────────────
shell-backend:
	$(COMPOSE) exec $(BACKEND_SVC) /bin/bash

shell-ollama:
	$(COMPOSE) exec $(OLLAMA_SVC) /bin/bash

# ─── Local dev (without Docker) ───────────────────────────────────────────────
dev-backend:
	@echo "Starting FastAPI backend with hot-reload (requires active venv and .env)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting Vite dev server"
	cd frontend && npm run dev

# ─── Code Quality ─────────────────────────────────────────────────────────────
lint:
	@echo "Running black (check)..."
	black --check .
	@echo "Running isort (check)..."
	isort --check .
	@echo "Running ruff..."
	ruff check .
	@echo "Lint passed!"

format:
	@echo "Formatting with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .
	@echo "Formatting complete."

type-check:
	@echo "Running mypy..."
	mypy app/

test:
	@echo "Running test suite..."
	pytest tests/ -v --tb=short \
		--cov=app \
		--cov-report=term-missing \
		--cov-report=html:htmlcov
	@echo "Coverage report: htmlcov/index.html"

# ─── ML Pipeline ──────────────────────────────────────────────────────────────
generate-dataset:
	@echo "Generating synthetic training dataset..."
	python scripts/generate_dataset.py

pipeline:
	@echo "Running ML pipeline (validate → preprocess → train → register)..."
	python -m ml.pipeline run \
		--data-path ./data/training_dataset.csv \
		--version 1.0.0 \
		--auto-promote

pipeline-list:
	python -m ml.pipeline list-versions

mlflow-ui:
	@echo "Starting MLflow UI at http://localhost:5000"
	mlflow ui --backend-store-uri ./mlruns --port 5000

# ─── Clean up ─────────────────────────────────────────────────────────────────
clean:
	@echo "WARNING: This will remove all containers, volumes, and images."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(COMPOSE) down -v --rmi all --remove-orphans
	@echo "Clean complete."
