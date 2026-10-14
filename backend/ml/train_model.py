"""
ReCare AI - Machine Learning Training Pipeline
Trains baseline and candidate gradient-boosting classifiers, performs probability calibration,
evaluates Brier score and Expected Calibration Error (ECE), and serializes the production model.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    brier_score_loss,
    precision_recall_curve,
)

from backend.ml.preprocessing import (
    deduplicate_encounters,
    patient_aware_train_test_split,
    create_preprocessor,
    EXCLUDED_FROM_FEATURES,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def compute_expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute Expected Calibration Error (ECE) and reliability diagram bins:
    ECE = sum_{b=1}^B (N_b / N) * |mean_pred_b - empirical_pos_b|
    """
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_assignments = np.digitize(y_prob, bin_edges) - 1
    # Clip edge cases where probability == 1.0 into last bin
    bin_assignments = np.clip(bin_assignments, 0, n_bins - 1)

    total_samples = len(y_true)
    ece = 0.0
    bins_data = []

    for b in range(n_bins):
        mask = bin_assignments == b
        count = int(np.sum(mask))
        if count > 0:
            avg_pred = float(np.mean(y_prob[mask]))
            empirical_rate = float(np.mean(y_true[mask]))
            weight = count / total_samples
            ece += weight * abs(empirical_rate - avg_pred)
            bins_data.append({
                "bin_index": b,
                "bin_range": f"{bin_edges[b]:.1f}-{bin_edges[b+1]:.1f}",
                "count": count,
                "mean_predicted": round(avg_pred, 4),
                "fraction_positive": round(empirical_rate, 4),
                "absolute_gap": round(abs(empirical_rate - avg_pred), 4),
            })
        else:
            bins_data.append({
                "bin_index": b,
                "bin_range": f"{bin_edges[b]:.1f}-{bin_edges[b+1]:.1f}",
                "count": 0,
                "mean_predicted": round((bin_edges[b] + bin_edges[b+1]) / 2, 4),
                "fraction_positive": 0.0,
                "absolute_gap": 0.0,
            })

    return round(float(ece), 4), {"n_bins": n_bins, "bins": bins_data}


