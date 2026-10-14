"""
ReCare AI - Unit Tests for Preprocessing and Data Leakage Prevention
"""

import pytest
import numpy as np
import pandas as pd
from backend.ml.preprocessing import (
    normalize_diagnosis_code,
    deduplicate_encounters,
    patient_aware_train_test_split,
    create_preprocessor,
    ClinicalFeatureEngineer,
)


def test_diagnosis_normalization():
    """Verify legacy ICD-9 and unformatted ICD-10 are correctly normalized."""
    assert normalize_diagnosis_code("428.0") == "I50.9"      # Heart Failure
    assert normalize_diagnosis_code("I509") == "I50.9"       # Missing dot
    assert normalize_diagnosis_code(" 496 ") == "J44.1"      # Legacy COPD with whitespace
    assert normalize_diagnosis_code("410.9") == "I21.0"      # Legacy AMI
    assert normalize_diagnosis_code("486") == "J18.9"        # Legacy Pneumonia


def test_encounter_deduplication():
    """Verify duplicate encounters are dropped without dropping valid multiple encounters per patient."""
    df = pd.DataFrame({
        "encounter_id": ["ENC-1", "ENC-2", "ENC-1", "ENC-3"],
        "patient_id": ["PT-A", "PT-A", "PT-A", "PT-B"],
        "age": [65, 65, 65, 70],
    })
    deduped, dups_removed = deduplicate_encounters(df)
    assert len(deduped) == 3
    assert dups_removed == 1
    # PT-A still has 2 distinct encounters (ENC-1 and ENC-2)
    assert len(deduped[deduped["patient_id"] == "PT-A"]) == 2


def test_patient_group_aware_leakage_prevention():
    """Verify patient-aware split strictly prevents identical patient IDs across train, val, and test splits."""
    # Create dataset with multiple encounters per patient
    patient_ids = [f"PT-{i}" for i in range(100)] * 3
    encounter_ids = [f"ENC-{i}" for i in range(len(patient_ids))]
    df = pd.DataFrame({
        "encounter_id": encounter_ids,
        "patient_id": patient_ids,
        "age": np.random.randint(40, 80, size=len(patient_ids)),
        "readmitted_30d": np.random.binomial(1, 0.2, size=len(patient_ids)),
    })

    train_df, val_df, test_df = patient_aware_train_test_split(df, test_size=0.20, val_size=0.15)
    train_pts = set(train_df["patient_id"])
    val_pts = set(val_df["patient_id"])
    test_pts = set(test_df["patient_id"])

    # Strict zero leakage assertion
    assert len(train_pts.intersection(val_pts)) == 0
    assert len(train_pts.intersection(test_pts)) == 0
    assert len(val_pts.intersection(test_pts)) == 0


def test_feature_engineering_missingness_indicators():
    """Verify transformer generates missingness indicators for laboratory tests."""
    df = pd.DataFrame({
        "hemoglobin": [12.0, np.nan, 14.5],
        "serum_creatinine": [np.nan, 1.2, 0.9],
        "sodium": [138.0, 140.0, np.nan],
        "bun": [18.0, np.nan, 22.0],
        "glucose": [110.0, 130.0, np.nan],
        "primary_diagnosis_code": ["428.0", "J44.1", "I21.0"],
        "medication_count": [12, 5, 8],
        "prior_admissions": [2, 0, 1],
        "prior_admissions_6m": [2, 0, 0],
    })
    engineer = ClinicalFeatureEngineer()
    transformed = engineer.transform(df)

    assert "hemoglobin_is_missing" in transformed.columns
    assert transformed["hemoglobin_is_missing"].tolist() == [0, 1, 0]
    assert "serum_creatinine_is_missing" in transformed.columns
    assert transformed["serum_creatinine_is_missing"].tolist() == [1, 0, 0]
    assert "polypharmacy_flag" in transformed.columns
    assert transformed["polypharmacy_flag"].tolist() == [1, 0, 0]
