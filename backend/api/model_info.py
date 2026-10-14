"""
ReCare AI - Model Info & Governance API Router
Exposes active model architecture, calibration status, and clinical safety constraints.
"""

import os
import json
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/model", tags=["Model Information"])
METADATA_PATH = "backend/models/model_metadata.json"


@router.get("/info")
def get_model_information():
    """Retrieve metadata, versioning, feature inputs, and calibration metrics of the active model."""
    if not os.path.exists(METADATA_PATH):
        raise HTTPException(
            status_code=404,
            detail="Model metadata not found. Please train a model via `python -m backend.ml.train_model`.",
        )

    try:
        with open(METADATA_PATH, "r") as f:
            meta = json.load(f)

        meta["governance"] = {
            "intended_use": "Decision-support triage for post-discharge care coordination calls.",
            "target_population": "Adult inpatient discharges with chronic or acute medical conditions.",
            "disclaimer": "ReCare AI is a synthetic-data decision-support demonstration. It is not an autonomous diagnostic tool or clinical medical device.",
            "weekly_capacity_constraint": 50,
            "sensitive_attribute_policy": "Demographics are monitored strictly for fairness auditing and never used to deny care.",
        }
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model metadata: {str(e)}")
