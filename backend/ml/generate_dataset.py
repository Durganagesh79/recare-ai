"""
ReCare AI - Synthetic Dataset Generator
Generates reproducible synthetic hospital discharge encounters with realistic clinical
characteristics, deliberate data imperfections, and hidden 30-day readmission outcomes.

DISCLAIMER: This dataset contains synthetic data generated for educational, research,
and hackathon demonstration purposes. It does not contain actual patient health information (PHI).
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Diagnosis code definitions with ICD-10 standard, legacy ICD-9 variations, and clinical condition names
DIAGNOSIS_DEFINITIONS = [
    {
        "condition": "Heart Failure",
        "standard_icd10": "I50.9",
        "variants": ["I50.9", "I509", "428.0", "i50.9", "I50.22", "428.1"],
        "base_weight": 0.20,
        "risk_multiplier": 1.45,
    },
    {
        "condition": "COPD / Chronic Lower Respiratory",
        "standard_icd10": "J44.1",
        "variants": ["J44.1", "J441", "496", "j44.1", "J44.9"],
        "base_weight": 0.16,
        "risk_multiplier": 1.35,
    },
    {
        "condition": "Acute Myocardial Infarction",
        "standard_icd10": "I21.0",
        "variants": ["I21.0", "I210", "410.9", "I21.9", "410.0"],
        "base_weight": 0.12,
        "risk_multiplier": 1.25,
    },
    {
        "condition": "Pneumonia",
        "standard_icd10": "J18.9",
        "variants": ["J18.9", "J189", "486", "j18.9", "J15.9"],
        "base_weight": 0.14,
        "risk_multiplier": 1.20,
    },
    {
        "condition": "Diabetes with Complications",
        "standard_icd10": "E11.65",
        "variants": ["E11.65", "E1165", "250.00", "E11.9", "250.02"],
        "base_weight": 0.13,
        "risk_multiplier": 1.18,
    },
    {
        "condition": "Sepsis",
        "standard_icd10": "A41.9",
        "variants": ["A41.9", "A419", "995.91", "a41.9", "A41.0"],
        "base_weight": 0.10,
        "risk_multiplier": 1.40,
    },
    {
        "condition": "Cerebrovascular Disease / Stroke",
        "standard_icd10": "I63.9",
        "variants": ["I63.9", "I639", "434.91", "I63.4"],
        "base_weight": 0.08,
        "risk_multiplier": 1.15,
    },
    {
        "condition": "Orthopedic / Joint Replacement",
        "standard_icd10": "Z96.651",
        "variants": ["Z96.651", "Z96651", "V43.64", "M16.1"],
        "base_weight": 0.07,
        "risk_multiplier": 0.75,
    },
]

DATA_DICTIONARY = {
    "encounter_id": "Unique identifier for hospital discharge encounter (e.g. ENC-10001).",
    "patient_id": "Unique patient identifier (e.g. PT-10001). Patients can have multiple encounters.",
    "age": "Patient age in years at discharge (18-95).",
    "sex": "Biological sex: Male, Female, or Other/Unknown.",
    "payer_type": "Primary health coverage: Medicare, Medicaid, Commercial, or Uninsured/Self-pay.",
    "primary_diagnosis_code": "Raw primary diagnosis code (ICD-10 or legacy ICD-9, with realistic formatting variance).",
    "condition_name": "Standardized primary clinical condition name.",
    "secondary_diagnoses_count": "Number of documented co-morbidities / secondary diagnoses (0-14).",
    "length_of_stay": "Inpatient length of stay in days (1-25).",
    "prior_admissions": "Total lifetime prior inpatient admissions recorded (0-10).",
    "prior_admissions_6m": "Number of inpatient admissions in the preceding 6 months (0-6).",
    "num_procedures": "Number of surgical or diagnostic procedures performed during encounter (0-7).",
    "discharge_disposition": "Discharge destination: Home, Home Health Care, Skilled Nursing Facility (SNF), Inpatient Rehabilitation, Against Medical Advice (AMA), Hospice.",
    "medication_count": "Number of active prescription medications prescribed at discharge (1-30).",
    "hemoglobin": "Laboratory blood hemoglobin in g/dL (normal 12.0-16.5; ~15% deliberate missingness).",
    "serum_creatinine": "Laboratory serum creatinine in mg/dL (normal 0.6-1.2; elevated in renal impairment; ~15% missingness).",
    "sodium": "Laboratory serum sodium in mEq/L (normal 135-145; ~15% missingness).",
    "bun": "Laboratory blood urea nitrogen in mg/dL (normal 7-20; ~15% missingness).",
    "glucose": "Laboratory blood glucose in mg/dL (normal 70-125; ~15% missingness).",
    "discharge_date": "Date of hospital discharge (YYYY-MM-DD).",
    "follow_up_scheduled": "Whether a post-discharge follow-up appointment was confirmed prior to discharge (True/False/Missing).",
    "is_planned_readmission": "Flag indicating if encounter is an intentionally planned admission (e.g. scheduled staging surgery or chemo cycle). Policy excludes these from avoidable penalties.",
    "readmitted_30d": "Ground truth target (0=No, 1=Yes) for all-cause 30-day readmission. Strictly hidden during feature prediction.",
}


def generate_synthetic_discharge_dataset(
    num_records: int = 25000,
    random_seed: int = 42,
    output_dir: str = "data/processed",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate synthetic hospital discharge records with deliberate real-world imperfections:
    - 15% realistic missing laboratory measurements
    - Inconsistent diagnosis code formats (ICD-10 vs legacy ICD-9, punctuation variance)
    - Repeated patient IDs across encounters (~17,500 unique patients for 25,000 records)
    - Small fraction of duplicate encounter records for deduplication testing (~0.5%)
    - Explicit planned readmissions flag
    - Realistic calibrated 30-day readmission outcome (approx 19.5% prevalence)
    """
    np.random.seed(random_seed)
    logger.info(f"Generating {num_records} synthetic discharge encounters (seed={random_seed})...")

    # Step 1: Assign patient IDs (simulate readmissions / recurring patients)
    # Approx 70% unique patients, creating multi-encounter histories for ~30%
    num_unique_patients = int(num_records * 0.70)
    all_patient_ids = [f"PT-{10000 + i}" for i in range(num_unique_patients)]
    
    # Skewed encounter assignment: some patients have 1, some 2, 3, or 4 encounters
    patient_weights = np.random.pareto(a=2.5, size=num_unique_patients) + 0.5
    patient_weights /= patient_weights.sum()
    assigned_patients = np.random.choice(all_patient_ids, size=num_records, replace=True, p=patient_weights)

    # Step 2: Demographics correlated with patient ID for consistency
    patient_demographics = {}
    sexes = ["Male", "Female", "Other/Unknown"]
    sex_probs = [0.49, 0.49, 0.02]
    
    for pid in all_patient_ids:
        # Age distribution skewed older for hospital inpatient population
        age = int(np.clip(np.random.normal(loc=66, scale=14), 18, 96))
        sex = np.random.choice(sexes, p=sex_probs)
        
        # Payer type correlated with age
        if age >= 65:
            payer = np.random.choice(
                ["Medicare", "Commercial", "Medicaid", "Uninsured/Self-pay"],
                p=[0.82, 0.12, 0.04, 0.02],
            )
        else:
            payer = np.random.choice(
                ["Commercial", "Medicaid", "Medicare", "Uninsured/Self-pay"],
                p=[0.55, 0.28, 0.09, 0.08],
            )
        patient_demographics[pid] = {"age": age, "sex": sex, "payer_type": payer}

    # Step 3: Encounter-level features
    ages = []
    sex_list = []
    payers = []
    
    for pid in assigned_patients:
        demo = patient_demographics[pid]
        # Allow slight age progression if multiple encounters
        ages.append(demo["age"])
        sex_list.append(demo["sex"])
        payers.append(demo["payer_type"])

    # Diagnosis selection
    diag_weights = np.array([d["base_weight"] for d in DIAGNOSIS_DEFINITIONS])
    diag_weights /= diag_weights.sum()
    selected_diag_idx = np.random.choice(len(DIAGNOSIS_DEFINITIONS), size=num_records, p=diag_weights)

    raw_diagnosis_codes = []
    condition_names = []
    diag_risk_mults = []

    for idx in selected_diag_idx:
        diag = DIAGNOSIS_DEFINITIONS[idx]
        condition_names.append(diag["condition"])
        diag_risk_mults.append(diag["risk_multiplier"])
        # Deliberate inconsistency: pick from variants (some without dot, some ICD-9, lowercase, etc.)
        variant = np.random.choice(diag["variants"])
        # Occasionally add trailing space
        if np.random.rand() < 0.05:
            variant = variant + " "
        raw_diagnosis_codes.append(variant)

    # Length of stay: Gamma distribution, right-skewed, mean ~4.5 days
    los = np.clip(np.random.gamma(shape=2.5, scale=1.8, size=num_records).round().astype(int), 1, 28)

    # Prior admissions
    prior_admissions_total = np.random.negative_binomial(n=1, p=0.45, size=num_records)
    prior_admissions_total = np.clip(prior_admissions_total, 0, 10)
    
    # Prior admissions in last 6 months must be <= total prior admissions
    prior_admissions_6m = [
        int(np.random.binomial(n=tot, p=0.75)) if tot > 0 else 0
        for tot in prior_admissions_total
    ]
    prior_admissions_6m = np.array(prior_admissions_6m)

    # Secondary diagnoses count (comorbidities)
    secondary_diag_count = np.clip(np.random.poisson(lam=4.2, size=num_records), 0, 14)

    # Number of procedures
    num_procedures = np.clip(np.random.poisson(lam=1.3, size=num_records), 0, 7)

    # Discharge disposition
    dispositions = [
        "Home",
        "Home Health Care",
        "Skilled Nursing Facility (SNF)",
        "Inpatient Rehabilitation",
        "Against Medical Advice (AMA)",
        "Hospice",
    ]
    disp_probs = [0.58, 0.19, 0.14, 0.05, 0.025, 0.015]
    discharge_dispositions = np.random.choice(dispositions, size=num_records, p=disp_probs)

    # Medication count: correlated with secondary diagnoses and age
    med_count = np.clip(
        (np.random.normal(loc=9.0, scale=4.0, size=num_records) + secondary_diag_count * 0.6).round().astype(int),
        1,
        32,
    )

    # Labs generation with realistic ranges and clinical correlations
    # Hemoglobin (g/dL): lower in anemia, chronic disease
    hemoglobin = np.clip(np.random.normal(loc=13.2, scale=2.1, size=num_records), 6.5, 18.5).round(1)
    
    # Serum Creatinine (mg/dL): lognormal, elevated in CKD
    serum_creatinine = np.clip(np.random.lognormal(mean=0.1, sigma=0.45, size=num_records), 0.4, 7.5).round(2)
    
    # Sodium (mEq/L)
    sodium = np.clip(np.random.normal(loc=138.5, scale=4.0, size=num_records), 118, 154).round(1)
    
    # BUN (mg/dL)
    bun = np.clip(np.random.normal(loc=18.0, scale=11.0, size=num_records), 5, 88).round(1)
    
    # Glucose (mg/dL)
    glucose = np.clip(np.random.normal(loc=125.0, scale=45.0, size=num_records), 55, 450).round(1)

    # Introduce deliberate ~15% missingness in labs
    missing_lab_mask = np.random.rand(num_records) < 0.15
    hemoglobin = np.where(missing_lab_mask | (np.random.rand(num_records) < 0.08), np.nan, hemoglobin)
    serum_creatinine = np.where(missing_lab_mask | (np.random.rand(num_records) < 0.06), np.nan, serum_creatinine)
    sodium = np.where(missing_lab_mask | (np.random.rand(num_records) < 0.07), np.nan, sodium)
    bun = np.where(missing_lab_mask | (np.random.rand(num_records) < 0.09), np.nan, bun)
    glucose = np.where(missing_lab_mask | (np.random.rand(num_records) < 0.08), np.nan, glucose)

    # Discharge dates over past 9 months
    start_date = datetime(2026, 1, 1)
    date_offsets = np.random.randint(0, 270, size=num_records)
    discharge_dates = [
        (start_date + timedelta(days=int(offset))).strftime("%Y-%m-%d")
        for offset in date_offsets
    ]

    # Follow-up appointment scheduled: ~60% True, 36% False, 4% Missing (None)
    follow_up_rand = np.random.rand(num_records)
    follow_up_scheduled = []
    for r in follow_up_rand:
        if r < 0.04:
            follow_up_scheduled.append(None)
        elif r < 0.64:
            follow_up_scheduled.append(True)
        else:
            follow_up_scheduled.append(False)

    # Planned readmission indicator (~3.5% of records represent planned admissions)
    is_planned_readmission = (np.random.rand(num_records) < 0.035).astype(bool)

    # Encounter IDs
    encounter_ids = [f"ENC-{100000 + i}" for i in range(num_records)]

    # Compute Ground Truth 30-day Readmission Risk Probability (Latent clinical logistic model)
    # Baseline log-odds adjusted to yield realistic ~20-22% 30-day hospital readmission rate
    log_odds = -3.25

    # Age effect: +0.015 per year over 50
    log_odds += (np.array(ages) - 50) * 0.015

    # Prior admissions in 6m is one of the strongest clinical predictors
    log_odds += prior_admissions_6m * 0.42
    log_odds += (prior_admissions_total - prior_admissions_6m) * 0.08

    # Length of stay
    log_odds += np.log1p(los) * 0.28

    # Medication polypharmacy
    log_odds += (med_count - 8) * 0.035

    # Secondary diagnoses
    log_odds += secondary_diag_count * 0.05

    # Procedures (slight protective effect or complex depending on count)
    log_odds += (num_procedures - 1) * 0.04

    # Diagnosis condition risk multiplier
    log_odds += np.log(np.array(diag_risk_mults))

    # Discharge disposition risk adjustments
    disp_odds_map = {
        "Home": -0.25,
        "Home Health Care": 0.15,
        "Skilled Nursing Facility (SNF)": 0.45,
        "Inpatient Rehabilitation": 0.20,
        "Against Medical Advice (AMA)": 0.85,
        "Hospice": -1.8,
    }
    disp_effects = np.array([disp_odds_map.get(d, 0.0) for d in discharge_dispositions])
    log_odds += disp_effects

    # Payer effect
    payer_odds_map = {
        "Medicare": 0.10,
        "Medicaid": 0.25,
        "Commercial": -0.15,
        "Uninsured/Self-pay": 0.20,
    }
    payer_effects = np.array([payer_odds_map.get(p, 0.0) for p in payers])
    log_odds += payer_effects

    # Lab abnormalities risk contributions (using imputed temporary values for risk score calculation)
    creat_temp = np.nan_to_num(serum_creatinine, nan=1.0)
    log_odds += np.where(creat_temp > 1.5, (creat_temp - 1.5) * 0.35, 0.0)

    na_temp = np.nan_to_num(sodium, nan=138.0)
    log_odds += np.where(na_temp < 132, 0.40, 0.0)

    hb_temp = np.nan_to_num(hemoglobin, nan=13.0)
    log_odds += np.where(hb_temp < 10.0, 0.30, 0.0)

    # Missing lab indicator itself has slight informative risk in acute settings
    log_odds += np.where(missing_lab_mask, 0.12, 0.0)

    # Follow-up appointment protective effect
    followup_arr = np.array([1 if f is True else (0 if f is False else 0.5) for f in follow_up_scheduled])
    log_odds -= followup_arr * 0.25

    # Calculate actual probability through sigmoid
    true_probabilities = 1.0 / (1.0 + np.exp(-log_odds))

    # Generate binary readmission outcomes
    readmitted_30d = (np.random.rand(num_records) < true_probabilities).astype(int)

    # Planned readmissions are usually treated separately in hospital quality measures
    # Ensure planned readmission indicator is recorded accurately
    readmitted_30d[is_planned_readmission] = 1

    # Assemble raw DataFrame
    df = pd.DataFrame({
        "encounter_id": encounter_ids,
        "patient_id": assigned_patients,
        "age": ages,
        "sex": sex_list,
        "payer_type": payers,
        "primary_diagnosis_code": raw_diagnosis_codes,
        "condition_name": condition_names,
        "secondary_diagnoses_count": secondary_diag_count,
        "length_of_stay": los,
        "prior_admissions": prior_admissions_total,
        "prior_admissions_6m": prior_admissions_6m,
        "num_procedures": num_procedures,
        "discharge_disposition": discharge_dispositions,
        "medication_count": med_count,
        "hemoglobin": hemoglobin,
        "serum_creatinine": serum_creatinine,
        "sodium": sodium,
        "bun": bun,
        "glucose": glucose,
        "discharge_date": discharge_dates,
        "follow_up_scheduled": follow_up_scheduled,
        "is_planned_readmission": is_planned_readmission,
        "readmitted_30d": readmitted_30d,
    })

    # Introduce deliberate ~0.5% duplicate encounters (near-duplicates or exact repeats)
    num_duplicates = int(num_records * 0.005)  # ~125 records
    dup_indices = np.random.choice(num_records, size=num_duplicates, replace=False)
    duplicates = df.iloc[dup_indices].copy()
    # Append duplicates to dataframe to test deduplication pipeline
    df_with_dups = pd.concat([df, duplicates], ignore_index=True)

    # Shuffle the final dataset
    df_final = df_with_dups.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)

    # Generate Data Quality Summary Report
    data_quality_report = {
        "total_records_generated": len(df_final),
        "unique_encounters": df_final["encounter_id"].nunique(),
        "duplicate_encounter_count": len(df_final) - df_final["encounter_id"].nunique(),
        "unique_patients": df_final["patient_id"].nunique(),
        "patients_with_multiple_encounters": int((df_final.groupby("patient_id")["encounter_id"].count() > 1).sum()),
        "readmission_rate_overall": float(round(df_final["readmitted_30d"].mean(), 4)),
        "planned_readmission_count": int(df_final["is_planned_readmission"].sum()),
        "missing_values_by_column": {
            col: int(df_final[col].isna().sum()) for col in df_final.columns if df_final[col].isna().sum() > 0
        },
        "missing_percentage_by_column": {
            col: float(round(df_final[col].isna().mean() * 100, 2)) for col in df_final.columns if df_final[col].isna().sum() > 0
        },
        "diagnosis_condition_distribution": df_final["condition_name"].value_counts().to_dict(),
        "payer_distribution": df_final["payer_type"].value_counts().to_dict(),
        "discharge_disposition_distribution": df_final["discharge_disposition"].value_counts().to_dict(),
    }

    # Save dataset and artifacts if output directory is provided
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "synthetic_discharges.csv")
    df_final.to_csv(csv_path, index=False)
    logger.info(f"Saved synthetic dataset with {len(df_final)} records to {csv_path}")

    # Save Data Quality Report & Dictionary
    quality_json_path = os.path.join(output_dir, "data_quality_report.json")
    with open(quality_json_path, "w") as f:
        json.dump(data_quality_report, f, indent=2)

    dict_json_path = os.path.join(output_dir, "data_dictionary.json")
    with open(dict_json_path, "w") as f:
        json.dump(DATA_DICTIONARY, f, indent=2)

    logger.info(f"Overall synthetic readmission rate: {data_quality_report['readmission_rate_overall'] * 100:.2f}%")
    logger.info(f"Duplicate encounters: {data_quality_report['duplicate_encounter_count']}")
    logger.info(f"Unique patients: {data_quality_report['unique_patients']}")

    return df_final, data_quality_report


if __name__ == "__main__":
    df, report = generate_synthetic_discharge_dataset(num_records=25000, random_seed=42)
    print("\nDataset Generation Complete!")
    print(f"Total Rows: {len(df)}")
    print(f"Readmission Rate: {report['readmission_rate_overall']*100:.2f}%")
    print(f"Missing Values: {report['missing_values_by_column']}")
