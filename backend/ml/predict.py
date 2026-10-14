"""
ReCare AI - Inference & Actionable Patient-Level Explanation Engine
Provides calibrated 30-day readmission risk predictions, clinician-friendly
feature contributions, actionable care-coordination drivers, and data-quality warnings.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import joblib

from backend.ml.preprocessing import (
    normalize_diagnosis_code,
    EXCLUDED_FROM_FEATURES,
    LAB_FEATURES,
    CONDITION_MAP,
)

logger = logging.getLogger(__name__)

# Global model cache to avoid reloading pipeline on every API request
_CACHED_PIPELINE = None
_CACHED_METADATA = None
MODEL_PATH = "backend/models/recare_readmission_model.joblib"
METADATA_PATH = "backend/models/model_metadata.json"


def get_model_pipeline():
    """Load model pipeline from disk once and cache in memory."""
    global _CACHED_PIPELINE
    if _CACHED_PIPELINE is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Trained model artifact not found at {MODEL_PATH}. "
                "Please run `python -m backend.ml.train_model` before generating predictions."
            )
        logger.info(f"Loading ReCare readmission model from {MODEL_PATH}...")
        _CACHED_PIPELINE = joblib.load(MODEL_PATH)
    return _CACHED_PIPELINE


def get_risk_tier(prob: float) -> str:
    """Categorize probability into standardized clinical operational tiers."""
    if prob < 0.15:
        return "Low Risk"
    elif prob < 0.30:
        return "Moderate Risk"
    else:
        return "High Risk"


def generate_actionable_explanations(
    row: Dict[str, Any],
    pred_prob: float,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Generate actionable, nurse-friendly explanations based on observed clinical features.
    Translates technical drivers into concrete transition-of-care suggestions without making
    unsubstantiated causal claims or prescribing drugs.
    """
    drivers = []
    data_warnings = []

    # 1. Prior Admissions in last 6 months (one of the strongest empirical risk factors)
    prior_6m = row.get("prior_admissions_6m", 0)
    if prior_6m is not None and not pd.isna(prior_6m) and int(prior_6m) >= 2:
        drivers.append({
            "feature": "prior_admissions_6m",
            "feature_label": "High Inpatient Utilization",
            "value": f"{int(prior_6m)} admissions in past 6 months",
            "impact": "Increases Risk Significantly",
            "direction": "positive",
            "actionable_suggestion": "Review history of recurrent exacerbations; assess patient's primary care continuity and social support barriers.",
        })
    elif prior_6m is not None and int(prior_6m) == 1:
        drivers.append({
            "feature": "prior_admissions_6m",
            "feature_label": "Recent Inpatient Admission",
            "value": "1 admission in past 6 months",
            "impact": "Increases Risk Moderately",
            "direction": "positive",
            "actionable_suggestion": "Verify post-discharge care plan addresses chronic disease stabilization.",
        })

    # 2. Medication count / Polypharmacy
    meds = row.get("medication_count")
    if meds is not None and not pd.isna(meds):
        med_cnt = int(meds)
        if med_cnt >= 12:
            drivers.append({
                "feature": "medication_count",
                "feature_label": "Elevated Medication Burden (Polypharmacy)",
                "value": f"{med_cnt} active discharge medications",
                "impact": "Increases Risk",
                "direction": "positive",
                "actionable_suggestion": "Suggest pharmacist medication-reconciliation call to verify adherence, identify interactions, and simplify regimen.",
            })
        elif med_cnt <= 4:
            drivers.append({
                "feature": "medication_count",
                "feature_label": "Low Medication Burden",
                "value": f"{med_cnt} discharge medications",
                "impact": "Lowers Risk",
                "direction": "negative",
                "actionable_suggestion": "Confirm essential chronic disease maintenance therapy was prescribed and understood.",
            })

    # 3. Length of stay
    los = row.get("length_of_stay")
    if los is not None and not pd.isna(los):
        los_val = int(los)
        if los_val >= 8:
            drivers.append({
                "feature": "length_of_stay",
                "feature_label": "Prolonged Inpatient Stay",
                "value": f"{los_val} days",
                "impact": "Increases Risk",
                "direction": "positive",
                "actionable_suggestion": "Higher functional deconditioning risk; review physical therapy, occupational therapy, and DME needs.",
            })

    # 4. Discharge disposition
    disp = str(row.get("discharge_disposition", "Home"))
    if disp in ["Skilled Nursing Facility (SNF)", "Inpatient Rehabilitation"]:
        drivers.append({
            "feature": "discharge_disposition",
            "feature_label": "Facility-to-Facility Hand-off",
            "value": disp,
            "impact": "Increases Risk",
            "direction": "positive",
            "actionable_suggestion": "Ensure warm hand-off with facility intake coordinator; confirm transfer of clinical summary and med list.",
        })
    elif disp == "Against Medical Advice (AMA)":
        drivers.append({
            "feature": "discharge_disposition",
            "feature_label": "Discharge Against Medical Advice",
            "value": disp,
            "impact": "Severe Risk Driver",
            "direction": "positive",
            "actionable_suggestion": "Urgent outpatient outreach recommended within 48-72 hours to re-engage patient with safe outpatient plan.",
        })
    elif disp == "Home Health Care":
        drivers.append({
            "feature": "discharge_disposition",
            "feature_label": "Home Health Transition",
            "value": disp,
            "impact": "Moderate Transition Need",
            "direction": "positive",
            "actionable_suggestion": "Verify home health agency intake appointment is scheduled within 48 hours of discharge.",
        })

    # 5. Laboratory abnormalities & missingness
    for lab in LAB_FEATURES:
        val = row.get(lab)
        if val is None or pd.isna(val):
            data_warnings.append(f"Laboratory {lab.replace('_', ' ').title()} was missing from the encounter record.")
            drivers.append({
                "feature": f"{lab}_is_missing",
                "feature_label": f"Missing Lab: {lab.replace('_', ' ').title()}",
                "value": "Not Documented",
                "impact": "Informative Missingness",
                "direction": "neutral",
                "actionable_suggestion": f"Check whether recent outpatient {lab.replace('_', ' ')} results exist or if outpatient re-testing is warranted.",
            })
        else:
            # Check clinical thresholds
            val_num = float(val)
            if lab == "serum_creatinine" and val_num >= 1.8:
                drivers.append({
                    "feature": "serum_creatinine",
                    "feature_label": "Elevated Serum Creatinine",
                    "value": f"{val_num:.2f} mg/dL (Baseline normal: 0.6-1.2)",
                    "impact": "Increases Risk",
                    "direction": "positive",
                    "actionable_suggestion": "Renal monitoring indicated; schedule outpatient BMP within 7-10 days and verify hydration status.",
                })
            elif lab == "sodium" and val_num < 132.0:
                drivers.append({
                    "feature": "sodium",
                    "feature_label": "Hyponatremia",
                    "value": f"{val_num:.1f} mEq/L (Normal: 135-145)",
                    "impact": "Increases Risk",
                    "direction": "positive",
                    "actionable_suggestion": "Electrolyte disturbance noted; review diuretic dosing and schedule follow-up lab check.",
                })
            elif lab == "hemoglobin" and val_num < 9.5:
                drivers.append({
                    "feature": "hemoglobin",
                    "feature_label": "Anemia",
                    "value": f"{val_num:.1f} g/dL (Normal: 12.0-16.5)",
                    "impact": "Increases Risk",
                    "direction": "positive",
                    "actionable_suggestion": "Assess symptoms of fatigue or dizziness; confirm iron supplementation or outpatient hematology review if needed.",
                })

    # 6. Follow-up appointment scheduling
    follow_up = row.get("follow_up_scheduled")
    if follow_up is False or str(follow_up).lower() == "false":
        drivers.append({
            "feature": "follow_up_scheduled",
            "feature_label": "No Documented Follow-up Appointment",
            "value": "Unscheduled at discharge",
            "impact": "Increases Risk",
            "direction": "positive",
            "actionable_suggestion": "Immediate call to schedule 7-day post-discharge primary care or specialist follow-up.",
        })
    elif follow_up is True or str(follow_up).lower() == "true":
        drivers.append({
            "feature": "follow_up_scheduled",
            "feature_label": "Follow-up Appointment Confirmed",
            "value": "Scheduled before discharge",
            "impact": "Protective Factor",
            "direction": "negative",
            "actionable_suggestion": "Verify patient has transportation and understands appointment date/time.",
        })

    # 7. Primary condition context
    code = row.get("primary_diagnosis_code")
    norm_code = normalize_diagnosis_code(code)
    condition = CONDITION_MAP.get(norm_code, row.get("condition_name", "Clinical Inpatient Admission"))
    if norm_code in ["I50.9", "J44.1", "A41.9"]:
        drivers.append({
            "feature": "primary_condition",
            "feature_label": f"Primary Diagnosis: {condition}",
            "value": norm_code,
            "impact": "High-Risk Clinical Cohort",
            "direction": "positive",
            "actionable_suggestion": f"Initiate disease-specific protocol for {condition} (e.g. daily weights for HF, inhaler technique for COPD).",
        })

    # Sort drivers so positive risk factors appear first, limit to top 5
    drivers.sort(key=lambda d: 1 if d["direction"] == "positive" else 0, reverse=True)
    top_drivers = drivers[:5]

    return top_drivers, data_warnings


