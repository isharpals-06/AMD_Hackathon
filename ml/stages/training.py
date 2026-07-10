"""
Stage 3: Training with MLflow Experiment Tracking

Trains a TF-IDF + Logistic Regression baseline classifier for the
router task categories. This acts as the reproducible, versioned
reference classifier — the fine-tuned Llama SLM is the Tier-1 model,
this is the auditable fallback.

Tracked with MLflow:
  - Parameters: max_features, C (regularisation), ngram_range, test_size
  - Metrics: accuracy, per-class precision/recall/f1, macro averages
  - Artifacts: trained model (joblib), confusion matrix (CSV), full report
  - Tags: dataset version, git commit (if available)
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Output of the training stage."""

    run_id: str
    accuracy: float
    macro_f1: float
    model_path: Path
    metrics: dict[str, Any]
    parameters: dict[str, Any]


def _get_git_commit() -> str | None:
    """Return the current git commit hash, or None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def train(
    train_path: str | Path,
    val_path: str | Path,
    output_dir: str | Path = "./models/classifier",
    experiment_name: str = "router-classifier",
    tracking_uri: str = "./mlruns",
    max_features: int = 10000,
    C: float = 1.0,
    ngram_range: tuple[int, int] = (1, 2),
) -> TrainingResult:
    """
    Train the TF-IDF + LogReg classifier and log the run to MLflow.

    Parameters
    ----------
    train_path / val_path:
        Parquet files produced by the preprocessing stage.
    output_dir:
        Where the trained model artifact will be saved.
    experiment_name:
        MLflow experiment to log under.
    tracking_uri:
        MLflow tracking server URI (default: local ./mlruns).
    max_features:
        TF-IDF vocabulary size limit.
    C:
        Logistic Regression regularisation strength.
    ngram_range:
        N-gram range for TF-IDF feature extraction.
    """
    try:
        import joblib
        import mlflow
        import mlflow.sklearn
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, classification_report, f1_score
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise RuntimeError(
            "mlflow, scikit-learn, pandas, and joblib are required for training. "
            "Install them with: pip install -r requirements.txt"
        ) from exc

    train_path = Path(train_path)
    val_path = Path(val_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ─────────────────────────────────────────────────────────────
    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)

    X_train, y_train = train_df["prompt"].tolist(), train_df["label"].tolist()
    X_val, y_val = val_df["prompt"].tolist(), val_df["label"].tolist()

    # ── Build pipeline ────────────────────────────────────────────────────────
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=max_features,
                    ngram_range=ngram_range,
                    strip_accents="unicode",
                    analyzer="word",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=C,
                    max_iter=1000,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )

    # ── MLflow tracking ───────────────────────────────────────────────────────
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    params: dict[str, Any] = {
        "max_features": max_features,
        "C": C,
        "ngram_range": list(ngram_range),
        "train_size": len(X_train),
        "val_size": len(X_val),
    }

    git_commit = _get_git_commit()

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        logger.info("MLflow run started: %s", run_id)

        # Log parameters
        mlflow.log_params(params)
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)
        mlflow.set_tag("stage", "training")
        mlflow.set_tag("model_type", "tfidf_logreg")

        # ── Train ─────────────────────────────────────────────────────────────
        logger.info("Fitting TF-IDF + LogReg pipeline...")
        pipeline.fit(X_train, y_train)

        # ── Evaluate on validation set ────────────────────────────────────────
        y_pred = pipeline.predict(X_val)
        accuracy = float(accuracy_score(y_val, y_pred))
        macro_f1 = float(f1_score(y_val, y_pred, average="macro"))

        report = classification_report(y_val, y_pred, output_dict=True)

        # Log scalar metrics
        mlflow.log_metric("val_accuracy", accuracy)
        mlflow.log_metric("val_macro_f1", macro_f1)
        for label_str, class_metrics in report.items():
            if isinstance(class_metrics, dict):
                safe_label = str(label_str).replace(" ", "_")
                for metric_name, value in class_metrics.items():
                    mlflow.log_metric(f"{safe_label}_{metric_name}", float(value))

        logger.info("Validation accuracy: %.4f | Macro F1: %.4f", accuracy, macro_f1)

        # ── Save model artifact ───────────────────────────────────────────────
        model_path = output_dir / "classifier.joblib"
        joblib.dump(pipeline, model_path)

        # Log model to MLflow
        mlflow.sklearn.log_model(pipeline, artifact_path="model")

        # Log classification report as JSON artifact
        report_path = output_dir / "classification_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        mlflow.log_artifact(str(report_path), artifact_path="reports")

        # Log params as artifact too (for reproducibility)
        params_path = output_dir / "run_params.json"
        with open(params_path, "w") as f:
            json.dump({"run_id": run_id, **params}, f, indent=2)
        mlflow.log_artifact(str(params_path), artifact_path="reports")

        logger.info("Model saved to %s | MLflow run: %s", model_path, run_id)

    return TrainingResult(
        run_id=run_id,
        accuracy=accuracy,
        macro_f1=macro_f1,
        model_path=model_path,
        metrics={"val_accuracy": accuracy, "val_macro_f1": macro_f1},
        parameters=params,
    )
