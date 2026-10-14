"""
ReCare AI - Resource-Constrained Weekly Intervention Optimizer
The core differentiator: Optimizes patient selection for care-coordination outreach subject to a
strict capacity constraint of contacting at most 50 unique patients per week.

Implements two ranking modes:
- Mode A: Risk-First Baseline (calibrated readmission probability ranking)
- Mode B: Expected Intervention Benefit (P(readmission) - P(readmission | intervention))
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from backend.ml.predict import get_model_pipeline, get_risk_tier, generate_actionable_explanations
from backend.services.intervention_recommender import recommend_interventions_for_encounter
from backend.ml.preprocessing import EXCLUDED_FROM_FEATURES, deduplicate_encounters

logger = logging.getLogger(__name__)

MAX_WEEKLY_CAPACITY = 50


def estimate_intervention_effect(row: Dict[str, Any], raw_prob: float) -> Tuple[float, float, str]:
    """
    Estimate patient-specific relative risk reduction (RRR) and expected benefit:
    Expected Benefit = P(readmission) * Relative_Risk_Reduction * Actionability_Factor
    
    DISCLAIMER: This is an illustrative simulation model based on published literature ranges
    (e.g. Project RED, BOOST, Coleman CTT), not a clinically validated causal treatment-effect model.
    """
    base_rrr = 0.22  # baseline literature RRR for multifaceted post-discharge nurse call ~20-25%
    actionability_factor = 1.0
    rationale_notes = []

    # High medication burden responds well to pharmacist medication reconciliation
    med_count = row.get("medication_count", 0)
    if med_count is not None and not pd.isna(med_count) and int(med_count) >= 10:
        base_rrr += 0.08
        rationale_notes.append("High pharmacotherapy actionability via medication reconciliation (+8% RRR)")

    # Follow-up scheduling gap is highly addressable
    follow_up = row.get("follow_up_scheduled")
    if follow_up is False or str(follow_up).lower() == "false":
        base_rrr += 0.06
        rationale_notes.append("Addressable clinical scheduling gap (+6% RRR)")

    # Severe chronic conditions have established clinical protocols
    cond = str(row.get("condition_name", "")).lower()
    if "heart failure" in cond or "copd" in cond:
        base_rrr += 0.05
        rationale_notes.append("Established chronic disease self-management pathway (+5% RRR)")

    # Barriers: AMA or Hospice
    disp = str(row.get("discharge_disposition", "Home"))
    if disp == "Hospice":
        actionability_factor = 0.05
        rationale_notes.append("Palliative focus; standard readmission prevention avoided")
    elif disp == "Against Medical Advice (AMA)":
        actionability_factor = 0.50
        rationale_notes.append("Engagement barrier: high attrition rate in outpatient contact")

    final_rrr = min(0.45, base_rrr * actionability_factor)
    expected_benefit = raw_prob * final_rrr
    rationale_text = "; ".join(rationale_notes) if rationale_notes else "Standard care-coordination benefit profile"

    return round(float(final_rrr), 4), round(float(expected_benefit), 4), rationale_text


def optimize_weekly_call_list(
    encounters_df: pd.DataFrame,
    mode: str = "risk_first",  # 'risk_first' (Mode A) or 'expected_benefit' (Mode B)
    max_capacity: int = MAX_WEEKLY_CAPACITY,
    filter_planned_readmissions: bool = True,
) -> Dict[str, Any]:
    """
    Rank and select up to 50 unique patients for the weekly care coordination list.
    """
    logger.info(f"Running Weekly Call List Optimizer in Mode: '{mode}' (Capacity: {max_capacity})...")

    # Step 1: Remove exact encounter-level duplicates
    deduped_df, dups_removed = deduplicate_encounters(encounters_df)

    # Step 2: Apply policy for planned readmissions
    if filter_planned_readmissions and "is_planned_readmission" in deduped_df.columns:
        eligible_df = deduped_df[~deduped_df["is_planned_readmission"]].copy()
    else:
        eligible_df = deduped_df.copy()

    total_eligible = len(eligible_df)
    if total_eligible == 0:
        return {
            "call_list_id": f"CL-{datetime.now().strftime('%Y%W')}-{uuid.uuid4().hex[:6]}",
            "reporting_period": f"Week {datetime.now().isocalendar()[1]}, {datetime.now().year}",
            "generated_at": datetime.now().isoformat(),
            "ranking_mode": mode,
            "total_eligible_discharges": 0,
            "selected_count": 0,
            "remaining_capacity": max_capacity,
            "selected_patients": [],
            "summary": {"average_risk": 0.0, "total_expected_benefit": 0.0},
        }

    # Step 3: Run Calibrated Prediction Pipeline
    bundle = get_model_pipeline()
    preprocessor = bundle["preprocessor"]
    calibrated_model = bundle["calibrated_model"]

    feature_cols = [c for c in eligible_df.columns if c not in EXCLUDED_FROM_FEATURES]
    X_trans = preprocessor.transform(eligible_df[feature_cols])
    predicted_probs = calibrated_model.predict_proba(X_trans)[:, 1]
    eligible_df["predicted_risk"] = predicted_probs

    # Calculate expected benefit and recommendations for all eligible rows
    expected_benefits = []
    rrrs = []
    benefit_rationales = []
    recommendation_summaries = []

    for idx, row in eligible_df.iterrows():
        p = float(row["predicted_risk"])
        row_dict = row.to_dict()
        rrr, exp_benefit, rationale = estimate_intervention_effect(row_dict, p)
        rec = recommend_interventions_for_encounter(row_dict, p)

        rrrs.append(rrr)
        expected_benefits.append(exp_benefit)
        benefit_rationales.append(rationale)
        recommendation_summaries.append(rec)

    eligible_df["expected_benefit"] = expected_benefits
    eligible_df["relative_risk_reduction"] = rrrs
    eligible_df["benefit_rationale"] = benefit_rationales
    eligible_df["intervention_details"] = recommendation_summaries

    # Step 4: Patient Uniqueness Constraint
    # If a patient has multiple eligible discharge encounters in the period, keep their most recent discharge
    if "discharge_date" in eligible_df.columns:
        eligible_df = eligible_df.sort_values(by=["patient_id", "discharge_date"], ascending=[True, False])
    unique_patient_df = eligible_df.drop_duplicates(subset=["patient_id"], keep="first").copy()

    # Step 5: Rank According to Selected Mode
    if mode == "expected_benefit":
        # Mode B: Rank by expected avoided readmission probability
        ranked_df = unique_patient_df.sort_values(by=["expected_benefit", "predicted_risk"], ascending=[False, False])
    else:
        # Mode A: Risk-First Baseline
        ranked_df = unique_patient_df.sort_values(by=["predicted_risk", "expected_benefit"], ascending=[False, False])

    # Step 6: Select up to MAX capacity (strictly <= 50 unique patients)
    selected_df = ranked_df.head(max_capacity).copy()
    selected_count = len(selected_df)

    # Format selected patients for presentation
    selected_patients_list = []
    for rank, (orig_idx, row) in enumerate(selected_df.iterrows(), start=1):
        row_dict = row.to_dict()
        p = float(row["predicted_risk"])
        top_drivers, warnings = generate_actionable_explanations(row_dict, p)
        rec_details = row["intervention_details"]

        # Selection rationale explanation
        if mode == "expected_benefit":
            selection_reason = (
                f"Rank #{rank} based on high intervention benefit (Est. Benefit: {round(row['expected_benefit']*100, 1)}%, "
                f"Predicted Risk: {round(p*100, 1)}%). {row['benefit_rationale']}."
            )
        else:
            selection_reason = (
                f"Rank #{rank} based on high calibrated readmission probability ({round(p*100, 1)}%). "
                f"Prioritized for acute clinical surveillance."
            )

        selected_patients_list.append({
            "rank": rank,
            "encounter_id": str(row["encounter_id"]),
            "patient_id": str(row["patient_id"]),
            "age": int(row.get("age", 0)) if not pd.isna(row.get("age")) else None,
            "sex": str(row.get("sex", "Unknown")),
            "payer_type": str(row.get("payer_type", "Unknown")),
            "condition_name": str(row.get("condition_name", "Inpatient Care")),
            "primary_diagnosis_code": str(row.get("primary_diagnosis_code", "")).strip(),
            "discharge_date": str(row.get("discharge_date", "")),
            "discharge_disposition": str(row.get("discharge_disposition", "Home")),
            "predicted_risk_probability": round(p, 4),
            "risk_percentage": round(p * 100, 1),
            "risk_category": get_risk_tier(p),
            "expected_benefit": round(float(row["expected_benefit"]), 4),
            "expected_benefit_percentage": round(float(row["expected_benefit"]) * 100, 1),
            "recommended_intervention": rec_details["primary_recommendation"],
            "intervention_priority": rec_details["primary_priority"],
            "intervention_action_plan": rec_details["action_plan"],
            "all_applicable_recommendations": rec_details["all_applicable_recommendations"],
            "key_risk_drivers": top_drivers,
            "data_quality_warnings": warnings,
            "selection_rationale": selection_reason,
            "contact_status": "Pending",  # Initial clinical placeholder
            "follow_up_notes": "",         # Nurse note placeholder
        })

    # Summary Statistics
    avg_selected_risk = float(selected_df["predicted_risk"].mean()) if selected_count > 0 else 0.0
    total_benefit = float(selected_df["expected_benefit"].sum()) if selected_count > 0 else 0.0
    cohort_avg_risk = float(eligible_df["predicted_risk"].mean())

    call_list_payload = {
        "call_list_id": f"CL-W{datetime.now().isocalendar()[1]}-{uuid.uuid4().hex[:6].upper()}",
        "reporting_period": f"Week {datetime.now().isocalendar()[1]}, {datetime.now().year}",
        "generated_at": datetime.now().isoformat(),
        "ranking_mode": mode,
        "mode_description": (
            "Mode B: Ranked by Expected Intervention Benefit (P(readmission) * Intervention Impact)"
            if mode == "expected_benefit"
            else "Mode A: Ranked by Calibrated Readmission Risk Probability (Baseline)"
        ),
        "total_eligible_discharges": total_eligible,
        "unique_patients_eligible": len(unique_patient_df),
        "duplicate_encounters_filtered": dups_removed,
        "capacity_limit": max_capacity,
        "selected_count": selected_count,
        "remaining_capacity": max(0, max_capacity - selected_count),
        "summary": {
            "average_selected_risk": round(avg_selected_risk, 4),
            "cohort_average_risk": round(cohort_avg_risk, 4),
            "risk_enrichment_ratio": round(avg_selected_risk / max(0.01, cohort_avg_risk), 2),
            "estimated_readmissions_averted_illustrative": round(total_benefit, 2),
        },
        "selected_patients": selected_patients_list,
    }

    return call_list_payload