def train_readmission_models(
    dataset_path: str = "data/processed/synthetic_discharges.csv",
    models_dir: str = "backend/models",
    random_seed: int = 42,
) -> Dict[str, Any]:
    """
    Train, compare, calibrate, and save the hospital readmission model pipeline.
    """
    logger.info(f"Loading dataset from {dataset_path}...")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}. Run generate_dataset.py first.")

    raw_df = pd.read_csv(dataset_path)
    logger.info(f"Loaded {len(raw_df)} records.")

    # 1. Deduplicate encounters
    df, dups_removed = deduplicate_encounters(raw_df)

    # Policy: Exclude planned readmissions from predictive training of avoidable readmission risk
    # (Documented hospital policy: planned chemotherapy/procedures are expected and not preventable penalty targets)
    df_predictive = df[~df["is_planned_readmission"]].copy().reset_index(drop=True)
    logger.info(f"Retained {len(df_predictive)} unplanned encounters after planned readmission policy.")

    # 2. Patient-group-aware split
    train_df, val_df, test_df = patient_aware_train_test_split(
        df_predictive,
        test_size=0.20,
        val_size=0.15,
        random_state=random_seed,
    )

    # Save holdout test split for independent evaluation and audit
    test_path = "data/processed/test_split.csv"
    test_df.to_csv(test_path, index=False)
    logger.info(f"Saved independent patient-isolated test set ({len(test_df)} records) to {test_path}")

    # Separate features and target
    X_train = train_df.drop(columns=[col for col in EXCLUDED_FROM_FEATURES if col in train_df.columns])
    y_train = train_df["readmitted_30d"].values

    X_val = val_df.drop(columns=[col for col in EXCLUDED_FROM_FEATURES if col in val_df.columns])
    y_val = val_df["readmitted_30d"].values

    X_test = test_df.drop(columns=[col for col in EXCLUDED_FROM_FEATURES if col in test_df.columns])
    y_test = test_df["readmitted_30d"].values

    # 3. Fit Preprocessing Pipeline
    preprocessor, numeric_cols = create_preprocessor()
    logger.info("Fitting preprocessing pipeline on training data...")
    X_train_trans = preprocessor.fit_transform(X_train)
    X_val_trans = preprocessor.transform(X_val)
    X_test_trans = preprocessor.transform(X_test)

    # 4. Train Candidate Models
    logger.info("Training Candidate Models...")

    # Candidate 1: Logistic Regression baseline
    baseline_lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_seed)
    baseline_lr.fit(X_train_trans, y_train)
    val_probs_lr = baseline_lr.predict_proba(X_val_trans)[:, 1]
    auc_pr_lr = float(average_precision_score(y_val, val_probs_lr))
    roc_auc_lr = float(roc_auc_score(y_val, val_probs_lr))
    brier_lr = float(brier_score_loss(y_val, val_probs_lr))
    ece_lr, _ = compute_expected_calibration_error(y_val, val_probs_lr)

    logger.info(f"Baseline Logistic Regression -> Val AUC-PR: {auc_pr_lr:.4f}, ROC-AUC: {roc_auc_lr:.4f}, Brier: {brier_lr:.4f}, ECE: {ece_lr:.4f}")

    # Candidate 2: HistGradientBoostingClassifier (Tabular Gradient Boosting)
    hgb = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=random_seed,
    )
    hgb.fit(X_train_trans, y_train)
    val_probs_hgb_raw = hgb.predict_proba(X_val_trans)[:, 1]
    auc_pr_hgb_raw = float(average_precision_score(y_val, val_probs_hgb_raw))
    roc_auc_hgb_raw = float(roc_auc_score(y_val, val_probs_hgb_raw))
    brier_hgb_raw = float(brier_score_loss(y_val, val_probs_hgb_raw))
    ece_hgb_raw, _ = compute_expected_calibration_error(y_val, val_probs_hgb_raw)

    logger.info(f"Raw HistGradientBoosting -> Val AUC-PR: {auc_pr_hgb_raw:.4f}, ROC-AUC: {roc_auc_hgb_raw:.4f}, Brier: {brier_hgb_raw:.4f}, ECE: {ece_hgb_raw:.4f}")

    # 5. Probability Calibration
    # Calibrate HistGradientBoosting using 3-fold cross-validation to guarantee calibrated probabilities
    logger.info("Calibrating probability outputs using 3-fold cross-validation...")
    calibrated_hgb = CalibratedClassifierCV(
        estimator=HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            random_state=random_seed,
        ),
        cv=3,
        method="sigmoid",
    )
    calibrated_hgb.fit(X_train_trans, y_train)

    # Evaluate on holdout test set to compare uncalibrated vs calibrated
    test_probs_raw = hgb.predict_proba(X_test_trans)[:, 1]
    test_probs_calibrated = calibrated_hgb.predict_proba(X_test_trans)[:, 1]

    ece_test_raw, _ = compute_expected_calibration_error(y_test, test_probs_raw)
    ece_test_calibrated, cal_diagram_data = compute_expected_calibration_error(y_test, test_probs_calibrated)
    brier_test_raw = float(brier_score_loss(y_test, test_probs_raw))
    brier_test_calibrated = float(brier_score_loss(y_test, test_probs_calibrated))
    auc_pr_test = float(average_precision_score(y_test, test_probs_calibrated))
    roc_auc_test = float(roc_auc_score(y_test, test_probs_calibrated))

    logger.info(
        f"Holdout Test Results: Raw ECE={ece_test_raw:.4f} -> Calibrated ECE={ece_test_calibrated:.4f} | "
        f"Raw Brier={brier_test_raw:.4f} -> Calibrated Brier={brier_test_calibrated:.4f} | "
        f"Test AUC-PR={auc_pr_test:.4f}, ROC-AUC={roc_auc_test:.4f}"
    )

    # Extract transformed feature names
    cat_encoder = preprocessor.named_steps["column_transforms"].named_transformers_["cat"].named_steps["onehot"]
    cat_features_out = list(cat_encoder.get_feature_names_out())
    all_feature_names = numeric_cols + cat_features_out

    # 6. Build Final Production Pipeline
    # Encapsulate preprocessing and calibrated model into a single pipeline object
    final_pipeline = {
        "preprocessor": preprocessor,
        "base_model": hgb,
        "calibrated_model": calibrated_hgb,
        "baseline_model": baseline_lr,
        "feature_names": all_feature_names,
    }

    model_version = "v1.2.0-calibrated-histgb"
    os.makedirs(models_dir, exist_ok=True)
    model_artifact_path = os.path.join(models_dir, "recare_readmission_model.joblib")
    joblib.dump(final_pipeline, model_artifact_path)
    logger.info(f"Saved complete model artifact to {model_artifact_path}")

    # Save comprehensive Model Metadata
    metadata = {
        "model_version": model_version,
        "model_architecture": "Calibrated HistGradientBoostingClassifier (Isotonic)",
        "baseline_architecture": "L2-Regularized Balanced Logistic Regression",
        "created_at": datetime.now().isoformat(),
        "random_seed": random_seed,
        "dataset_used": dataset_path,
        "total_records_processed": len(raw_df),
        "unplanned_records_trained": len(df_predictive),
        "train_samples": len(train_df),
        "validation_samples": len(val_df),
        "test_samples": len(test_df),
        "test_prevalence": round(float(y_test.mean()), 4),
        "metrics_summary": {
            "test_auc_pr": round(auc_pr_test, 4),
            "test_roc_auc": round(roc_auc_test, 4),
            "test_brier_score_raw": round(brier_test_raw, 4),
            "test_brier_score_calibrated": round(brier_test_calibrated, 4),
            "test_expected_calibration_error_raw": round(ece_test_raw, 4),
            "test_expected_calibration_error_calibrated": round(ece_test_calibrated, 4),
            "baseline_val_auc_pr": round(auc_pr_lr, 4),
            "baseline_val_roc_auc": round(roc_auc_lr, 4),
            "baseline_val_brier": round(brier_lr, 4),
            "baseline_val_ece": round(ece_lr, 4),
        },
        "calibration_bins": cal_diagram_data["bins"],
        "feature_names": all_feature_names,
    }

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved model metadata to {metadata_path}")

    return metadata


if __name__ == "__main__":
    meta = train_readmission_models()
    print("\nModel Training Complete!")
    print(f"Model Version: {meta['model_version']}")
    print(f"Test AUC-PR: {meta['metrics_summary']['test_auc_pr']}")
    print(f"Calibrated ECE: {meta['metrics_summary']['test_expected_calibration_error_calibrated']}")
