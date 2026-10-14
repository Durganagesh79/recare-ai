"""
ReCare AI - SQLAlchemy Database Models
Defines schema for patients, encounters, predictions, weekly call list runs, and audit logs.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.db.database import Base


class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(64), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    sex = Column(String(32), nullable=True)
    payer_type = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    encounters = relationship("EncounterModel", back_populates="patient", cascade="all, delete-orphan")


class EncounterModel(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), index=True, nullable=False)
    
    age = Column(Integer, nullable=True)
    sex = Column(String(32), nullable=True)
    payer_type = Column(String(64), nullable=True)
    primary_diagnosis_code = Column(String(32), nullable=True)
    condition_name = Column(String(128), nullable=True)
    secondary_diagnoses_count = Column(Integer, default=0)
    length_of_stay = Column(Integer, default=1)
    prior_admissions = Column(Integer, default=0)
    prior_admissions_6m = Column(Integer, default=0)
    num_procedures = Column(Integer, default=0)
    discharge_disposition = Column(String(64), default="Home")
    medication_count = Column(Integer, default=0)

    # Labs
    hemoglobin = Column(Float, nullable=True)
    serum_creatinine = Column(Float, nullable=True)
    sodium = Column(Float, nullable=True)
    bun = Column(Float, nullable=True)
    glucose = Column(Float, nullable=True)

    discharge_date = Column(String(32), nullable=True, index=True)
    follow_up_scheduled = Column(Boolean, nullable=True)
    is_planned_readmission = Column(Boolean, default=False)
    readmitted_30d = Column(Integer, nullable=True)  # Ground truth label (hidden during inference)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("PatientModel", back_populates="encounters")
    prediction = relationship("PredictionModel", back_populates="encounter", uselist=False)


class PredictionModel(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(String(64), ForeignKey("encounters.encounter_id"), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), index=True, nullable=False)
    predicted_risk_probability = Column(Float, nullable=False)
    risk_category = Column(String(32), nullable=False)
    model_version = Column(String(64), default="v1.2.0-calibrated-histgb")
    top_contributing_features = Column(JSON, nullable=True)
    data_quality_warnings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    encounter = relationship("EncounterModel", back_populates="prediction")


class CallListRunModel(Base):
    __tablename__ = "call_list_runs"

    id = Column(Integer, primary_key=True, index=True)
    call_list_id = Column(String(64), unique=True, index=True, nullable=False)
    reporting_period = Column(String(64), nullable=False)
    ranking_mode = Column(String(32), default="risk_first")
    capacity_limit = Column(Integer, default=50)
    selected_count = Column(Integer, default=0)
    summary_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("CallListEntryModel", back_populates="call_list_run", cascade="all, delete-orphan")


class CallListEntryModel(Base):
    __tablename__ = "call_list_entries"

    id = Column(Integer, primary_key=True, index=True)
    call_list_run_id = Column(Integer, ForeignKey("call_list_runs.id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    encounter_id = Column(String(64), nullable=False, index=True)
    patient_id = Column(String(64), nullable=False, index=True)
    predicted_risk_probability = Column(Float, nullable=False)
    expected_benefit = Column(Float, nullable=True)
    recommended_intervention = Column(String(128), nullable=False)
    intervention_priority = Column(String(32), default="High")
    intervention_action_plan = Column(Text, nullable=True)
    contact_status = Column(String(32), default="Pending")  # Pending, Attempted, Connected, Declined
    follow_up_notes = Column(Text, default="")
    selection_rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    call_list_run = relationship("CallListRunModel", back_populates="entries")


class DatasetVersionModel(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(64), unique=True, index=True, nullable=False)
    file_name = Column(String(256), nullable=False)
    row_count = Column(Integer, nullable=False)
    duplicate_count = Column(Integer, default=0)
    missing_stats = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
