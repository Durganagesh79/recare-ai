"""
ReCare AI - Database Initialization & Seed Script
Creates tables, ingests synthetic records into SQLite/PostgreSQL, runs predictions,
and generates the initial baseline weekly call list.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from backend.db.database import engine, SessionLocal, Base
from backend.db.models import (
    PatientModel,
    EncounterModel,
    PredictionModel,
    CallListRunModel,
    CallListEntryModel,
    DatasetVersionModel,
)
from backend.ml.predict import get_model_pipeline, predict_batch_encounters
from backend.services.intervention_optimizer import optimize_weekly_call_list

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def initialize_and_seed_database(
    dataset_path: str = "data/processed/synthetic_discharges.csv",
    max_seed_encounters: int = 5000,  # Seed first 5,000 for rapid DB startup, or full if requested
):
    """Create all tables and seed with synthetic encounters and predictions."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_encounters = db.query(EncounterModel).count()
        if existing_encounters > 0:
            logger.info(f"Database already populated with {existing_encounters} encounters. Skipping initial seed.")
            return

        if not os.path.exists(dataset_path):
            logger.warning(f"Dataset not found at {dataset_path}. Database tables created without seed data.")
            return

        logger.info(f"Seeding database from {dataset_path} (loading up to {max_seed_encounters} encounters)...")
        raw_df = pd.read_csv(dataset_path)
        from backend.ml.preprocessing import deduplicate_encounters
        df, dups_removed = deduplicate_encounters(raw_df)
        logger.info(f"Deduplication removed {dups_removed} duplicate encounter records before database ingestion.")

        # Ingest Patients
        unique_pts = df.drop_duplicates(subset=["patient_id"]).head(max_seed_encounters)
        patient_objs = []
        for _, row in unique_pts.iterrows():
            patient_objs.append(
                PatientModel(
                    patient_id=str(row["patient_id"]),
                    age=int(row["age"]) if not pd.isna(row["age"]) else None,
                    sex=str(row["sex"]) if not pd.isna(row["sex"]) else "Other/Unknown",
                    payer_type=str(row["payer_type"]) if not pd.isna(row["payer_type"]) else "Unknown",
                )
            )
        db.bulk_save_objects(patient_objs)
        db.commit()
        logger.info(f"Seeded {len(patient_objs)} unique patients.")

        # Ingest Encounters
        seed_df = df.head(max_seed_encounters).copy()
        encounter_objs = []
        for _, row in seed_df.iterrows():
            encounter_objs.append(
                EncounterModel(
                    encounter_id=str(row["encounter_id"]),
                    patient_id=str(row["patient_id"]),
                    age=int(row["age"]) if not pd.isna(row["age"]) else None,
                    sex=str(row["sex"]) if not pd.isna(row["sex"]) else "Other/Unknown",
                    payer_type=str(row["payer_type"]) if not pd.isna(row["payer_type"]) else "Unknown",
                    primary_diagnosis_code=str(row["primary_diagnosis_code"]).strip() if not pd.isna(row["primary_diagnosis_code"]) else None,
                    condition_name=str(row.get("condition_name", "Clinical Care")),
                    secondary_diagnoses_count=int(row["secondary_diagnoses_count"]) if not pd.isna(row["secondary_diagnoses_count"]) else 0,
                    length_of_stay=int(row["length_of_stay"]) if not pd.isna(row["length_of_stay"]) else 1,
                    prior_admissions=int(row["prior_admissions"]) if not pd.isna(row["prior_admissions"]) else 0,
                    prior_admissions_6m=int(row["prior_admissions_6m"]) if not pd.isna(row["prior_admissions_6m"]) else 0,
                    num_procedures=int(row["num_procedures"]) if not pd.isna(row["num_procedures"]) else 0,
                    discharge_disposition=str(row["discharge_disposition"]) if not pd.isna(row["discharge_disposition"]) else "Home",
                    medication_count=int(row["medication_count"]) if not pd.isna(row["medication_count"]) else 0,
                    hemoglobin=float(row["hemoglobin"]) if not pd.isna(row["hemoglobin"]) else None,
                    serum_creatinine=float(row["serum_creatinine"]) if not pd.isna(row["serum_creatinine"]) else None,
                    sodium=float(row["sodium"]) if not pd.isna(row["sodium"]) else None,
                    bun=float(row["bun"]) if not pd.isna(row["bun"]) else None,
                    glucose=float(row["glucose"]) if not pd.isna(row["glucose"]) else None,
                    discharge_date=str(row["discharge_date"]) if not pd.isna(row["discharge_date"]) else None,
                    follow_up_scheduled=bool(row["follow_up_scheduled"]) if not pd.isna(row["follow_up_scheduled"]) else None,
                    is_planned_readmission=bool(row.get("is_planned_readmission", False)),
                    readmitted_30d=int(row["readmitted_30d"]) if not pd.isna(row["readmitted_30d"]) else None,
                )
            )
        db.bulk_save_objects(encounter_objs)
        db.commit()
        logger.info(f"Seeded {len(encounter_objs)} hospital encounters.")

        # Compute and persist predictions for seeded encounters using model
        logger.info("Computing predictions for seeded encounters...")
        records_to_predict = seed_df.to_dict(orient="records")
        preds = predict_batch_encounters(records_to_predict)

        pred_objs = []
        for p in preds:
            pred_objs.append(
                PredictionModel(
                    encounter_id=p["encounter_id"],
                    patient_id=p["patient_id"],
                    predicted_risk_probability=p["predicted_risk_probability"],
                    risk_category=p["risk_category"],
                    model_version=p["model_version"],
                    top_contributing_features=p["top_contributing_features"],
                    data_quality_warnings=p["data_quality_warnings"],
                )
            )
        db.bulk_save_objects(pred_objs)
        db.commit()
        logger.info(f"Persisted {len(pred_objs)} calibrated risk predictions.")

        # Generate and seed initial Monday Morning Call List
        logger.info("Generating initial Monday Morning Call List run...")
        call_list = optimize_weekly_call_list(seed_df, mode="risk_first", max_capacity=50)

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
        logger.info(f"Seeded initial weekly call list run with {len(entry_objs)} patient entries.")

    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    initialize_and_seed_database()
