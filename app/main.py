"""
FastAPI application entrypoint.

Production enhancements over v1:
  - Pydantic Settings config (startup validation)
  - CORS middleware with configurable origins
  - Slowapi rate limiting (per-IP, configurable)
  - Optional API key authentication header
  - Prometheus metrics endpoint (via prometheus-fastapi-instrumentator)
  - /version endpoint
  - /metrics/summary renamed from /metrics (avoids clash with Prometheus)
  - Structured logging via JSON formatter
  - Global exception handlers (422, 500)
  - Request-ID header propagation via middleware
"""
from __future__ import annotations

import logging
import logging.config
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import config
from app.database import (
    get_aggregate_metrics,
    get_per_model_metrics,
    init_db,
    log_request,
)
from app.middleware.logging_middleware import StructuredLoggingMiddleware
from app.models import (
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    ProcessRequest,
    ProcessResponse,
    RouteMetadata,
    TokenMetrics,
    CostMetrics,
    VersionResponse,
)
from app.services.classifier import TaskClassifier
from app.services.executor import ModelExecutor
from app.services.fireworks_client import FireworksClient
from app.services.ollama_client import OllamaClient
from app.services.router import RoutingEngine

# ── Logging setup ─────────────────────────────────────────────────────────────
# Build the logging config — use JSON formatter if python-json-logger is installed
_json_formatter: dict = {
    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
}
try:
    # python-json-logger ≥ 3.x uses pythonjsonlogger.json
    from pythonjsonlogger import json as _pjl_json  # noqa: F401
    _json_formatter["()"] = "pythonjsonlogger.json.JsonFormatter"
except ImportError:
    try:
        # python-json-logger 2.x uses pythonjsonlogger.jsonlogger
        from pythonjsonlogger import jsonlogger as _pjl_old  # noqa: F401
        _json_formatter["()"] = "pythonjsonlogger.jsonlogger.JsonFormatter"
    except ImportError:
        # No JSON logger available — fall back to simple text format
        _json_formatter = {"format": "%(asctime)s %(name)s %(levelname)s %(message)s"}

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": _json_formatter,
        "simple": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if not config.DEBUG else "simple",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": config.LOG_LEVEL,
        "handlers": ["console"],
    },
})
logger = logging.getLogger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, enabled=config.RATE_LIMIT_ENABLED)

# ── API Key security scheme ───────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> None:
    """Validate X-API-Key header when API_KEY_ENABLED is True."""
    if not config.API_KEY_ENABLED:
        return
    if not config.API_KEY or api_key != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass your key in the X-API-Key header.",
        )


# ── Application lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # Startup
    logger.info("Initialising SQLite database...")
    init_db()

    logger.info("Initialising ChromaDB classifier service...")
    application.state.classifier = TaskClassifier(persist_directory=config.CHROMADB_DIR)

    # Attach Prometheus instrumentation if enabled
    if config.PROMETHEUS_ENABLED:
        try:
            from prometheus_fastapi_instrumentator import Instrumentator

            Instrumentator(
                should_group_status_codes=False,
                should_ignore_untemplated=True,
                should_respect_env_var=True,
                should_instrument_requests_inprogress=True,
                excluded_handlers=["/metrics"],
                inprogress_name="amd_router_inprogress",
                inprogress_labels=True,
            ).instrument(application).expose(application, endpoint="/metrics")
            logger.info("Prometheus metrics exposed at /metrics")
        except ImportError:
            logger.warning(
                "prometheus-fastapi-instrumentator not installed. Prometheus metrics disabled."
            )

    logger.info("Application startup complete.")
    yield

    # Shutdown
    logger.info("Shutting down router service.")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="SLM-Based Intelligent Multi-Model Router",
    description=(
        "Intelligent API router optimised for local SLMs on AMD ROCm GPUs "
        "with automatic cloud fallback via Fireworks AI."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware (order matters — outermost first) ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)

# ── Rate-limit error handler ──────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Global error handlers ─────────────────────────────────────────────────────
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.exception("Unhandled server error [request_id=%s]", request_id)
    return JSONResponse(
        status_code=500,
        content={"request_id": request_id, "error": "Internal server error"},
    )


