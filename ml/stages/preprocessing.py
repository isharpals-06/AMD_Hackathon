"""
Stage 2: Preprocessing

Loads the validated CSV, applies cleaning, encodes labels, and splits
the dataset into train/validation/test sets.

Outputs are saved to `data/processed/` as parquet files for efficient
downstream loading.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CATEGORY_TO_ID: dict[str, int] = {
    "math": 0,
    "coding": 1,
    "research": 2,
    "casual_chat": 3,
}
ID_TO_CATEGORY: dict[int, str] = {v: k for k, v in CATEGORY_TO_ID.items()}


@dataclass
class PreprocessingResult:
    """Paths to the saved processed split files."""

    train_path: Path
    val_path: Path
    test_path: Path
    train_size: int
    val_size: int
    test_size: int
    label_map: dict[str, int]


def preprocess(
    data_path: str | Path,
    output_dir: str | Path = "./data/processed",
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_seed: int = 42,
) -> PreprocessingResult:
    """
    Clean, encode, and split the dataset.

    Parameters
    ----------
    data_path:
        Path to the validated raw CSV.
    output_dir:
        Directory where processed parquet files will be saved.
    test_size:
        Fraction of data reserved for the test set.
    val_size:
        Fraction of data (from remainder) reserved for validation.
    random_seed:
        RNG seed for reproducibility.

    Returns
    -------
    PreprocessingResult
        Paths and sizes of the three produced splits.
    """
    try:
        import pandas as pd
        from sklearn.model_selection import train_test_split
    except ImportError as exc:
        raise RuntimeError(
            "pandas and scikit-learn are required for preprocessing."
        ) from exc

    data_path = Path(data_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading dataset from %s", data_path)
    df = pd.read_csv(data_path)
    df.columns = df.columns.str.lower()

    # ── Cleaning ──────────────────────────────────────────────────────────────
    initial_rows = len(df)
    df = df.dropna(subset=["prompt", "category"])
    df["prompt"] = df["prompt"].str.strip()
    df = df[df["prompt"].str.len() >= 5]
    df = df[df["category"].isin(CATEGORY_TO_ID.keys())]
    logger.info("Cleaned dataset: %d → %d rows", initial_rows, len(df))

    # ── Label encoding ────────────────────────────────────────────────────────
    df["label"] = df["category"].map(CATEGORY_TO_ID)

    # ── Split ─────────────────────────────────────────────────────────────────
    train_df, temp_df = train_test_split(
        df,
        test_size=test_size + val_size,
        random_state=random_seed,
        stratify=df["label"],
    )
    relative_val = val_size / (test_size + val_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=1.0 - relative_val,
        random_state=random_seed,
        stratify=temp_df["label"],
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    train_path = output_dir / "train.parquet"
    val_path = output_dir / "val.parquet"
    test_path = output_dir / "test.parquet"

    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)

    logger.info(
        "Preprocessing complete: train=%d, val=%d, test=%d",
        len(train_df),
        len(val_df),
        len(test_df),
    )

    return PreprocessingResult(
        train_path=train_path,
        val_path=val_path,
        test_path=test_path,
        train_size=len(train_df),
        val_size=len(val_df),
        test_size=len(test_df),
        label_map=CATEGORY_TO_ID,
    )
