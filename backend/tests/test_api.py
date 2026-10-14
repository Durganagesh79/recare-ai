"""
ReCare AI - End-to-End API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify health endpoint returns healthy status and model flag."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ReCare AI Backend"
    assert "model_loaded" in data


def test_dashboard_summary_endpoint():
    """Verify dashboard summary returns live aggregated KPIs and charts."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "kpi" in data
    assert "charts" in data
    assert data["kpi"]["weekly_capacity_limit"] == 50
    assert "this_weeks_care_priorities" in data


def test_patients_registry_endpoint():
    """Verify patient search and pagination."""
    response = client.get("/api/patients?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_records" in data
    assert len(data["items"]) <= 10


def test_single_prediction_endpoint():
    """Verify single prediction endpoint validates input and returns calibrated probability."""
    payload = {
        "encounter_id": "ENC-TEST-API",
        "patient_id": "PT-TEST-API",
        "age": 68,
        "sex": "Male",
        "payer_type": "Medicare",
        "primary_diagnosis_code": "I50.9",
        "secondary_diagnoses_count": 4,
        "length_of_stay": 5,
        "prior_admissions": 2,
        "prior_admissions_6m": 1,
        "num_procedures": 1,
        "discharge_disposition": "Home Health Care",
        "medication_count": 11,
        "hemoglobin": 12.0,
        "serum_creatinine": 1.4,
        "sodium": 137.0,
        "bun": 20.0,
        "glucose": 125.0,
        "follow_up_scheduled": True,
        "is_planned_readmission": False,
    }
    response = client.post("/api/predictions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_risk_probability" in data
    assert 0.0 <= data["predicted_risk_probability"] <= 1.0
    assert "top_contributing_features" in data


def test_call_list_current_and_csv_export():
    """Verify current call list retrieval and CSV download."""
    response = client.get("/api/call-list/current")
    assert response.status_code == 200
    data = response.json()
    assert data["capacity_limit"] == 50
    assert data["selected_count"] <= 50

    # Test CSV export
    csv_resp = client.get("/api/reports/call-list.csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "Priority Rank" in csv_resp.text


def test_evaluation_metrics_endpoint():
    """Verify evaluation endpoint returns primary metrics."""
    response = client.get("/api/evaluation/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "primary_metrics" in data
    assert "auc_pr" in data["primary_metrics"]
    assert "recall_at_50" in data["primary_metrics"]


def test_fairness_report_endpoint():
    """Verify fairness audit endpoint returns subgroup evaluations."""
    response = client.get("/api/fairness/report")
    assert response.status_code == 200
    data = response.json()
    assert "audited_attributes" in data
    assert "age_group" in data["audited_attributes"]
    assert "sex" in data["audited_attributes"]
    assert "payer_type" in data["audited_attributes"]
