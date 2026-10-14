"""
ReCare AI - Rules-Based Intervention Recommender
Maps observed clinical features, discharge dispositions, and medication burdens to
transparent, human-reviewable care-coordination intervention categories.
"""

from typing import Dict, Any, List
import pandas as pd


INTERVENTION_CATEGORIES = [
    "Pharmacist Medication Reconciliation",
    "Post-Discharge Follow-up Appointment Scheduling",
    "Nurse Transition-of-Care Call",
    "Specialist Disease-Management Review",
    "Home Health & Community Transition Support",
    "Care Coordination & Social Determinants (SDOH) Outreach",
]


def recommend_interventions_for_encounter(
    row: Dict[str, Any],
    pred_prob: float,
) -> Dict[str, Any]:
    """
    Generate tailored, rules-based care-coordination interventions for a patient encounter.
    Each recommendation is documented with supporting features and verification notes.
    """
    recommendations = []
    
    # 1. Medication Burden Rule -> Pharmacist Medication Reconciliation
    med_count = row.get("medication_count")
    if med_count is not None and not pd.isna(med_count) and int(med_count) >= 10:
        recommendations.append({
            "category": "Pharmacist Medication Reconciliation",
            "priority": "High" if int(med_count) >= 14 else "Medium",
            "supporting_features": [f"Medication count: {int(med_count)} active discharge prescriptions"],
            "rationale": "High prescription burden increases risk of drug-drug interactions, non-adherence, and dosing discrepancies during care handoff.",
            "rule_status": "Polypharmacy Rule (Threshold >= 10 meds)",
            "verification_needed": "Verify if updated discharge medication list matches patient's home pharmacy and prior outpatient regimen.",
            "action_plan": "Schedule dedicated 15-minute pharmacist review call within 48-72 hours of discharge.",
        })

    # 2. Unscheduled Follow-up Rule -> Appointment Scheduling
    follow_up = row.get("follow_up_scheduled")
    if follow_up is False or str(follow_up).lower() == "false" or pd.isna(follow_up):
        recommendations.append({
            "category": "Post-Discharge Follow-up Appointment Scheduling",
            "priority": "High",
            "supporting_features": ["Follow-up appointment status: Not scheduled or missing at discharge"],
            "rationale": "Unscheduled follow-up within 7-14 days is a proven risk factor for acute readmission exacerbation.",
            "rule_status": "Follow-Up Gap Rule",
            "verification_needed": "Verify patient primary care physician (PCP) contact information and insurance network participation.",
            "action_plan": "Outreach coordinator assists patient in booking appointment within 7 days of discharge.",
        })

    # 3. High Prior Inpatient Admissions -> Nurse Transition-of-Care Call
    prior_6m = row.get("prior_admissions_6m", 0)
    if prior_6m is not None and not pd.isna(prior_6m) and int(prior_6m) >= 1:
        recommendations.append({
            "category": "Nurse Transition-of-Care Call",
            "priority": "High" if int(prior_6m) >= 2 else "Medium",
            "supporting_features": [f"Prior admissions in 6 months: {int(prior_6m)}"],
            "rationale": "History of recurrent acute utilization indicates fragile chronic illness management requiring active nursing surveillance.",
            "rule_status": "Recurrent Utilization Rule",
            "verification_needed": "Assess caregiver support availability and patient understanding of red-flag symptom escalations.",
            "action_plan": "Conduct structured 48-hour post-discharge transition assessment using standard Coleman Care Transitions protocol.",
        })

    # 4. Complex Discharge Disposition -> Home Health & Community Transition Support
    disp = str(row.get("discharge_disposition", "Home"))
    if disp in ["Home Health Care", "Skilled Nursing Facility (SNF)", "Inpatient Rehabilitation"]:
        recommendations.append({
            "category": "Home Health & Community Transition Support",
            "priority": "Medium",
            "supporting_features": [f"Discharge disposition: {disp}"],
            "rationale": "Post-acute facility or home agency transitions frequently suffer from information drop-off between hospital and receiving teams.",
            "rule_status": "Care Transition Hand-Off Rule",
            "verification_needed": "Confirm intake nurse arrival date, equipment delivery (oxygen, walker, wound care), and transmission of continuity summary.",
            "action_plan": "Contact receiving agency coordinator to confirm first clinical contact within 48 hours.",
        })
    elif disp == "Against Medical Advice (AMA)":
        recommendations.append({
            "category": "Care Coordination & Social Determinants (SDOH) Outreach",
            "priority": "Urgent",
            "supporting_features": ["Discharge disposition: Against Medical Advice (AMA)"],
            "rationale": "AMA discharges experience higher readmission and mortality rates due to incomplete acute treatment courses.",
            "rule_status": "AMA High-Risk Protocol",
            "verification_needed": "Identify root cause of early departure (e.g. child care, work obligations, pain management, mistrust) without punitive judgment.",
            "action_plan": "Empathetic outreach within 24-48 hours offering non-judgmental assistance with outpatient medication pickup and clinic re-engagement.",
        })

    # 5. Specialized Chronic Conditions -> Specialist Disease-Management Review
    diag_code = str(row.get("primary_diagnosis_code", ""))
    cond_name = str(row.get("condition_name", ""))
    if any(k in diag_code.upper() or k in cond_name.lower() for k in ["I50", "heart failure", "428"]):
        recommendations.append({
            "category": "Specialist Disease-Management Review",
            "priority": "High",
            "supporting_features": ["Primary condition: Heart Failure (HF)"],
            "rationale": "HF patients benefit significantly from daily weight monitoring protocols, low-sodium guidance, and prompt diuretic titration.",
            "rule_status": "Heart Failure Care Pathway",
            "verification_needed": "Ensure patient has a working bathroom scale and understands the '2-3 lbs overnight / 5 lbs in a week' weight gain rule.",
            "action_plan": "Cardiology clinic follow-up scheduled; deliver HF self-management disease-education kit.",
        })
    elif any(k in diag_code.upper() or k in cond_name.lower() for k in ["J44", "copd", "496"]):
        recommendations.append({
            "category": "Specialist Disease-Management Review",
            "priority": "Medium",
            "supporting_features": ["Primary condition: COPD"],
            "rationale": "COPD patients require verified inhaler technique, smoking cessation support, and a written exacerbation action plan.",
            "rule_status": "COPD Pathway",
            "verification_needed": "Verify patient has active inhalers and spacer device at home.",
            "action_plan": "Pulmonology or respiratory therapist outreach within 5 days.",
        })

    # If no specific rule triggered, provide primary nurse care-coordination baseline
    if not recommendations:
        recommendations.append({
            "category": "Nurse Transition-of-Care Call",
            "priority": "Standard",
            "supporting_features": [f"Predicted 30-day readmission risk: {round(pred_prob*100, 1)}%"],
            "rationale": "Routine general transition follow-up to answer post-discharge questions and verify general wellness.",
            "rule_status": "Standard Follow-Up Protocol",
            "verification_needed": "Check general recovery trajectory and prescription filling.",
            "action_plan": "Standard post-discharge phone call within 5-7 business days.",
        })

    # Select primary recommendation based on highest priority
    priority_weights = {"Urgent": 4, "High": 3, "Medium": 2, "Standard": 1}
    recommendations.sort(key=lambda r: priority_weights.get(r["priority"], 0), reverse=True)
    primary_rec = recommendations[0]

    return {
        "primary_recommendation": primary_rec["category"],
        "primary_priority": primary_rec["priority"],
        "primary_rationale": primary_rec["rationale"],
        "action_plan": primary_rec["action_plan"],
        "all_applicable_recommendations": recommendations,
        "human_review_status": "Pending Clinical Review",
        "clinician_override_allowed": True,
    }
