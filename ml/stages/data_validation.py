"""
Stage 1: Data Validation

Validates the raw training CSV before any preprocessing occurs.

Checks:
  - File exists and is readable
  - Required columns: 'prompt', 'category'
  - No null values in required columns
  - Category values are within the expected set
  - Dataset is large enough (min_rows threshold)
  - Class balance (no category should be under 10% of total)

Returns a DataValidationReport dataclass with pass/fail details.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

EXPECTED_CATEGORIES = {"math", "coding", "research", "casual_chat"}
REQUIRED_COLUMNS = {"prompt", "category"}
MIN_ROWS = 100
MIN_CLASS_FRACTION = 0.05  # each class must be >= 5% of dataset


@dataclass
class DataValidationReport:
    """Result of the data validation stage."""

    passed: bool = True
    total_rows: int = 0
    null_counts: dict[str, int] = field(default_factory=dict)
    category_distribution: dict[str, int] = field(default_factory=dict)
    unknown_categories: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate(data_path: str | Path, min_rows: int = MIN_ROWS) -> DataValidationReport:
    """
    Validate the training CSV at `data_path`.

    Parameters
    ----------
    data_path:
        Path to the raw CSV file (must have 'prompt' and 'category' columns).
    min_rows:
        Minimum acceptable number of rows.

    Returns
    -------
    DataValidationReport
        Detailed pass/fail report. ``report.passed`` is False if any hard error
        is found; warnings do not affect ``passed``.
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required for data validation. Install it with: pip install pandas"
        ) from exc

    report = DataValidationReport()
    data_path = Path(data_path)

    # ── Check file existence ──────────────────────────────────────────────────
    if not data_path.exists():
        report.errors.append(f"Data file not found: {data_path}")
        report.passed = False
        return report

    # ── Load CSV ──────────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(data_path)
    except Exception as exc:
        report.errors.append(f"Failed to read CSV: {exc}")
        report.passed = False
        return report

    report.total_rows = len(df)

    # ── Check required columns ────────────────────────────────────────────────
    missing_cols = REQUIRED_COLUMNS - set(df.columns.str.lower())
    if missing_cols:
        report.errors.append(f"Missing required columns: {missing_cols}")
        report.passed = False
        return report

    # Normalise column names to lowercase
    df.columns = df.columns.str.lower()

    # ── Check minimum rows ────────────────────────────────────────────────────
    if report.total_rows < min_rows:
        report.errors.append(f"Dataset too small: {report.total_rows} rows (minimum: {min_rows})")
        report.passed = False

    # ── Check nulls ───────────────────────────────────────────────────────────
    report.null_counts = df[list(REQUIRED_COLUMNS)].isnull().sum().to_dict()
    for col, count in report.null_counts.items():
        if count > 0:
            report.errors.append(f"Column '{col}' has {count} null values")
            report.passed = False

    # ── Category distribution ─────────────────────────────────────────────────
    report.category_distribution = df["category"].value_counts().to_dict()
    unknown = set(df["category"].dropna().unique()) - EXPECTED_CATEGORIES
    if unknown:
        report.unknown_categories = list(unknown)
        report.warnings.append(f"Unexpected categories found: {unknown}")

    # ── Class balance check ───────────────────────────────────────────────────
    for cat, count in report.category_distribution.items():
        fraction = count / report.total_rows if report.total_rows > 0 else 0
        if fraction < MIN_CLASS_FRACTION:
            report.warnings.append(
                f"Category '{cat}' has only {fraction:.1%} of samples (threshold: {MIN_CLASS_FRACTION:.0%})"
            )

    # ── Summary ───────────────────────────────────────────────────────────────
    if report.passed:
        logger.info(
            "Data validation PASSED — %d rows, categories: %s",
            report.total_rows,
            report.category_distribution,
        )
    else:
        logger.error("Data validation FAILED — errors: %s", report.errors)

    for warning in report.warnings:
        logger.warning("Data validation warning: %s", warning)

    return report
