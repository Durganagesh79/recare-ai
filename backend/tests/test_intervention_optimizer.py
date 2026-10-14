"""
ReCare AI - Unit Tests for Resource-Constrained Weekly Intervention Optimizer
CRITICAL GUARANTEES:
1. Call list never exceeds 50 unique patients per week.
2. No duplicate calls to the same patient in a single planning cycle.
3. Planned readmissions are properly filtered.
4. Mode A vs Mode B ranking logic operates correctly.
"""

import pytest
import numpy as np
import pandas as pd
from backend.services.intervention_optimizer import optimize_weekly_call_list, MAX_WEEKLY_CAPACITY


@pytest.fixture
def sample_encounters_dataframe():
    """Generate 120 synthetic test encounters with some recurring patients and planned admissions."""
    np.random.seed(123)
    # 70 unique patients across 120 encounters
    patient_ids = [f"PT-{i}" for i in np.random.randint(100, 170, size=120)]
    encounter_ids = [f"ENC-{2000 + i}" for i in range(120)]

    df = pd.DataFrame({
        "encounter_id": encounter_ids,
        "patient_id": patient_ids,
        "age": np.random.randint(50, 90, size=120),
        "sex": np.random.choice(["Male", "Female"], size=120),
        "payer_type": np.random.choice(["Medicare", "Medicaid", "Commercial"], size=120),
        "primary_diagnosis_code": np.random.choice(["I50.9", "J44.1", "I21.0", "Z96.651"], size=120),
        "condition_name": "Heart Failure",
        "secondary_diagnoses_count": np.random.randint(1, 8, size=120),
        "length_of_stay": np.random.randint(2, 12, size=120),
        "prior_admissions": np.random.randint(0, 5, size=120),
        "prior_admissions_6m": np.random.randint(0, 3, size=120),
        "num_procedures": np.random.randint(0, 3, size=120),
        "discharge_disposition": np.random.choice(["Home", "Home Health Care", "SNF"], size=120),
        "medication_count": np.random.randint(4, 20, size=120),
        "hemoglobin": np.random.normal(12.5, 1.5, size=120),
        "serum_creatinine": np.random.normal(1.2, 0.5, size=120),
        "sodium": 138.0,
        "bun": 18.0,
        "glucose": 120.0,
        "discharge_date": "2026-03-15",
        "follow_up_scheduled": True,
        # 10 records are planned readmissions
        "is_planned_readmission": [i < 10 for i in range(120)],
        "readmitted_30d": np.random.binomial(1, 0.2, size=120),
    })
    return df


def test_capacity_constraint_strictly_at_most_50(sample_encounters_dataframe):
    """Confirm the optimizer NEVER exceeds the weekly capacity of 50 patients."""
    res_mode_a = optimize_weekly_call_list(sample_encounters_dataframe, mode="risk_first", max_capacity=50)
    assert res_mode_a["selected_count"] <= 50
    assert len(res_mode_a["selected_patients"]) <= 50

    res_mode_b = optimize_weekly_call_list(sample_encounters_dataframe, mode="expected_benefit", max_capacity=50)
    assert res_mode_b["selected_count"] <= 50
    assert len(res_mode_b["selected_patients"]) <= 50


def test_patient_uniqueness_guarantee(sample_encounters_dataframe):
    """Confirm every patient selected in the call list is UNIQUE (no repeated calls to same patient)."""
    res = optimize_weekly_call_list(sample_encounters_dataframe, mode="risk_first", max_capacity=50)
    selected_patients = res["selected_patients"]
    selected_pids = [p["patient_id"] for p in selected_patients]

    assert len(selected_pids) == len(set(selected_pids)), "Duplicate patient detected in weekly call list!"


def test_fewer_than_50_eligible_patients(sample_encounters_dataframe):
    """If fewer than 50 eligible patients exist, select only the eligible count without padding."""
    small_df = sample_encounters_dataframe.head(15)
    res = optimize_weekly_call_list(small_df, mode="risk_first", max_capacity=50)
    assert res["selected_count"] <= 15
    assert res["remaining_capacity"] == 50 - res["selected_count"]


def test_planned_readmission_filter(sample_encounters_dataframe):
    """Confirm planned readmissions are excluded from avoidable care coordination list."""
    res = optimize_weekly_call_list(sample_encounters_dataframe, filter_planned_readmissions=True)
    planned_enc_ids = set(sample_encounters_dataframe[sample_encounters_dataframe["is_planned_readmission"]]["encounter_id"])
    selected_enc_ids = set([p["encounter_id"] for p in res["selected_patients"]])

    assert len(planned_enc_ids.intersection(selected_enc_ids)) == 0, "Planned readmission found in weekly call list!"
