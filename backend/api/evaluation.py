"""
ReCare AI - Model Evaluation API Router
Returns official holdout test metrics: AUC-PR, Recall@50, Precision@50, ECE calibration error,
Brier score, reliability diagrams, and interactive precision-recall coordinates.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from backend.ml.evaluate import evaluate_model_on_test_set

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])
REPORT_PATH = "data/reports/evaluation_results.json"


@router.get("/metrics")
def get_evaluation_metrics():
    """Retrieve verified evaluation metrics computed on the independent holdout test set."""
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            pass

    # If report file not yet generated, compute dynamically
    try:
        results = evaluate_model_on_test_set()
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load or run evaluation metrics: {str(e)}. Ensure test split and model exist.",
        )