# ═════════════════════════════════════════════════════════════════════════════
#  Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/version",
    response_model=VersionResponse,
    summary="API version information",
    tags=["System"],
)
async def get_version() -> VersionResponse:
    """Returns the API version and environment information."""
    return VersionResponse(
        version="1.0.0",
        api_version="v1",
        environment="production" if not config.DEBUG else "development",
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
    tags=["System"],
)
async def get_health() -> HealthResponse:
    """Verify connectivity to all downstream dependencies."""
    ollama_healthy = await OllamaClient.check_health()
    fireworks_healthy = await FireworksClient.check_health()

    db_healthy = False
    try:
        get_aggregate_metrics()
        db_healthy = True
    except Exception:
        pass

    system_status = "healthy" if (ollama_healthy and db_healthy) else "degraded"

    return HealthResponse(
        status=system_status,
        version="1.0.0",
        services={
            "ollama_local": "connected" if ollama_healthy else "disconnected",
            "fireworks_cloud": "connected" if fireworks_healthy else "disconnected",
            "sqlite_metrics_db": "healthy" if db_healthy else "unhealthy",
        },
    )


@app.post(
    "/process",
    response_model=ProcessResponse,
    responses={
        429: {"description": "Rate limit exceeded"},
        401: {"description": "Unauthorised — invalid API key"},
        500: {"model": ErrorResponse},
    },
    summary="Route and execute a prompt",
    tags=["Routing"],
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def process_prompt(
    request: Request,
    body: ProcessRequest,
) -> ProcessResponse:
    """
    Classify the incoming prompt and route it to the optimal model.

    The classifier uses a 3-tier cascade:
    1. Fine-tuned Llama-3.2-1B SLM
    2. ChromaDB semantic vector search
    3. Keyword regex fallback
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.info("Processing request [request_id=%s]", request_id)

    classifier_service: TaskClassifier | None = getattr(
        request.app.state, "classifier", None
    )

    # 1. Classify task type
    if body.task_type:
        task_type = body.task_type
        logger.info("Manual task_type override: %s [request_id=%s]", task_type, request_id)
    else:
        if classifier_service:
            decision = await classifier_service.classify(body.prompt)
            task_type = decision.get("category", "casual_chat")
        else:
            task_type = "casual_chat"
            logger.warning(
                "Classifier not available, defaulting to casual_chat [request_id=%s]",
                request_id,
            )

    # 2. Get routing rules
    routing_rules = RoutingEngine.get_routing(task_type)

    # 3. Execute with primary/fallback chain
    execution_result = await ModelExecutor.execute(body.prompt, routing_rules)

    # 4. Log to SQLite (non-blocking best-effort)
    db_record: dict[str, Any] = {
        "request_id": request_id,
        "prompt": body.prompt,
        "task_type": task_type,
        "prompt_length": len(body.prompt),
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
        "error_message": execution_result["error_message"],
    }
    try:
        log_request(db_record)
    except Exception as db_err:
        logger.error("Failed to log request to DB: %s [request_id=%s]", db_err, request_id)

    # 5. Handle failure
    if execution_result["status"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "request_id": request_id,
                "status": "failed",
                "error": "All models in the fallback chain failed to respond.",
                "detail": execution_result["error_message"],
                "attempts": execution_result["attempts"],
            },
        )

    return ProcessResponse(
        request_id=request_id,
        status=execution_result["status"],
        result=execution_result["result"],
        metadata=RouteMetadata(
            task_type=task_type,
            primary_model=routing_rules["primary_model"],
            fallback_model_used=execution_result["fallback_model_used"],
            final_model_used=execution_result["final_model_used"],
            latency_ms=execution_result["latency_ms"],
        ),
        tokens=TokenMetrics(
            input=execution_result["tokens"]["input"],
            output=execution_result["tokens"]["output"],
            total=execution_result["tokens"]["total"],
        ),
        cost=CostMetrics(usd=execution_result["cost_usd"]),
    )


@app.get(
    "/metrics/summary",
    response_model=MetricsResponse,
    summary="Aggregated performance metrics",
    tags=["Analytics"],
)
def get_metrics_summary() -> MetricsResponse:
    """Returns aggregated performance, token, and cost-savings metrics from SQLite."""
    try:
        return MetricsResponse(aggregated_metrics=get_aggregate_metrics())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {e}",
        )


@app.get(
    "/metrics/models",
    summary="Per-model performance breakdown",
    tags=["Analytics"],
)
def get_model_metrics() -> dict[str, Any]:
    """Returns per-model request count, avg latency, and cost breakdown."""
    try:
        return {
            "status": "success",
            "models": get_per_model_metrics(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch per-model metrics: {e}",
        )


# ── Legacy alias — keep /metrics working for existing clients ─────────────────
@app.get("/metrics/legacy", include_in_schema=False)
def get_metrics_legacy():
    """Deprecated: use /metrics/summary instead."""
    try:
        return {"status": "success", "aggregated_metrics": get_aggregate_metrics()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {e}")
