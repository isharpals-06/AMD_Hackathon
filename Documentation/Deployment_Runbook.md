# Deployment Runbook
## Multi-Model Fallback Router

**Version:** 1.0  
**Last Updated:** July 2026  

---

## 1. Pre-Deployment Checklist

Before deploying, ensure:
- [ ] All tests passing (run `pytest -v`)
- [ ] Code linted (run `black app/ && flake8 app/`)
- [ ] No hardcoded secrets in code
- [ ] Docker image builds successfully
- [ ] Environment variables documented
- [ ] README up to date
- [ ] Setup instructions tested on clean machine

---

## 2. Docker Setup

### 2.1 Dockerfile

**File: `Dockerfile`**
```dockerfile
# Multi-stage build for smaller image
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY scripts/ ./scripts/

# Set PATH for pip packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Build Docker Image

```bash
# Build image
docker build -t multi-model-router:latest .

# Tag for registry (if pushing to Docker Hub or other registry)
docker tag multi-model-router:latest yourregistry/multi-model-router:latest

# Verify image
docker images | grep multi-model-router
```

### 2.3 Test Docker Image Locally

```bash
# Run container with environment variables
docker run -p 8000:8000 \
  -e FIREWORKS_API_KEY=your_api_key \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -e DEBUG=False \
  multi-model-router:latest

# Test health check
curl http://localhost:8000/health

# Stop container
docker stop <container_id>
```

---

## 3. Docker Compose Setup (Recommended)

### 3.1 docker-compose.yml

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - FIREWORKS_API_KEY=${FIREWORKS_API_KEY}
      - OLLAMA_URL=http://ollama:11434
      - DATABASE_URL=sqlite:///./data/metrics.db
      - DEBUG=False
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    depends_on:
      - ollama
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_models:/root/.ollama
      - ./init_ollama.sh:/init_ollama.sh
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    # Run initialization script on startup
    entrypoint: |
      sh -c '
      ollama serve &
      sleep 10
      bash /init_ollama.sh
      wait
      '

networks:
  app-network:
    driver: bridge

volumes:
  data:
  ollama_models:
```

### 3.2 Docker Compose Environment File

**File: `.env.example`** (copy to `.env` for deployment)
```
# Fireworks API Configuration
FIREWORKS_API_KEY=your_api_key_here

# Ollama Configuration
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=qwen:7b

# Database Configuration
DATABASE_URL=sqlite:///./data/metrics.db

# App Configuration
DEBUG=False
LOG_LEVEL=INFO
PORT=8000
HOST=0.0.0.0
```

### 3.3 Initialize Ollama Models Script

**File: `init_ollama.sh`**
```bash
#!/bin/bash

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama is ready!"
    break
  fi
  echo "Attempt $i: Ollama not ready yet, waiting..."
  sleep 2
done

# Pull Qwen model
echo "Pulling Qwen model..."
ollama pull qwen:7b

echo "Ollama initialization complete"
```

---

## 4. Deployment Steps

### Step 1: Prepare Environment

```bash
# Clone repository
git clone https://github.com/your-team/multi-model-router.git
cd multi-model-router

# Create .env file from template
cp .env.example .env

# Edit .env with your Fireworks API key
nano .env
# Set: FIREWORKS_API_KEY=your_actual_key
```

### Step 2: Build & Start Services

```bash
# Build and start all services (API + Ollama)
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f api
docker-compose logs -f ollama
```

### Step 3: Verify Deployment

```bash
# Check services are running
docker-compose ps
# Output should show both 'api' and 'ollama' as 'Up'

# Test health check
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}

# Test API endpoint
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize quantum computing", "task_type": "summarization"}'
```

### Step 4: Run Tests

```bash
# Install dependencies (if not in container)
pip install -r requirements.txt

# Run test suite
pytest -v

# Or run inside container
docker-compose exec api pytest -v
```

---

## 5. Monitoring & Logs

### 5.1 View Logs

```bash
# View all logs
docker-compose logs

# View API logs only
docker-compose logs api

# View Ollama logs only
docker-compose logs ollama

# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100 api
```

### 5.2 Check Container Health

```bash
# Check container status
docker-compose ps

# Inspect running container
docker-compose exec api curl http://localhost:8000/health

# SSH into container for debugging
docker-compose exec api /bin/bash
```

### 5.3 Database Status

```bash
# Access database from container
docker-compose exec api sqlite3 /app/data/metrics.db

# Query requests
sqlite> SELECT COUNT(*) FROM requests;

# Exit
sqlite> .quit
```

