"""
Model Registry

Maintains a JSON-based model registry at `models/registry.json`.

Each entry records:
  - version (semver)
  - mlflow_run_id
  - model_path
  - accuracy / macro_f1
  - stage: staging | production | archived
  - registered_at timestamp
  - promoted_at timestamp (if production)
  - git_commit (if available)

Supports:
  - register_model(): add a new staging entry
  - promote_to_production(): mark a version as production (archives the old one)
  - get_production_model(): return the current production entry
  - list_versions(): show all registered versions
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path("./models/registry.json")
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {"versions": []}


def _save_registry(registry: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2, default=str)
    logger.info("Registry saved to %s", REGISTRY_PATH)


def register_model(
    version: str,
    mlflow_run_id: str,
    model_path: str | Path,
    accuracy: float,
    macro_f1: float,
    parameters: Optional[dict[str, Any]] = None,
    git_commit: Optional[str] = None,
) -> dict[str, Any]:
    """
    Register a newly trained model as 'staging'.

    Parameters
    ----------
    version:
        Semantic version string, e.g. "1.2.0".
    mlflow_run_id:
        The MLflow run ID from the training stage.
    model_path:
        Path to the saved model artifact.
    accuracy / macro_f1:
        Validation metrics from training.
    parameters:
        Hyperparameters dict (optional, for documentation).
    git_commit:
        Short git SHA for traceability.
    """
    registry = _load_registry()

    # Check for duplicate version
    existing = [v for v in registry["versions"] if v["version"] == version]
    if existing:
        logger.warning("Version %s already exists in registry. Overwriting.", version)
        registry["versions"] = [v for v in registry["versions"] if v["version"] != version]

    entry: dict[str, Any] = {
        "version": version,
        "mlflow_run_id": mlflow_run_id,
        "model_path": str(model_path),
        "stage": "staging",
        "metrics": {
            "accuracy": round(accuracy, 4),
            "macro_f1": round(macro_f1, 4),
        },
        "parameters": parameters or {},
        "git_commit": git_commit,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "promoted_at": None,
    }

    registry["versions"].append(entry)
    _save_registry(registry)
    logger.info("Registered model version %s (stage=staging, run_id=%s)", version, mlflow_run_id)
    return entry


def promote_to_production(version: str) -> dict[str, Any]:
    """
    Promote a staging model to production.

    Archives the previous production model (if any).
    Raises ValueError if the version does not exist or is already archived.
    """
    registry = _load_registry()
    versions = registry["versions"]

    target = next((v for v in versions if v["version"] == version), None)
    if target is None:
        raise ValueError(f"Version '{version}' not found in registry.")
    if target["stage"] == "archived":
        raise ValueError(f"Version '{version}' is archived and cannot be promoted.")

    # Archive the current production model
    for v in versions:
        if v["stage"] == "production":
            v["stage"] = "archived"
            logger.info("Archived previous production model: %s", v["version"])

    # Promote the target
    target["stage"] = "production"
    target["promoted_at"] = datetime.now(timezone.utc).isoformat()

    _save_registry(registry)
    logger.info("Promoted model version %s to production", version)
    return target


def get_production_model() -> Optional[dict[str, Any]]:
    """Return the current production model entry, or None if none exists."""
    registry = _load_registry()
    for v in reversed(registry["versions"]):
        if v["stage"] == "production":
            return v
    return None


def list_versions() -> list[dict[str, Any]]:
    """Return all registered model versions in registration order."""
    return _load_registry().get("versions", [])


def rollback(previous_version: str) -> dict[str, Any]:
    """
    Roll back to a previous version by promoting it to production.

    This archives the current production model and promotes the target version.
    """
    logger.warning("Rolling back to version %s", previous_version)
    return promote_to_production(previous_version)
