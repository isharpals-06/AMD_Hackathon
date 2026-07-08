import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from app import config
from app.models import ProcessRequest, ProcessResponse, ErrorResponse, RouteMetadata, TokenMetrics, CostMetrics
from app.services.classifier import TaskClassifier
from app.services.router import RoutingEngine
from app.services.executor import ModelExecutor
from app.services.ollama_client import OllamaClient
from app.services.fireworks_client import FireworksClient
from app.database import log_request, get_aggregate_metrics, init_db

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("Initializing SQLite database...")
    init_db()

    logger.info("Initializing ChromaDB classifier service...")
    app.state.classifier = TaskClassifier(persist_directory=config.CHROMADB_DIR)

    yield  # Application is running

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("Shutting down router service.")


app = FastAPI(
    title="SLM-Based Intelligent Multi-Model Router",
    description="Intelligent API router optimized for local SLMs on AMD ROCm GPUs and cloud fallbacks.",
    version="1.0",
    lifespan=lifespan,
)

@app.post("/process", response_model=ProcessResponse, responses={500: {"model": ErrorResponse}})
async def process_prompt(request: ProcessRequest, http_request: Request):
    request_id = str(uuid.uuid4())
    logger.info(f"Received request {request_id}")

    classifier_service: TaskClassifier | None = getattr(http_request.app.state, "classifier", None)

    # 1. Classify task type (use override if provided, otherwise run semantic classification)
    if request.task_type:
        task_type = request.task_type
        logger.info(f"Using manual task_type override: {task_type}")
    else:
        if classifier_service:
            decision = await classifier_service.classify(request.prompt)
            task_type = decision.get("category", "casual_chat")
        else:
            task_type = "casual_chat"
            logger.warning("Classifier service not available. Defaulting to casual_chat.")
            
    # 2. Get routing rules
    routing_rules = RoutingEngine.get_routing(task_type)
    
    # 3. Execute prompt routing (with primary/fallback handling)
    execution_result = await ModelExecutor.execute(request.prompt, routing_rules)
    
    # Assemble database log record
    db_record = {
        "request_id": request_id,
        "prompt": request.prompt,
        "task_type": task_type,
        "prompt_length": len(request.prompt),
        "primary_model": routing_rules["primary_model"],
        "fallback_model_used": 1 if execution_result["fallback_model_used"] else 0,
        "final_model_used": execution_result["final_model_used"],
        "status": execution_result["status"],
        "response": execution_result["result"],
        "response_length": len(execution_result["result"]),
        "tokens_used": execution_result["tokens"]["total"],
        "input_tokens": execution_result["tokens"]["input"],
        "output_tokens": execution_result["tokens"]["output"],
        "cost_usd": execution_result["cost_usd"],
        "latency_ms": execution_result["latency_ms"],
        "error_message": execution_result["error_message"]
    }
    
    # Log asynchronously to SQLite
    try:
        log_request(db_record)
    except Exception as e:
        logger.error(f"Failed to log request to database: {e}")
        
    # Handle failure responses
    if execution_result["status"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "request_id": request_id,
                "status": "failed",
                "error": "All models in fallback chain failed to respond.",
                "detail": execution_result["error_message"],
                "attempts": execution_result["attempts"]
            }
        )
        
    return ProcessResponse(
        request_id=request_id,
        status="success",
        result=execution_result["result"],
        metadata=RouteMetadata(
            task_type=task_type,
            primary_model=routing_rules["primary_model"],
            fallback_model_used=execution_result["fallback_model_used"],
            final_model_used=execution_result["final_model_used"],
            latency_ms=execution_result["latency_ms"]
        ),
        tokens=TokenMetrics(
            input=execution_result["tokens"]["input"],
            output=execution_result["tokens"]["output"],
            total=execution_result["tokens"]["total"]
        ),
        cost=CostMetrics(
            usd=execution_result["cost_usd"]
        )
    )

@app.get("/config")
def get_config():
    """Returns active models and configuration targets."""
    return {
        "status": "success",
        "models": {
            "math": {
                "primary": config.MATH_PRIMARY_MODEL,
                "fallback": config.MATH_FALLBACK_MODEL
            },
            "coding": {
                "primary": config.CODING_PRIMARY_MODEL,
                "fallback": config.CODING_FALLBACK_MODEL
            },
            "research": {
                "primary": config.RESEARCH_PRIMARY_MODEL,
                "fallback": config.RESEARCH_FALLBACK_MODEL
            },
            "casual": {
                "primary": config.CASUAL_PRIMARY_MODEL,
                "fallback": config.CASUAL_FALLBACK_MODEL
            }
        }
    }

@app.get("/metrics")
def get_metrics():
    """Returns aggregated performance and cost savings metrics."""
    try:
        return {
            "status": "success",
            "aggregated_metrics": get_aggregate_metrics()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {e}"
        )

@app.get("/health")
async def get_health():
    """System health check verifying dependencies."""
    ollama_healthy = await OllamaClient.check_health()
    fireworks_healthy = await FireworksClient.check_health()
    
    db_healthy = False
    try:
        # Check SQLite db write/readability
        metrics = get_aggregate_metrics()
        db_healthy = True
    except Exception:
        pass
        
    system_status = "healthy"
    if not (ollama_healthy and fireworks_healthy and db_healthy):
        system_status = "degraded"
        
    return {
        "status": system_status,
        "services": {
            "ollama_local": "connected" if ollama_healthy else "disconnected",
            "fireworks_cloud": "connected" if fireworks_healthy else "disconnected",
            "sqlite_metrics_db": "healthy" if db_healthy else "unhealthy"
        }
    }
