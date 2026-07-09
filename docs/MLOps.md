# MLOps Guide

## Overview

This project follows a modular MLOps lifecycle for the **Router Classifier** — the TF-IDF + Logistic Regression baseline model that backs the Tier-3 fallback classification system. The fine-tuned Llama SLM (Tier 1) is trained separately via the Jupyter notebook workflow.

---

## ML Pipeline

The pipeline is orchestrated via a Click CLI:

```
python -m ml.pipeline [COMMAND] [OPTIONS]
```

### Pipeline Stages

```
Raw CSV
   │
   ▼
Stage 1: Data Validation  (ml/stages/data_validation.py)
   │  - Schema check (prompt, category columns)
   │  - Null value detection
   │  - Class balance check (each class ≥ 5%)
   │  - Minimum rows: 100
   ▼
Stage 2: Preprocessing  (ml/stages/preprocessing.py)
   │  - Clean + strip prompts
   │  - Label encode categories → integers
   │  - Stratified train/val/test split (70/15/15)
   │  - Save to data/processed/*.parquet
   ▼
Stage 3: Training  (ml/stages/training.py)
   │  - TF-IDF (max_features=10000, ngram=(1,2))
   │  - Logistic Regression (multinomial, lbfgs)
   │  - Log params, metrics, artifacts → MLflow
   │  - Save model to models/classifier/classifier.joblib
   ▼
Stage 4: Model Registration  (ml/registry.py)
      - Add entry to models/registry.json
      - Stage: "staging"
      - Auto-promote if accuracy ≥ 0.80 (--auto-promote flag)
```

---

## Running the Pipeline

### Prerequisites

```bash
# Install all dependencies
pip install -r requirements.txt

# Generate the training dataset (if not present)
python scripts/generate_dataset.py
# → Creates: data/training_dataset.csv (2000 rows, 4 categories)
```

### Full Pipeline Run

```bash
python -m ml.pipeline run \
  --data-path ./data/training_dataset.csv \
  --version 1.0.0 \
  --auto-promote
```

### With Custom Hyperparameters

```bash
python -m ml.pipeline run \
  --data-path ./data/training_dataset.csv \
  --version 1.1.0 \
  --max-features 20000 \
  --C 0.5 \
  --auto-promote
```

### Skip Validation (if already validated)

```bash
python -m ml.pipeline run --skip-validation --version 1.0.1
```

---

## MLflow Experiment Tracking

MLflow tracks every training run automatically.

### View the MLflow UI

```bash
mlflow ui --backend-store-uri ./mlruns --port 5000
# Open: http://localhost:5000
```

### What Gets Tracked

| Category | Items |
|----------|-------|
| **Parameters** | max_features, C, ngram_range, train_size, val_size |
| **Metrics** | val_accuracy, val_macro_f1, per-class precision/recall/F1 |
| **Artifacts** | classifier.joblib, classification_report.json, run_params.json |
| **Tags** | git_commit, stage, model_type |

### Remote MLflow Server

To use a remote tracking server, set:

```env
MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
```

---

## Model Registry

The model registry (`models/registry.json`) tracks all trained versions.

### Commands

```bash
# List all registered versions
python -m ml.pipeline list-versions

# Promote a staging model to production
python -m ml.pipeline promote --version 1.0.0

# Roll back to a previous version
python -m ml.pipeline rollback --version 0.9.0
```

### Version Stages

| Stage | Description |
|-------|-------------|
| `staging` | Newly trained, not yet validated for production |
| `production` | Active production model (only one at a time) |
| `archived` | Previous production, retained for rollback |

### Example Registry Entry

```json
{
  "version": "1.0.0",
  "mlflow_run_id": "a3b4c5d6e7f8",
  "model_path": "models/classifier/classifier.joblib",
  "stage": "production",
  "metrics": {
    "accuracy": 0.9215,
    "macro_f1": 0.9187
  },
  "parameters": {
    "max_features": 10000,
    "C": 1.0,
    "ngram_range": [1, 2]
  },
  "git_commit": "abc1234",
  "registered_at": "2026-07-09T08:30:00+00:00",
  "promoted_at": "2026-07-09T08:35:00+00:00"
}
```

---

## Dataset Management

### Generate Synthetic Dataset

```bash
python scripts/generate_dataset.py
# → data/training_dataset.csv (2000 rows: 500 per category)
```

### Dataset Schema

| Column | Type | Description |
|--------|------|-------------|
| `prompt` | string | User input text |
| `category` | string | Label: math, coding, research, casual_chat |

### DVC Setup (Future)

To add DVC for dataset versioning:

```bash
pip install dvc
dvc init
dvc add data/training_dataset.csv

# Configure a remote (S3, GCS, Azure, etc.)
dvc remote add -d myremote s3://your-bucket/dvc-store
dvc push
```

---

## Model Performance Expectations

| Category | Expected Accuracy |
|----------|------------------|
| math | ≥ 0.90 |
| coding | ≥ 0.88 |
| research | ≥ 0.85 |
| casual_chat | ≥ 0.92 |
| **Overall (macro F1)** | **≥ 0.85** |

---

## Llama-3.2-1B Fine-Tuning (Tier 1 SLM)

The Tier-1 SLM is trained separately via the Jupyter notebook:

```
Multi_Model_Router_Llama3_QLoRA_Finetuning.ipynb/
```

After training:

```bash
# 1. Merge LoRA adapters into base model
python scripts/merge_lora.py

# 2. Build the Ollama model from Modelfile
ollama create llama3-router -f Modelfile

# 3. Verify
ollama run llama3-router "Solve for x: 2x + 6 = 20"
```

---

## Monitoring Model Health

Check the SQLite metrics database to detect routing drift:

```bash
# Check fallback rate (high fallback = Tier 1 SLM may be degrading)
sqlite3 data/metrics.db "SELECT
  task_type,
  COUNT(*) as total,
  SUM(fallback_model_used) as fallbacks,
  ROUND(AVG(latency_ms)) as avg_latency
FROM requests
GROUP BY task_type;"
```

A fallback rate > 20% suggests the Tier-1 SLM should be retrained.
