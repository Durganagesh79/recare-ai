"""
ReCare AI - Patient Registry & Individual Patient Detail API Router
Provides multi-criteria search, risk filtering, and full patient-level clinical drill-downs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from backend.db.database import get_db
from backend.db.models import PatientModel, EncounterModel, PredictionModel
from backend.services.intervention_recommender import recommend_interventions_for_encounter

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("")
def list_patients(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by Patient ID, Encounter ID, or Condition"),
    risk_category: Optional[str] = Query(None, description="Low Risk, Moderate Risk, High Risk"),
    condition_name: Optional[str] = Query(None),
    discharge_disposition: Optional[str] = Query(None),
    payer_type: Optional[str] = Query(None),
    sort_by: str = Query("predicted_risk", description="predicted_risk, discharge_date, encounter_id"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Search and filter patient encounters in the hospital registry."""
    query = (
        db.query(EncounterModel, PredictionModel)
        .outerjoin(PredictionModel, EncounterModel.encounter_id == PredictionModel.encounter_id)
    )

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (EncounterModel.patient_id.ilike(search_term))
            | (EncounterModel.encounter_id.ilike(search_term))
            | (EncounterModel.condition_name.ilike(search_term))
            | (EncounterModel.primary_diagnosis_code.ilike(search_term))
        )

    if risk_category:
        query = query.filter(PredictionModel.risk_category == risk_category)

    if condition_name:
        query = query.filter(EncounterModel.condition_name == condition_name)

    if discharge_disposition:
        query = query.filter(EncounterModel.discharge_disposition == discharge_disposition)

    if payer_type:
        query = query.filter(EncounterModel.payer_type == payer_type)

    # Sorting
    if sort_by == "predicted_risk":
        col = PredictionModel.predicted_risk_probability
    elif sort_by == "discharge_date":
        col = EncounterModel.discharge_date
    else:
        col = EncounterModel.encounter_id

    if sort_order == "desc":
        query = query.order_by(desc(col))
    else:
        query = query.order_by(asc(col))

    total_records = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    items = []
    for enc, pred in results:
        items.append({
            "encounter_id": enc.encounter_id,
            "patient_id": enc.patient_id,
            "age": enc.age,
            "sex": enc.sex,
            "payer_type": enc.payer_type,
            "condition_name": enc.condition_name,
            "primary_diagnosis_code": enc.primary_diagnosis_code,
            "discharge_disposition": enc.discharge_disposition,
            "discharge_date": enc.discharge_date,
            "length_of_stay": enc.length_of_stay,
            "medication_count": enc.medication_count,
            "prior_admissions_6m": enc.prior_admissions_6m,
            "is_planned_readmission": enc.is_planned_readmission,
            "predicted_risk_probability": round(pred.predicted_risk_probability, 4) if pred else None,
            "risk_percentage": round(pred.predicted_risk_probability * 100, 1) if pred else None,
            "risk_category": pred.risk_category if pred else "Unscored",
            "observed_readmission": enc.readmitted_30d,
        })

    total_pages = (total_records + page_size - 1) // page_size

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": total_pages,
    }


@router.get("/{patient_id}")
def get_patient_detail(patient_id: str, db: Session = Depends(get_db)):
    """Fetch complete patient clinical record, all encounters, and AI decision support recommendations."""
    patient = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()
    if not patient:
        # Check if an encounter exists with this ID
        enc = db.query(EncounterModel).filter(EncounterModel.encounter_id == patient_id).first()
        if enc:
            patient_id = enc.patient_id
            patient = db.query(PatientModel).filter(PatientModel.patient_id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID '{patient_id}' not found.")

    encounters = (
        db.query(EncounterModel)
        .filter(EncounterModel.patient_id == patient_id)
        .order_by(desc(EncounterModel.discharge_date))
        .all()
    )

    enc_details = []
    latest_prediction = None
    latest_recommendations = None

    for enc in encounters:
        pred = db.query(PredictionModel).filter(PredictionModel.encounter_id == enc.encounter_id).first()
        enc_dict = {
            "encounter_id": enc.encounter_id,
            "discharge_date": enc.discharge_date,
            "condition_name": enc.condition_name,
            "primary_diagnosis_code": enc.primary_diagnosis_code,
            "length_of_stay": enc.length_of_stay,
            "prior_admissions_6m": enc.prior_admissions_6m,
            "medication_count": enc.medication_count,
            "discharge_disposition": enc.discharge_disposition,
            "labs": {
                "hemoglobin": enc.hemoglobin,
                "serum_creatinine": enc.serum_creatinine,
                "sodium": enc.sodium,
                "bun": enc.bun,
                "glucose": enc.glucose,
            },
            "follow_up_scheduled": enc.follow_up_scheduled,
            "is_planned_readmission": enc.is_planned_readmission,
            "observed_readmission": enc.readmitted_30d,
            "prediction": {
                "probability": round(pred.predicted_risk_probability, 4) if pred else None,
                "risk_percentage": round(pred.predicted_risk_probability * 100, 1) if pred else None,
                "risk_category": pred.risk_category if pred else "Unscored",
                "top_drivers": pred.top_contributing_features if pred else [],
                "data_quality_warnings": pred.data_quality_warnings if pred else [],
            } if pred else None,
        }
        enc_details.append(enc_dict)

        if latest_prediction is None and pred:
            latest_prediction = enc_dict["prediction"]
            # Generate tailored intervention plan
            row_for_rec = {
                "medication_count": enc.medication_count,
                "follow_up_scheduled": enc.follow_up_scheduled,
                "prior_admissions_6m": enc.prior_admissions_6m,
                "discharge_disposition": enc.discharge_disposition,
                "primary_diagnosis_code": enc.primary_diagnosis_code,
                "condition_name": enc.condition_name,
            }
            latest_recommendations = recommend_interventions_for_encounter(
                row_for_rec, pred.predicted_risk_probability
            )

    return {
        "patient_id": patient.patient_id,
        "demographics": {
            "age": patient.age,
            "sex": patient.sex,
            "payer_type": patient.payer_type,
        },
        "total_encounters_on_record": len(enc_details),
        "latest_encounter": enc_details[0] if enc_details else None,
        "all_encounters": enc_details,
        "ai_decision_support": {
            "active_prediction": latest_prediction,
            "intervention_recommendations": latest_recommendations,
        },
    }
