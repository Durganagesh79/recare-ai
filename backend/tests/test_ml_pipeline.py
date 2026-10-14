"""
ReCare AI - Unit Tests for ML Training, Prediction Bounds, and Calibration Metrics
"""

import pytest
import numpy as np
import os
from backend.ml.train_model import compute_expected_calibration_error
from backend.ml.predict import predict_single_encounter, predict_batch_encounters, get_risk_tier
from backend.ml.evaluate import evaluate_model_on_test_set


def test_ece_computation():
    """Verify Expected Calibration Error calculation on known synthetic probabilities."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    # Perfectly calibrated case: 0.0 for zeros, 1.0 for ones
    y_prob_perfect = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0])
    ece_perf, info = compute_expected_calibration_error(y_true, y_prob_perfect, n_bins=5)
    assert ece_perf == 0.0

    # Miscalibrated case: predicts 0.9 for all zeros
    y_prob_bad = np.array([0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
    ece_bad, _ = compute_expected_calibration_error(y_true, y_prob_bad, n_bins=5)
    assert ece_bad > 0.3


def test_prediction_output_and_bounds():
    """Verify inference engine returns valid calibrated probabilities in [0.0, 1.0] and rich drivers."""
    sample_encounter = {
        "encounter_id": "ENC-TEST-1",
        "patient_id": "PT-TEST-1",
        "age": 72,
        "sex": "Female",
        "payer_type": "Medicare",
        "primary_diagnosis_code": "I50.9",
        "secondary_diagnoses_count": 5,
        "length_of_stay": 6,
        "prior_admissions": 3,
        "prior_admissions_6m": 2,
        "num_procedures": 1,
        "discharge_disposition": "Home Health Care",
        "medication_count": 14,
        "hemoglobin": 10.5,
        "serum_creatinine": 1.9,
        "sodium": 136.0,
        "bun": 24.0,
        "glucose": 135.0,
        "follow_up_scheduled": False,
        "is_planned_readmission": False,
    }

    pred = predict_single_encounter(sample_encounter)
    assert 0.0 <= pred["predicted_risk_probability"] <= 1.0
    assert pred["risk_category"] in ["Low Risk", "Moderate Risk", "High Risk"]
    assert len(pred["top_contributing_features"]) > 0
    # Check that high prior admissions and polypharmacy were recognized as risk drivers
    driver_features = [d["feature"] for d in pred["top_contributing_features"]]
    assert "prior_admissions_6m" in driver_features or "medication_count" in driver_features


def test_batch_prediction_consistency():
    """Verify batch prediction returns matching length and valid schema."""
    batch = [
        {
            "encounter_id": f"ENC-{i}",
            "patient_id": f"PT-{i}",
            "age": 65 + i,
            "sex": "Male",
            "payer_type": "Commercial",
            "primary_diagnosis_code": "J44.1",
            "secondary_diagnoses_count": 3,
            "length_of_stay": 3,
            "prior_admissions": 1,
            "prior_admissions_6m": 1,
            "num_procedures": 0,
            "discharge_disposition": "Home",
            "medication_count": 8,
            "hemoglobin": 13.0,
            "serum_creatinine": 1.0,
            "sodium": 140.0,
            "bun": 16.0,
            "glucose": 110.0,
            "follow_up_scheduled": True,
            "is_planned_readmission": False,
        }
        for i in range(5)
    ]
    results = predict_batch_encounters(batch)
    assert len(results) == 5
    for r in results:
        assert 0.0 <= r["predicted_risk_probability"] <= 1.0
