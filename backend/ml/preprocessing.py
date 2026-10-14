"""
ReCare AI - Data Preprocessing & Feature Engineering Pipeline
Handles data cleaning, diagnosis code normalization, missingness indicator engineering,
patient-group-aware splitting to avoid leakage, and scikit-learn compatible transformer pipelines.
"""

import re
import logging
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit

logger = logging.getLogger(__name__)

# Diagnosis code normalization map (ICD-10 variants & legacy ICD-9 mapped to standard condition groups)
ICD_NORMALIZATION_MAP = {
    # Heart Failure
    "I50.9": "I50.9", "I509": "I50.9", "428.0": "I50.9", "428.1": "I50.9", "I50.22": "I50.9",
    # COPD
    "J44.1": "J44.1", "J441": "J44.1", "496": "J44.1", "J44.9": "J44.1",
    # AMI
    "I21.0": "I21.0", "I210": "I21.0", "410.9": "I21.0", "I21.9": "I21.0", "410.0": "I21.0",
    # Pneumonia
    "J18.9": "J18.9", "J189": "J18.9", "486": "J18.9", "J15.9": "J18.9",
    # Diabetes
    "E11.65": "E11.65", "E1165": "E11.65", "250.00": "E11.65", "E11.9": "E11.65", "250.02": "E11.65",
    # Sepsis
    "A41.9": "A41.9", "A419": "A41.9", "995.91": "A41.9", "A41.0": "A41.9",
    # Stroke
    "I63.9": "I63.9", "I639": "I63.9", "434.91": "I63.9", "I63.4": "I63.9",
    # Orthopedic
    "Z96.651": "Z96.651", "Z96651": "Z96.651", "V43.64": "Z96.651", "M16.1": "Z96.651",
}

CONDITION_MAP = {
    "I50.9": "Heart Failure",
    "J44.1": "COPD",
    "I21.0": "Acute Myocardial Infarction",
    "J18.9": "Pneumonia",
    "E11.65": "Diabetes with Complications",
    "A41.9": "Sepsis",
    "I63.9": "Stroke / Cerebrovascular",
    "Z96.651": "Orthopedic / Joint Replacement",
}

NUMERIC_FEATURES = [
    "age",
    "secondary_diagnoses_count",
    "length_of_stay",
    "prior_admissions",
    "prior_admissions_6m",
    "num_procedures",
    "medication_count",
    "hemoglobin",
    "serum_creatinine",
    "sodium",
    "bun",
    "glucose",
]

LAB_FEATURES = [
    "hemoglobin",
    "serum_creatinine",
    "sodium",
    "bun",
    "glucose",
]

CATEGORICAL_FEATURES = [
    "sex",
    "payer_type",
    "discharge_disposition",
    "normalized_diagnosis",
    "follow_up_scheduled",
]

EXCLUDED_FROM_FEATURES = [
    "encounter_id",
    "patient_id",
    "discharge_date",
    "is_planned_readmission",
    "readmitted_30d",
    "primary_diagnosis_code",
    "condition_name",
]


def normalize_diagnosis_code(code: Any) -> str:
    """Normalize raw diagnosis code string (strip whitespaces, uppercase, map legacy ICD-9)."""
    if pd.isna(code):
        return "UNKNOWN"
    cleaned = str(code).strip().upper()
    return ICD_NORMALIZATION_MAP.get(cleaned, cleaned)


