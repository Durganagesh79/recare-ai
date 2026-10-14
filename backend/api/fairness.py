"""
ReCare AI - Fairness & Bias Audit API Router
Returns subgroup performance across Age groups, Sex, and Payer type,
with calibration equity, selection rates, and practical mitigation strategies.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from backend.ml.fairness_audit import run_fairness_audit

router = APIRouter(prefix="/api/fairness", tags=["Fairness & Bias"])
FAIRNESS_REPORT_PATH = "data/reports/fairness_audit_report.json"


@router.get("/report")
def get_fairness_audit_report():
    """Retrieve comprehensive algorithmic fairness and disparate impact audit results."""
    if os.path.exists(FAIRNESS_REPORT_PATH):
        try:
            with open(FAIRNESS_REPORT_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass

    try:
        report = run_fairness_audit()
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load or run fairness audit: {str(e)}",
        )
