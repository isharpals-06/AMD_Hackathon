# AMD Multi-Model Router — Developer Makefile
# Usage: make <target>

.PHONY: help build up down restart logs ps shell-backend shell-ollama \
        pull-models dev-backend dev-frontend clean

# ─── Variables ────────────────────────────────────────────────────────────────
COMPOSE       := docker compose
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
	@echo "    make build          Build all Docker images"
	@echo "    make up             Start all services (detached)"
	@echo "    make down           Stop and remove containers"
	@echo "    make restart        Rebuild images and restart all services"
	@echo "    make logs           Tail logs from all services"
	@echo "    make ps             Show running container status"
	@echo ""
	@echo "  Model Management"
	@echo "    make pull-models    Pull required Ollama models into the container"
	@echo ""
	@echo "  Shell Access"
	@echo "    make shell-backend  Open shell inside the backend container"
	@echo "    make shell-ollama   Open shell inside the Ollama container"
	@echo ""
	@echo "  Local Dev (no Docker)"
	@echo "    make dev-backend    Run FastAPI server locally (requires venv)"
	@echo "    make dev-frontend   Run Vite dev server locally"
	@echo ""
	@echo "    make clean          Remove all containers, volumes, and images"
	@echo "  ─────────────────────────────────────────────────────────────"
	@echo ""

# ─── Docker targets ───────────────────────────────────────────────────────────
build:
	$(COMPOSE) build --no-cache

up:
	$(COMPOSE) up -d

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
	@echo "Starting FastAPI backend (requires active venv and .env)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting Vite dev server"
	cd frontend && npm run dev

# ─── Clean up ─────────────────────────────────────────────────────────────────
clean:
	@echo "WARNING: This will remove all containers, volumes, and images."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(COMPOSE) down -v --rmi all --remove-orphans
	@echo "Clean complete."