def deduplicate_encounters(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove exact or duplicate encounter records while retaining genuine multi-encounter patients."""
    initial_count = len(df)
    # Deduplicate strictly on encounter_id keeping the first instance
    df_dedup = df.drop_duplicates(subset=["encounter_id"], keep="first").copy()
    duplicates_removed = initial_count - len(df_dedup)
    logger.info(f"Deduplication: removed {duplicates_removed} duplicate encounter records.")
    return df_dedup, duplicates_removed


class ClinicalFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom Scikit-Learn Transformer for:
    1. Creating missingness indicators for laboratory tests (informative missingness).
    2. Engineering domain-specific clinical risk interaction ratios (e.g., BUN/Creatinine ratio, prior admission velocity).
    3. Follow-up appointment encoding.
    """
    def __init__(self):
        self.engineered_feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = X.copy()

        # Ensure normalized diagnosis exists
        if "normalized_diagnosis" not in X_out.columns and "primary_diagnosis_code" in X_out.columns:
            X_out["normalized_diagnosis"] = X_out["primary_diagnosis_code"].apply(normalize_diagnosis_code)
        elif "normalized_diagnosis" not in X_out.columns:
            X_out["normalized_diagnosis"] = "UNKNOWN"

        # Missingness indicator flags for laboratories
        for lab in LAB_FEATURES:
            if lab in X_out.columns:
                X_out[f"{lab}_is_missing"] = X_out[lab].isna().astype(int)

        # Follow-up scheduled standardization
        if "follow_up_scheduled" in X_out.columns:
            X_out["follow_up_scheduled"] = X_out["follow_up_scheduled"].fillna("Missing").astype(str)
        else:
            X_out["follow_up_scheduled"] = "Missing"

        # Payer and Sex missingness handling
        if "payer_type" in X_out.columns:
            X_out["payer_type"] = X_out["payer_type"].fillna("Unknown").astype(str)
        if "sex" in X_out.columns:
            X_out["sex"] = X_out["sex"].fillna("Other/Unknown").astype(str)
        if "discharge_disposition" in X_out.columns:
            X_out["discharge_disposition"] = X_out["discharge_disposition"].fillna("Home").astype(str)

        # High-utilization velocity indicator (ratio of 6-month prior admissions to total prior admissions)
        if "prior_admissions_6m" in X_out.columns and "prior_admissions" in X_out.columns:
            prior_tot = np.maximum(X_out["prior_admissions"].fillna(0), 1)
            X_out["prior_velocity_ratio"] = (X_out["prior_admissions_6m"].fillna(0) / prior_tot).clip(0, 1)

        # Polypharmacy flag (>= 10 discharge medications)
        if "medication_count" in X_out.columns:
            X_out["polypharmacy_flag"] = (X_out["medication_count"] >= 10).astype(int)

        return X_out


def create_preprocessor() -> Tuple[Pipeline, List[str]]:
    """
    Build scikit-learn ColumnTransformer and Pipeline for end-to-end preprocessing.
    Keeps feature transformations unified for training and production inference.
    """
    feature_engineer = ClinicalFeatureEngineer()

    # Derived feature columns after feature engineering
    lab_indicator_cols = [f"{lab}_is_missing" for lab in LAB_FEATURES]
    numeric_cols = NUMERIC_FEATURES + lab_indicator_cols + ["prior_velocity_ratio", "polypharmacy_flag"]

    num_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    column_transformer = ColumnTransformer(
        transformers=[
            ("num", num_transformer, numeric_cols),
            ("cat", cat_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    full_preprocessing_pipeline = Pipeline(steps=[
        ("engineer", feature_engineer),
        ("column_transforms", column_transformer),
    ])

    return full_preprocessing_pipeline, numeric_cols


def patient_aware_train_test_split(
    df: pd.DataFrame,
    test_size: float = 0.20,
    val_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform Patient-Group-Aware splitting on patient_id so that encounters from the same patient
    never leak across train, validation, and test datasets.
    """
    logger.info("Executing patient-group-aware data split...")
    # First split: Train+Val vs Test
    gss_test = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_val_idx, test_idx = next(gss_test.split(df, groups=df["patient_id"]))
    
    train_val_df = df.iloc[train_val_idx].copy()
    test_df = df.iloc[test_idx].copy()

    # Second split: Train vs Validation
    val_rel_size = val_size / (1.0 - test_size)
    gss_val = GroupShuffleSplit(n_splits=1, test_size=val_rel_size, random_state=random_state + 1)
    train_idx, val_idx = next(gss_val.split(train_val_df, groups=train_val_df["patient_id"]))

    train_df = train_val_df.iloc[train_idx].copy()
    val_df = train_val_df.iloc[val_idx].copy()

    # Verify no patient overlap
    train_patients = set(train_df["patient_id"])
    val_patients = set(val_df["patient_id"])
    test_patients = set(test_df["patient_id"])

    assert len(train_patients.intersection(val_patients)) == 0, "Patient leakage detected between train and val!"
    assert len(train_patients.intersection(test_patients)) == 0, "Patient leakage detected between train and test!"
    assert len(val_patients.intersection(test_patients)) == 0, "Patient leakage detected between val and test!"

    logger.info(
        f"Split complete: Train={len(train_df)} ({len(train_patients)} pts), "
        f"Val={len(val_df)} ({len(val_patients)} pts), "
        f"Test={len(test_df)} ({len(test_patients)} pts)"
    )

    return train_df, val_df, test_df
