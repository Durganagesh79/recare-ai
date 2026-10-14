"""
ReCare AI - Dataset Management & Data Quality API Router
Provides schema validation, dataset preview, quality diagnostics, CSV uploads,
and explicit controls for generating synthetic datasets and triggering model training.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.init_db import initialize_and_seed_database
from backend.ml.generate_dataset import generate_synthetic_discharge_dataset
from backend.ml.train_model import train_readmission_models
from backend.ml.evaluate import evaluate_model_on_test_set
from backend.ml.fairness_audit import run_fairness_audit
from backend.ml.preprocessing import deduplicate_encounters, normalize_diagnosis_code

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/datasets", tags=["Datasets & Data Quality"])

QUALITY_REPORT_PATH = "data/processed/data_quality_report.json"
DATA_DICTIONARY_PATH = "data/processed/data_dictionary.json"


@router.get("/quality")
def get_data_quality_report():
    """Retrieve comprehensive data-quality summary report and clinical data dictionary."""
    report = {}
    dictionary = {}

    if os.path.exists(QUALITY_REPORT_PATH):
        try:
            with open(QUALITY_REPORT_PATH, "r") as f:
                report = json.load(f)
        except Exception:
            pass

    if os.path.exists(DATA_DICTIONARY_PATH):
        try:
            with open(DATA_DICTIONARY_PATH, "r") as f:
                dictionary = json.load(f)
        except Exception:
            pass

    return {
        "status": "success",
        "quality_report": report,
        "data_dictionary": dictionary,
    }


@router.post("/upload")
async def upload_and_validate_dataset(file: UploadFile = File(...)):
    """
    Upload and validate hospital discharge dataset CSV.
    Checks schema, missing values, duplicates, and returns structured validation report.
    Does NOT automatically retrain model.
    """
    # Enforce file format and reasonable size bounds (< 50MB)
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are accepted.")

    try:
        contents = await file.read()
        if len(contents) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds maximum 50MB limit.")

        import io
        df_upload = pd.read_csv(io.BytesIO(contents))
        total_rows = len(df_upload)

        # Expected core clinical columns
        expected_cols = [
            "encounter_id", "patient_id", "age", "sex", "payer_type",
            "primary_diagnosis_code", "length_of_stay", "medication_count"
        ]
        missing_cols = [col for col in expected_cols if col not in df_upload.columns]
        
        # Deduplication check
        deduped_df, dups_count = deduplicate_encounters(df_upload)

        # Missingness summary
        missing_counts = {
            col: int(df_upload[col].isna().sum())
            for col in df_upload.columns
            if df_upload[col].isna().sum() > 0
        }

        # Check if labeled target exists
        is_labeled = "readmitted_30d" in df_upload.columns

        # Sample preview (top 5 rows sanitized)
        preview_rows = df_upload.head(5).fillna("").to_dict(orient="records")

        # Save to raw uploads
        os.makedirs("data/raw", exist_ok=True)
        save_path = os.path.join("data/raw", f"upload_{file.filename}")
        with open(save_path, "wb") as f:
            f.write(contents)

        return {
            "status": "validated" if not missing_cols else "warning",
            "filename": file.filename,
            "total_records": total_rows,
            "unique_encounters": len(deduped_df),
            "duplicate_encounters_detected": dups_count,
            "missing_required_columns": missing_cols,
            "missing_values_by_column": missing_counts,
            "dataset_type": "Historical Labeled (Training Eligible)" if is_labeled else "Unlabeled Future Discharges (Inference Only)",
            "can_train_model": is_labeled and not missing_cols,
            "can_run_inference": not missing_cols,
            "preview": preview_rows,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


@router.post("/generate")
def trigger_generate_synthetic_dataset(records: int = 25000, seed: int = 42):
    """Regenerate synthetic hospital discharge dataset with deliberate imperfections."""
    try:
        df, report = generate_synthetic_discharge_dataset(num_records=records, random_seed=seed)
        return {
            "status": "success",
            "message": f"Successfully generated {len(df)} synthetic discharge records.",
            "report": report,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dataset: {str(e)}")


@router.post("/train")
def trigger_model_training(seed: int = 42):
    """Explicitly trigger model training and calibration pipeline."""
    try:
        meta = train_readmission_models(random_seed=seed)
        # Automatically update evaluation and fairness reports
        evaluate_model_on_test_set()
        run_fairness_audit()
        return {
            "status": "success",
            "message": "Model training, calibration, evaluation, and fairness audit successfully completed.",
            "model_metadata": meta,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")