def predict_single_encounter(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate calibrated prediction and rich clinical explanation for a single encounter record.
    """
    bundle = get_model_pipeline()
    preprocessor = bundle["preprocessor"]
    calibrated_model = bundle["calibrated_model"]

    # Normalize single record into a 1-row DataFrame
    df_row = pd.DataFrame([record])
    feature_cols = [c for c in df_row.columns if c not in EXCLUDED_FROM_FEATURES]
    X_trans = preprocessor.transform(df_row[feature_cols])

    prob = float(calibrated_model.predict_proba(X_trans)[0, 1])
    prob_rounded = round(prob, 4)
    risk_tier = get_risk_tier(prob)

    top_drivers, warnings = generate_actionable_explanations(record, prob)

    return {
        "encounter_id": record.get("encounter_id", "UNKNOWN"),
        "patient_id": record.get("patient_id", "UNKNOWN"),
        "predicted_risk_probability": prob_rounded,
        "risk_percentage": round(prob_rounded * 100, 1),
        "risk_category": risk_tier,
        "model_version": "v1.2.0-calibrated-histgb",
        "top_contributing_features": top_drivers,
        "data_quality_warnings": warnings,
        "prediction_timestamp": datetime.now().isoformat(),
    }


def predict_batch_encounters(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch prediction endpoint with row-level validation tolerance.
    """
    bundle = get_model_pipeline()
    preprocessor = bundle["preprocessor"]
    calibrated_model = bundle["calibrated_model"]

    if not records:
        return []

    df_batch = pd.DataFrame(records)
    feature_cols = [c for c in df_batch.columns if c not in EXCLUDED_FROM_FEATURES]

    # Transform batch
    X_trans = preprocessor.transform(df_batch[feature_cols])
    probs = calibrated_model.predict_proba(X_trans)[:, 1]

    results = []
    for idx, row in df_batch.iterrows():
        p = float(probs[idx])
        p_round = round(p, 4)
        rec_dict = row.to_dict()
        top_drivers, warnings = generate_actionable_explanations(rec_dict, p)

        results.append({
            "encounter_id": rec_dict.get("encounter_id", f"ENC-{idx}"),
            "patient_id": rec_dict.get("patient_id", f"PT-{idx}"),
            "predicted_risk_probability": p_round,
            "risk_percentage": round(p_round * 100, 1),
            "risk_category": get_risk_tier(p),
            "model_version": "v1.2.0-calibrated-histgb",
            "top_contributing_features": top_drivers,
            "data_quality_warnings": warnings,
            "prediction_timestamp": datetime.now().isoformat(),
        })

    return results
