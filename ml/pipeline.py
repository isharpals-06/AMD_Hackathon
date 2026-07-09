"""
ML Pipeline CLI Orchestrator

Chains all pipeline stages: validate → preprocess → train → register.

Usage:
    python -m ml.pipeline run
    python -m ml.pipeline run --data-path ./data/training_dataset.csv
    python -m ml.pipeline run --skip-validation
    python -m ml.pipeline list-versions
    python -m ml.pipeline promote --version 1.0.0
    python -m ml.pipeline rollback --version 0.9.0
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from ml.registry import list_versions, promote_to_production, rollback
from ml.stages import data_validation, preprocessing, training

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ml.pipeline")

DEFAULT_DATA_PATH = "./data/training_dataset.csv"
DEFAULT_PROCESSED_DIR = "./data/processed"
DEFAULT_MODEL_DIR = "./models/classifier"
DEFAULT_VERSION = "1.0.0"


@click.group()
def cli():
    """AMD Multi-Model Router — ML Pipeline CLI."""
    pass


@cli.command()
@click.option(
    "--data-path",
    default=DEFAULT_DATA_PATH,
    show_default=True,
    help="Path to raw training CSV (prompt, category columns required).",
)
@click.option(
    "--processed-dir",
    default=DEFAULT_PROCESSED_DIR,
    show_default=True,
    help="Output directory for preprocessed parquet splits.",
)
@click.option(
    "--model-dir",
    default=DEFAULT_MODEL_DIR,
    show_default=True,
    help="Output directory for trained model artifacts.",
)
@click.option(
    "--version",
    default=DEFAULT_VERSION,
    show_default=True,
    help="Model version string (semver) to register.",
)
@click.option(
    "--max-features",
    default=10000,
    show_default=True,
    help="TF-IDF vocabulary size.",
)
@click.option("--C", "reg_C", default=1.0, show_default=True, help="Logistic Regression C.")
@click.option(
    "--skip-validation",
    is_flag=True,
    default=False,
    help="Skip the data validation stage.",
)
@click.option(
    "--auto-promote",
    is_flag=True,
    default=False,
    help="Automatically promote the new version to production if accuracy > 0.80.",
)
@click.option(
    "--mlflow-uri",
    default="./mlruns",
    show_default=True,
    help="MLflow tracking URI.",
)
@click.option(
    "--experiment",
    default="router-classifier",
    show_default=True,
    help="MLflow experiment name.",
)
def run(
    data_path: str,
    processed_dir: str,
    model_dir: str,
    version: str,
    max_features: int,
    reg_c: float,
    skip_validation: bool,
    auto_promote: bool,
    mlflow_uri: str,
    experiment: str,
):
    """Run the full ML pipeline: validate → preprocess → train → register."""
    click.echo(click.style("\n🚀 AMD Router ML Pipeline", fg="cyan", bold=True))
    click.echo(f"   Data:    {data_path}")
    click.echo(f"   Version: {version}")
    click.echo(f"   MLflow:  {mlflow_uri}\n")

    # ── Stage 1: Data Validation ──────────────────────────────────────────────
    if not skip_validation:
        click.echo(click.style("── Stage 1/4: Data Validation", bold=True))
        report = data_validation.validate(data_path)
        if not report.passed:
            click.echo(click.style("✗ Data validation FAILED:", fg="red"))
            for err in report.errors:
                click.echo(f"  • {err}")
            sys.exit(1)
        click.echo(click.style(f"✓ Validation passed ({report.total_rows} rows)\n", fg="green"))
    else:
        click.echo(click.style("── Stage 1/4: Data Validation [SKIPPED]\n", dim=True))

    # ── Stage 2: Preprocessing ────────────────────────────────────────────────
    click.echo(click.style("── Stage 2/4: Preprocessing", bold=True))
    prep_result = preprocessing.preprocess(
        data_path=data_path,
        output_dir=processed_dir,
    )
    click.echo(
        click.style(
            f"✓ Splits: train={prep_result.train_size}, "
            f"val={prep_result.val_size}, test={prep_result.test_size}\n",
            fg="green",
        )
    )

    # ── Stage 3: Training ─────────────────────────────────────────────────────
    click.echo(click.style("── Stage 3/4: Training (with MLflow)", bold=True))
    train_result = training.train(
        train_path=prep_result.train_path,
        val_path=prep_result.val_path,
        output_dir=model_dir,
        experiment_name=experiment,
        tracking_uri=mlflow_uri,
        max_features=max_features,
        C=reg_c,
    )
    click.echo(
        click.style(
            f"✓ Training complete — accuracy={train_result.accuracy:.4f}, "
            f"macro_f1={train_result.macro_f1:.4f}\n",
            fg="green",
        )
    )

    # ── Stage 4: Register ─────────────────────────────────────────────────────
    click.echo(click.style("── Stage 4/4: Model Registration", bold=True))
    from ml.registry import register_model

    register_model(
        version=version,
        mlflow_run_id=train_result.run_id,
        model_path=train_result.model_path,
        accuracy=train_result.accuracy,
        macro_f1=train_result.macro_f1,
        parameters=train_result.parameters,
    )
    click.echo(click.style(f"✓ Registered version {version} (stage=staging)\n", fg="green"))

    # ── Auto-promote ──────────────────────────────────────────────────────────
    if auto_promote:
        threshold = 0.80
        if train_result.accuracy >= threshold:
            promote_to_production(version)
            click.echo(
                click.style(
                    f"🎉 Auto-promoted version {version} to production "
                    f"(accuracy {train_result.accuracy:.4f} ≥ {threshold})",
                    fg="cyan",
                    bold=True,
                )
            )
        else:
            click.echo(
                click.style(
                    f"⚠ Auto-promote skipped: accuracy {train_result.accuracy:.4f} < {threshold}",
                    fg="yellow",
                )
            )

    click.echo(click.style("\n✅ Pipeline complete!\n", fg="green", bold=True))


@cli.command(name="list-versions")
def list_versions_cmd():
    """List all registered model versions."""
    versions = list_versions()
    if not versions:
        click.echo("No models registered yet. Run: python -m ml.pipeline run")
        return
    click.echo(f"\n{'Version':<12} {'Stage':<12} {'Accuracy':<10} {'F1':<10} {'Run ID'}")
    click.echo("─" * 70)
    for v in versions:
        metrics = v.get("metrics", {})
        click.echo(
            f"{v['version']:<12} {v['stage']:<12} "
            f"{metrics.get('accuracy', 0):<10.4f} "
            f"{metrics.get('macro_f1', 0):<10.4f} "
            f"{v.get('mlflow_run_id', 'N/A')[:12]}"
        )
    click.echo()


@cli.command()
@click.option("--version", required=True, help="Model version to promote to production.")
def promote(version: str):
    """Promote a staging model version to production."""
    try:
        entry = promote_to_production(version)
        click.echo(click.style(f"✓ Promoted version {version} to production.", fg="green"))
        click.echo(f"  Model path: {entry['model_path']}")
    except ValueError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--version", required=True, help="Model version to roll back to.")
def rollback_cmd(version: str):
    """Roll back to a previous model version."""
    try:
        entry = rollback(version)
        click.echo(click.style(f"✓ Rolled back to version {version}.", fg="yellow"))
        click.echo(f"  Model path: {entry['model_path']}")
    except ValueError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    cli()
