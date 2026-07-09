"""
Integration tests for the FastAPI router API.

These tests exercise the full request/response cycle using
TestClient with mocked external services (Ollama, Fireworks).
No running Ollama or Fireworks instance is required.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestVersionEndpoint:
    def test_version_returns_200(self, client: TestClient):
        response = client.get("/version")
        assert response.status_code == 200

    def test_version_has_required_fields(self, client: TestClient):
        data = client.get("/version").json()
        assert "version" in data
        assert "api_version" in data
        assert "environment" in data

    def test_version_value(self, client: TestClient):
        data = client.get("/version").json()
        assert data["version"] == "1.0.0"


@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_status_field(self, client: TestClient):
        data = client.get("/health").json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")

    def test_health_has_services_field(self, client: TestClient):
        data = client.get("/health").json()
        assert "services" in data
        assert isinstance(data["services"], dict)


@pytest.mark.integration
class TestProcessEndpoint:
    """Tests for POST /process."""

    VALID_PAYLOAD = {"prompt": "Write a Python function to reverse a string."}

    def test_process_returns_200_on_valid_prompt(self, client: TestClient):
        response = client.post("/process", json=self.VALID_PAYLOAD)
        assert response.status_code == 200

    def test_process_response_has_all_fields(self, client: TestClient):
        data = client.post("/process", json=self.VALID_PAYLOAD).json()
        assert "request_id" in data
        assert "status" in data
        assert "result" in data
        assert "metadata" in data
        assert "tokens" in data
        assert "cost" in data

    def test_process_metadata_has_routing_info(self, client: TestClient):
        data = client.post("/process", json=self.VALID_PAYLOAD).json()
        meta = data["metadata"]
        assert "task_type" in meta
        assert "primary_model" in meta
        assert "fallback_model_used" in meta
        assert "final_model_used" in meta
        assert "latency_ms" in meta

    def test_process_with_manual_task_type_override(self, client: TestClient):
        payload = {"prompt": "Hello there friend!", "task_type": "casual_chat"}
        data = client.post("/process", json=payload).json()
        assert data["metadata"]["task_type"] == "casual_chat"

    def test_process_rejects_prompt_too_short(self, client: TestClient):
        response = client.post("/process", json={"prompt": "hi"})
        assert response.status_code == 422

    def test_process_rejects_prompt_too_long(self, client: TestClient):
        response = client.post("/process", json={"prompt": "x" * 8001})
        assert response.status_code == 422

    def test_process_rejects_invalid_task_type(self, client: TestClient):
        response = client.post(
            "/process",
            json={"prompt": "Valid prompt here.", "task_type": "invalid_type"},
        )
        assert response.status_code == 422

    def test_process_rejects_empty_body(self, client: TestClient):
        response = client.post("/process", json={})
        assert response.status_code == 422

    def test_request_id_in_response_header(self, client: TestClient):
        response = client.post("/process", json=self.VALID_PAYLOAD)
        assert "x-request-id" in response.headers


@pytest.mark.integration
class TestMetricsEndpoints:
    def test_metrics_summary_returns_200(self, client: TestClient):
        response = client.get("/metrics/summary")
        assert response.status_code == 200

    def test_metrics_summary_has_status_field(self, client: TestClient):
        data = client.get("/metrics/summary").json()
        assert data["status"] == "success"

    def test_metrics_summary_has_aggregated_metrics(self, client: TestClient):
        data = client.get("/metrics/summary").json()
        assert "aggregated_metrics" in data

    def test_model_metrics_returns_200(self, client: TestClient):
        response = client.get("/metrics/models")
        assert response.status_code == 200

    def test_model_metrics_has_models_field(self, client: TestClient):
        data = client.get("/metrics/models").json()
        assert "models" in data
        assert isinstance(data["models"], list)


@pytest.mark.integration
class TestOpenAPI:
    def test_openapi_docs_accessible(self, client: TestClient):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_accessible(self, client: TestClient):
        response = client.get("/openapi.json")
        assert response.status_code == 200
