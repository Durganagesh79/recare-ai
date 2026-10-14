"""
ReCare AI - Pydantic Request & Response Validation Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EncounterInputSchema(BaseModel):
    encounter_id: Optional[str] = "ENC-NEW"
    patient_id: Optional[str] = "PT-NEW"
    age: int = Field(..., ge=0, le=125)
    sex: str = Field(..., description="Male, Female, or Other/Unknown")
    payer_type: str = Field(..., description="Medicare, Medicaid, Commercial, or Uninsured/Self-pay")
    primary_diagnosis_code: str
    condition_name: Optional[str] = None
    secondary_diagnoses_count: int = Field(0, ge=0)
    length_of_stay: int = Field(1, ge=1)
    prior_admissions: int = Field(0, ge=0)
    prior_admissions_6m: int = Field(0, ge=0)
    num_procedures: int = Field(0, ge=0)
    discharge_disposition: str = Field("Home")
    medication_count: int = Field(0, ge=0)
    hemoglobin: Optional[float] = None
    serum_creatinine: Optional[float] = None
    sodium: Optional[float] = None
    bun: Optional[float] = None
    glucose: Optional[float] = None
    discharge_date: Optional[str] = None
    follow_up_scheduled: Optional[bool] = None
    is_planned_readmission: Optional[bool] = False


class BatchEncounterInputSchema(BaseModel):
    encounters: List[EncounterInputSchema]


class FeatureContributionSchema(BaseModel):
    feature: str
    feature_label: str
    value: str
    impact: str
    direction: str
    actionable_suggestion: str


class PredictionResponseSchema(BaseModel):
    encounter_id: str
    patient_id: str
    predicted_risk_probability: float
    risk_percentage: float
    risk_category: str
    model_version: str
    top_contributing_features: List[FeatureContributionSchema]
    data_quality_warnings: List[str]
    prediction_timestamp: str


class PatientListItemSchema(BaseModel):
    patient_id: str
    encounter_id: str
    age: Optional[int]
    sex: Optional[str]
    payer_type: Optional[str]
    condition_name: Optional[str]
    primary_diagnosis_code: Optional[str]
    discharge_disposition: Optional[str]
    discharge_date: Optional[str]
    predicted_risk: Optional[float]
    risk_category: Optional[str]
    is_planned_readmission: bool
    observed_readmission: Optional[int] = None


class CallListGenerateRequest(BaseModel):
    mode: str = Field("risk_first", description="'risk_first' or 'expected_benefit'")
    max_capacity: int = Field(50, ge=1, le=100)
    filter_planned_readmissions: bool = True


class CallListEntryUpdateSchema(BaseModel):
    contact_status: Optional[str] = None  # Pending, Attempted, Connected, Declined
    follow_up_notes: Optional[str] = None


class ImpactScenarioRequest(BaseModel):
    cohort_size: int = 50
    reach_rate: Optional[float] = None
    relative_risk_reduction: Optional[float] = None