---

## 6. Troubleshooting

### Issue: Docker build fails

**Symptom:** `docker-compose up --build` fails
```
Step 5/10 : RUN pip install --user --no-cache-dir -r requirements.txt
ERROR: ...
```

**Solution:**
```bash
# Clean up old images
docker-compose down -v
docker system prune -a

# Rebuild
docker-compose up --build
```

### Issue: Port 8000 already in use

**Symptom:** `Error response from daemon: Bind for 0.0.0.0:8000 failed`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port in docker-compose.yml
# ports:
#   - "8001:8000"
```

### Issue: Ollama model not loading

**Symptom:** Ollama container running but model not available
```
curl http://localhost:11434/api/tags
# Returns: {"models": []}
```

**Solution:**
```bash
# Check Ollama logs
docker-compose logs ollama

# Manually pull model
docker-compose exec ollama ollama pull qwen:7b

# Verify
docker-compose exec ollama ollama list
```

### Issue: Fireworks API authentication fails

**Symptom:** `API key not found` or `Invalid API key`

**Solution:**
```bash
# Verify .env file has API key
cat .env | grep FIREWORKS_API_KEY

# Test API key directly
curl -H "Authorization: Bearer YOUR_KEY" \
  https://api.fireworks.ai/inference/v1/completions

# If test fails, regenerate API key in Fireworks dashboard
```

### Issue: Container exits immediately

**Symptom:** `docker-compose ps` shows `Exited (1)`

**Solution:**
```bash
# Check logs
docker-compose logs api

# Common causes:
# 1. Invalid API key
# 2. Ollama not reachable
# 3. Database initialization failed

# Verify health
curl http://localhost:8000/health
```

---

## 7. Cleanup & Shutdown

### Stop Services

```bash
# Stop all services (keep data)
docker-compose stop

# Stop and remove containers (keep data)
docker-compose down

# Stop, remove containers AND volumes (DELETE DATA)
docker-compose down -v
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (WARNING: removes ALL unused Docker objects)
docker system prune -a --volumes
```

---

## 8. Production Deployment Considerations

### For Hackathon (Cloud Deployment)
If deploying to cloud (AWS, GCP, Azure):

1. **Use cloud provider's container service:**
   - AWS ECS / Fargate
   - Google Cloud Run
   - Azure Container Instances

2. **Environment variables:** Use managed secrets service
   - AWS Secrets Manager
   - Google Secret Manager
   - Azure Key Vault

3. **Storage:** Use managed database instead of SQLite
   - AWS RDS
   - Google Cloud SQL
   - Azure Database

4. **Example: AWS ECS Task Definition**
```json
{
  "family": "multi-model-router",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "YOUR_ECR_REPO/multi-model-router:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OLLAMA_URL",
          "value": "http://ollama:11434"
        }
      ],
      "secrets": [
        {
          "name": "FIREWORKS_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:fireworks-api-key"
        }
      ]
    }
  ]
}
```

---

## 9. Performance Optimization

### Docker Compose Optimization

```yaml
# In docker-compose.yml, add resources:
services:
  api:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  ollama:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### Network Optimization

```yaml
# Use host network for local development (faster)
services:
  api:
    # ... existing config ...
    network_mode: "host"  # macOS/Linux only
```

---

## 10. Backup & Recovery

### Database Backup

```bash
# Backup database
docker-compose exec api cp /app/data/metrics.db /app/data/metrics.db.backup

# Extract backup from container
docker cp <container_id>:/app/data/metrics.db ./metrics.db.backup
```

### Recovery

```bash
# Stop services
docker-compose down

# Restore backup
cp metrics.db.backup data/metrics.db

# Restart
docker-compose up
```

---

## 11. Deployment Checklist (For Submission)

- [ ] Code reviewed and approved
- [ ] All tests passing
- [ ] Docker image builds successfully
- [ ] docker-compose.yml works on clean machine
- [ ] .env.example has all required variables documented
- [ ] Health check passes
- [ ] API endpoint responds correctly
- [ ] Logs are clean (no errors)
- [ ] Database initialized correctly
- [ ] README has setup instructions
- [ ] Submission package ready

---

## 12. Quick Reference Commands

```bash
# Start everything
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f api

# Run tests
docker-compose exec api pytest -v

# Get metrics
curl http://localhost:8000/metrics

# Stop everything
docker-compose down

# Clean everything
docker-compose down -v && docker system prune -a
```

---

## End of Deployment Runbook
