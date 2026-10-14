"""
ReCare AI - Weekly Call List Optimization API Router
Exposes the core 50-patient resource-constrained optimizer and care-coordination call logging.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from backend.db.database import get_db
from backend.db.models import EncounterModel, CallListRunModel, CallListEntryModel
from backend.services.intervention_optimizer import optimize_weekly_call_list
from backend.schemas.pydantic_models import CallListGenerateRequest, CallListEntryUpdateSchema

router = APIRouter(prefix="/api/call-list", tags=["Weekly Call List"])


@router.get("/current")
def get_current_call_list(db: Session = Depends(get_db)):
    """Fetch the active weekly 50-patient call list."""
    run = db.query(CallListRunModel).order_by(CallListRunModel.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No active weekly call list found. Generate a call list first.")

    entries = (
        db.query(CallListEntryModel, EncounterModel)
        .join(EncounterModel, CallListEntryModel.encounter_id == EncounterModel.encounter_id)
        .filter(CallListEntryModel.call_list_run_id == run.id)
        .order_by(CallListEntryModel.rank.asc())
        .all()
    )

    patients_list = []
    for entry, enc in entries:
        patients_list.append({
            "entry_id": entry.id,
            "rank": entry.rank,
            "patient_id": entry.patient_id,
            "encounter_id": entry.encounter_id,
            "age": enc.age,
            "sex": enc.sex,
            "payer_type": enc.payer_type,
            "condition_name": enc.condition_name,
            "primary_diagnosis_code": enc.primary_diagnosis_code,
            "discharge_disposition": enc.discharge_disposition,
            "discharge_date": enc.discharge_date,
            "predicted_risk_probability": round(entry.predicted_risk_probability, 4),
            "risk_percentage": round(entry.predicted_risk_probability * 100, 1),
            "expected_benefit": round(entry.expected_benefit, 4) if entry.expected_benefit else 0.0,
            "expected_benefit_percentage": round((entry.expected_benefit or 0.0) * 100, 1),
            "recommended_intervention": entry.recommended_intervention,
            "intervention_priority": entry.intervention_priority,
            "intervention_action_plan": entry.intervention_action_plan,
            "contact_status": entry.contact_status,
            "follow_up_notes": entry.follow_up_notes or "",
            "selection_rationale": entry.selection_rationale,
        })

    return {
        "call_list_id": run.call_list_id,
        "reporting_period": run.reporting_period,
        "ranking_mode": run.ranking_mode,
        "mode_description": (
            "Mode B: Ranked by Expected Intervention Benefit"
            if run.ranking_mode == "expected_benefit"
            else "Mode A: Ranked by Calibrated Readmission Risk Probability (Baseline)"
        ),
        "capacity_limit": run.capacity_limit,
        "selected_count": run.selected_count,
        "remaining_capacity": max(0, run.capacity_limit - run.selected_count),
        "summary": run.summary_json or {},
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "selected_patients": patients_list,
    }


@router.post("/generate")
def generate_new_call_list(
    payload: CallListGenerateRequest,
    db: Session = Depends(get_db),
):
    """Run optimizer across recent discharges to select up to 50 unique patients."""
    # Query encounters
    encounters = db.query(EncounterModel).all()
    if not encounters:
        raise HTTPException(status_code=400, detail="No hospital encounter records found to optimize.")

    # Convert to DataFrame
    enc_dicts = []
    for e in encounters:
        enc_dicts.append({
            "encounter_id": e.encounter_id,
            "patient_id": e.patient_id,
            "age": e.age,
            "sex": e.sex,
            "payer_type": e.payer_type,
            "primary_diagnosis_code": e.primary_diagnosis_code,
            "condition_name": e.condition_name,
            "secondary_diagnoses_count": e.secondary_diagnoses_count,
            "length_of_stay": e.length_of_stay,
            "prior_admissions": e.prior_admissions,
            "prior_admissions_6m": e.prior_admissions_6m,
            "num_procedures": e.num_procedures,
            "discharge_disposition": e.discharge_disposition,
            "medication_count": e.medication_count,
            "hemoglobin": e.hemoglobin,
            "serum_creatinine": e.serum_creatinine,
            "sodium": e.sodium,
            "bun": e.bun,
            "glucose": e.glucose,
            "discharge_date": e.discharge_date,
            "follow_up_scheduled": e.follow_up_scheduled,
            "is_planned_readmission": e.is_planned_readmission,
            "readmitted_30d": e.readmitted_30d,
        })
    df = pd.DataFrame(enc_dicts)

    # Execute optimizer
    call_list = optimize_weekly_call_list(
        df,
        mode=payload.mode,
        max_capacity=min(payload.max_capacity, 50),
        filter_planned_readmissions=payload.filter_planned_readmissions,
    )

    # Persist run
    cl_run = CallListRunModel(
        call_list_id=call_list["call_list_id"],
        reporting_period=call_list["reporting_period"],
        ranking_mode=call_list["ranking_mode"],
        capacity_limit=call_list["capacity_limit"],
        selected_count=call_list["selected_count"],
        summary_json=call_list["summary"],
    )
    db.add(cl_run)
    db.commit()
    db.refresh(cl_run)

    entry_objs = []
    for p in call_list["selected_patients"]:
        entry_objs.append(
            CallListEntryModel(
                call_list_run_id=cl_run.id,
                rank=p["rank"],
                encounter_id=p["encounter_id"],
                patient_id=p["patient_id"],
                predicted_risk_probability=p["predicted_risk_probability"],
                expected_benefit=p["expected_benefit"],
                recommended_intervention=p["recommended_intervention"],
                intervention_priority=p["intervention_priority"],
                intervention_action_plan=p["intervention_action_plan"],
                contact_status="Pending",
                follow_up_notes="",
                selection_rationale=p["selection_rationale"],
            )
        )
    db.bulk_save_objects(entry_objs)
    db.commit()

    return call_list


@router.patch("/entries/{entry_id}")
def update_call_list_entry_status(
    entry_id: int,
    payload: CallListEntryUpdateSchema,
    db: Session = Depends(get_db),
):
    """Update contact status and clinical follow-up notes for a specific call list entry."""
    entry = db.query(CallListEntryModel).filter(CallListEntryModel.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Call list entry with ID {entry_id} not found.")

    if payload.contact_status is not None:
        entry.contact_status = payload.contact_status

    if payload.follow_up_notes is not None:
        entry.follow_up_notes = payload.follow_up_notes

    db.commit()
    return {
        "status": "success",
        "entry_id": entry.id,
        "contact_status": entry.contact_status,
        "follow_up_notes": entry.follow_up_notes,
    }
