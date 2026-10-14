"""
ReCare AI - Predictions API Router
Provides single encounter inference, batch predictions, and prediction history queries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import PredictionModel, EncounterModel
from backend.ml.predict import predict_single_encounter, predict_batch_encounters
from backend.schemas.pydantic_models import EncounterInputSchema, BatchEncounterInputSchema, PredictionResponseSchema

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.post("", response_model=PredictionResponseSchema)
def create_single_prediction(payload: EncounterInputSchema):
    """Generate calibrated 30-day readmission risk prediction and actionable clinical drivers for one encounter."""
    try:
        record_dict = payload.model_dump()
        result = predict_single_encounter(record_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@router.post("/batch")
def create_batch_predictions(payload: BatchEncounterInputSchema):
    """Generate calibrated predictions for a batch of discharge encounters."""
    try:
        records = [enc.model_dump() for enc in payload.encounters]
        results = predict_batch_encounters(records)
        return {
            "total_evaluated": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")


@router.get("")
def list_predictions(
    db: Session = Depends(get_db),
    risk_category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    """Retrieve historical persisted risk predictions with pagination."""
    query = db.query(PredictionModel, EncounterModel).join(
        EncounterModel, PredictionModel.encounter_id == EncounterModel.encounter_id
    )

    if risk_category:
        query = query.filter(PredictionModel.risk_category == risk_category)

    query = query.order_by(PredictionModel.predicted_risk_probability.desc())
    total_records = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    items = []
    for pred, enc in results:
        items.append({
            "encounter_id": pred.encounter_id,
            "patient_id": pred.patient_id,
            "age": enc.age,
            "sex": enc.sex,
            "payer_type": enc.payer_type,
            "condition_name": enc.condition_name,
            "predicted_risk_probability": round(pred.predicted_risk_probability, 4),
            "risk_percentage": round(pred.predicted_risk_probability * 100, 1),
            "risk_category": pred.risk_category,
            "top_contributing_features": pred.top_contributing_features,
            "data_quality_warnings": pred.data_quality_warnings,
            "created_at": pred.created_at.isoformat() if pred.created_at else None,
        })

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": (total_records + page_size - 1) // page_size,
    }


@router.get("/{encounter_id}")
def get_prediction_for_encounter(encounter_id: str, db: Session = Depends(get_db)):
    """Fetch stored prediction and drivers for a specific encounter ID."""
    pred = db.query(PredictionModel).filter(PredictionModel.encounter_id == encounter_id).first()
    if not pred:
        raise HTTPException(status_code=404, detail=f"No prediction found for encounter '{encounter_id}'.")

    return {
        "encounter_id": pred.encounter_id,
        "patient_id": pred.patient_id,
        "predicted_risk_probability": round(pred.predicted_risk_probability, 4),
        "risk_percentage": round(pred.predicted_risk_probability * 100, 1),
        "risk_category": pred.risk_category,
        "model_version": pred.model_version,
        "top_contributing_features": pred.top_contributing_features,
        "data_quality_warnings": pred.data_quality_warnings,
        "prediction_timestamp": pred.created_at.isoformat() if pred.created_at else None,
    }
