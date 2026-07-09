"""
Enhanced Pydantic request/response schemas.

Changes from v1:
  - Added HealthResponse, VersionResponse, MetricsResponse typed models
  - Added input validators (prompt length cap, whitespace stripping)
  - Added TaskType literal enum for safer routing
"""
from __future__ import annotations

from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, field_validator

# ── Input / Request ──────────────────────────────────────────────────────────

VALID_TASK_TYPES = {"math", "coding", "research", "casual_chat"}


class ProcessRequest(BaseModel):
    """Incoming prompt routing request."""

    prompt: Annotated[
        str,
        Field(
            min_length=5,
            max_length=8000,
            description="The input prompt for the router system.",
            examples=["Solve for x: 3x + 5 = 20"],
        ),
    ]
    task_type: Optional[str] = Field(
        default=None,
        description=(
            "Optional task-type override. "
            "Valid values: math, coding, research, casual_chat. "
            "If not provided, the 3-tier classifier will be used."
        ),
    )

    @field_validator("prompt", mode="before")
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        """Strip leading/trailing whitespace from the prompt."""
        return v.strip()

    @field_validator("task_type", mode="before")
    @classmethod
    def validate_task_type(cls, v: Optional[str]) -> Optional[str]:
        """Ensure manual overrides use a recognised task type."""
        if v is None:
            return v
        normalised = v.strip().lower()
        if normalised not in VALID_TASK_TYPES:
            raise ValueError(
                f"Invalid task_type '{v}'. Must be one of: {sorted(VALID_TASK_TYPES)}"
            )
        return normalised


class SeedRequest(BaseModel):
    """A single labeled example for seeding the classifier."""
    text: str = Field(min_length=5, description="The example prompt.")
    category: str = Field(description="The category of the prompt.")

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised not in VALID_TASK_TYPES:
            raise ValueError(f"Invalid category '{v}'. Must be one of: {sorted(VALID_TASK_TYPES)}")
        return normalised


class SeedBatchRequest(BaseModel):
    """Batch payload for adding multiple seed examples."""
    seeds: list[SeedRequest] = Field(min_length=1, description="List of seed examples to add.")


# ── Response sub-models ───────────────────────────────────────────────────────


class TokenMetrics(BaseModel):
    """Token usage breakdown."""

    input: int = Field(ge=0, description="Number of input/prompt tokens")
    output: int = Field(ge=0, description="Number of output/completion tokens")
    total: int = Field(ge=0, description="Total tokens (input + output)")


class CostMetrics(BaseModel):
    """Cost estimate for the request."""

    usd: float = Field(ge=0.0, description="Estimated cost in US dollars")
    currency: str = Field(default="USD", description="Currency code")


class RouteMetadata(BaseModel):
    """Routing decision metadata returned alongside the response."""

    task_type: str = Field(description="Classified task category")
    primary_model: str = Field(description="The configured primary model for this task type")
    fallback_model_used: bool = Field(description="Whether the fallback model was used")
    final_model_used: str = Field(description="The model that actually produced the response")
    latency_ms: int = Field(ge=0, description="Total request latency in milliseconds")


class ProcessResponse(BaseModel):
    """Successful prompt routing response."""

    request_id: str = Field(description="Unique identifier for this request")
    status: str = Field(description="Request status: success | success_via_fallback")
    result: str = Field(description="Model response text")
    metadata: RouteMetadata
    tokens: TokenMetrics
    cost: CostMetrics


# ── Error models ──────────────────────────────────────────────────────────────


class ErrorAttempt(BaseModel):
    """Details of a single failed model invocation."""

    model: str
    status: str
    error: str


class ErrorResponse(BaseModel):
    """Response returned when all models in the fallback chain fail."""

    request_id: str
    status: str = "failed"
    error: str
    detail: str
    attempts: list[ErrorAttempt]


# ── Health / Info models ──────────────────────────────────────────────────────


class ServiceStatus(BaseModel):
    """Status of a single downstream service."""

    name: str
    status: str  # connected | disconnected | healthy | unhealthy
    latency_ms: Optional[int] = None


class HealthResponse(BaseModel):
    """System health check response."""

    status: str = Field(description="overall: healthy | degraded | unhealthy")
    services: dict[str, str] = Field(description="Per-service status map")
    version: str = Field(description="Application version")


class VersionResponse(BaseModel):
    """API version information."""

    version: str
    api_version: str
    environment: str


# ── Metrics response ──────────────────────────────────────────────────────────


class AggregateMetrics(BaseModel):
    """Aggregated performance and cost metrics from the SQLite log."""

    total_requests: int = 0
    successful_requests: int = 0
    total_tokens: Optional[int] = 0
    total_cost: Optional[float] = 0.0
    avg_latency_ms: Optional[float] = 0.0
    fallback_count: int = 0
    baseline_cost_usd: float = 0.0
    cost_saved_usd: float = 0.0
    savings_pct: float = 0.0


class MetricsResponse(BaseModel):
    """Response for the /metrics/summary endpoint."""

    status: str = "success"
    aggregated_metrics: dict[str, Any]


# ── ChromaDB Seeding models ───────────────────────────────────────────────────

class SeedRequest(BaseModel):
    """Request payload to dynamically add a seed example to ChromaDB."""

    prompt: str = Field(min_length=5, description="The example prompt text")
    category: str = Field(description="The labeled category (math, coding, research, casual_chat)")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised not in VALID_TASK_TYPES:
            raise ValueError(f"Invalid category '{v}'. Must be one of: {sorted(VALID_TASK_TYPES)}")
        return normalised


class SeedResponse(BaseModel):
    """Response payload for the dynamic ChromaDB seeding endpoint."""

    status: str = "success"
    message: str
    id: str
    category: str
