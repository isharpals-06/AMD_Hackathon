from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ProcessRequest(BaseModel):
    prompt: str = Field(..., min_length=5, description="The input prompt for the router system.")
    task_type: Optional[str] = Field(None, description="Optional override. If not provided, it will be classified using ChromaDB.")

class TokenMetrics(BaseModel):
    input: int
    output: int
    total: int

class CostMetrics(BaseModel):
    usd: float
    currency: str = "USD"

class RouteMetadata(BaseModel):
    task_type: str
    primary_model: str
    fallback_model_used: bool
    final_model_used: str
    latency_ms: int

class ProcessResponse(BaseModel):
    request_id: str
    status: str
    result: str
    metadata: RouteMetadata
    tokens: TokenMetrics
    cost: CostMetrics

class ErrorAttempt(BaseModel):
    model: str
    status: str
    error: str

class ErrorResponse(BaseModel):
    request_id: str
    status: str = "failed"
    error: str
    detail: str
    attempts: List[ErrorAttempt]
