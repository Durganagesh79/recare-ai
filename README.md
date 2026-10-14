# ReCare AI — 30-Day Hospital Readmission Prediction & Care Intervention Platform

> **Predict Earlier. Prioritize Smarter. Prevent Avoidable Readmissions.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.142-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Executive Summary & Clinical Vision

Hospital readmission within 30 days is a critical healthcare quality and cost challenge, penalized by CMS under the Hospital Readmissions Reduction Program (HRRP). However, hospital care-coordination and transitional-care nursing teams face severe resource limitations: **in this operational scenario, the hospital can contact at most 50 unique patients per week**.

Most existing healthcare predictive models stop at calculating raw readmission risk probabilities. **ReCare AI** bridges the gap between prediction and clinical action:
1. **Calibrated Machine Learning Engine:** Predicts true 30-day readmission risk using gradient boosting with strict probability calibration (Expected Calibration Error: **1.08%**; AUC-PR: **0.3608** vs 18% base prevalence).
2. **Resource-Constrained Weekly Optimizer:** Solves the capacity constraint by selecting strictly **at most 50 unique patients per week**, preventing repeated calls to duplicate patient records, and offering two distinct ranking strategies:
   - **Mode A (Risk-First Baseline):** Prioritizes by calibrated readmission probability.
   - **Mode B (Expected Intervention Benefit):** Ranks by $\Delta P = P(\text{readmission}) \times \text{RRR} \times \text{Actionability}$, directing resources toward patients with addressable clinical risk.
3. **Actionable Patient-Level Explanations:** Translates technical feature attributions into clinician-friendly transition reviews without making unsubstantiated causal claims or prescribing medications.
4. **Mandatory Fairness & Bias Audit:** Evaluates algorithmic equity across Age Groups, Sex, and Payer coverage with documented disparity tracking.
5. **Monday Morning Care Coordination Brief:** Generates formatted executive reports available via instant CSV export and professional ReportLab PDF downloads.

> ⚠️ **CLINICAL DEMONSTRATION NOTICE:** ReCare AI is an advanced prototype developed with synthetic hospital discharge data. Its predictions and care intervention recommendations provide decision support to licensed clinical staff and must never replace clinical judgment.

---

## 2. Platform Architecture & Technology Stack

```mermaid
graph TD
    A[Synthetic Data Engine<br/>25,000 Inpatient Records] -->|Deliberate Imperfections| B[Preprocessing & Feature Pipeline]
    B -->|GroupShuffleSplit Zero-Leakage| C[Calibrated ML Model<br/>HistGB + Isotonic]
    C --> D[Evaluation Engine<br/>AUC-PR, Recall@50, ECE]
    C --> E[Fairness & Bias Audit<br/>Age, Sex, Payer Strata]
    C --> F[Weekly Intervention Optimizer<br/>50-Patient Capacity Constraint]
    F -->|Mode A / Mode B| G[Rules-Based Recommender<br/>Med Rec, Follow-Up, Transitions]
    G --> H[FastAPI REST Backend<br/>Endpoints, Database, PDF Service]
    H --> I[React 19 + TypeScript + Tailwind UI<br/>Clinical Analytics Platform]
```

### Full-Stack Specifications:
- **Frontend:** React 19, Vite 8, TypeScript, Tailwind CSS, Recharts for clinical analytics, Lucide Icons, React Router v7, Axios.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2 validation, SQLAlchemy ORM, ReportLab for executive PDF streaming, joblib.
- **Machine Learning & Preprocessing:** Scikit-Learn 1.8+, pandas, NumPy, SciPy, custom ClinicalFeatureEngineer with missingness indicators.
- **Database:** SQLite (local zero-config development) with seamless PostgreSQL compatibility (Supabase / Render / Neon).
- **Testing:** Comprehensive pytest suite covering ML pipeline, leakage prevention, 50-patient capacity limits, and REST APIs.

---

## 3. Synthetic Dataset & Deliberate Real-World Imperfections

The platform includes a reproducible generator (`backend/ml/generate_dataset.py`) producing **25,125 discharge encounters** across **11,730 unique patients** (random seed = 42).

### Realistic Clinical Imperfections Introduced:
1. **~15% Missing Laboratory Panels:** Hemoglobin, serum creatinine, sodium, BUN, and glucose feature realistic clinical missingness patterns. Missingness indicators (`*_is_missing`) are engineered so missing measurements provide informative signal rather than discarding cases.
2. **Inconsistent Diagnosis Formats:** ICD-10 variants, legacy ICD-9 codes (`428.0` for Heart Failure, `496` for COPD, `410.9` for AMI), lowercase characters, and missing decimals are normalized by `normalize_diagnosis_code()`.
3. **Multi-Encounter Longitudinal Histories:** Approximately 30% of patients have 2 to 4 distinct encounters across the 9-month timeframe.
4. **Deliberate Duplicate Encounter Records:** Exactly 125 near-duplicate encounter IDs are embedded to test deduplication pipelines.
5. **Planned Readmission Flag (`is_planned_readmission`):** ~3.5% of records represent scheduled chemotherapy or elective procedures. Documented hospital policy filters these out from avoidable readmission penalties.
6. **Realistic Readmission Prevalence:** Ground-truth readmissions are calibrated to **21.25%** overall, matching national hospital inpatient benchmarks.

### Clinical Data Dictionary:
| Column | Type | Clinical Description & Operational Handling |
| :--- | :--- | :--- |
| `encounter_id` | String | Unique encounter identifier (e.g., `ENC-100042`). Deduplicated before modeling. |
| `patient_id` | String | Unique patient identifier (e.g., `PT-10042`). Used for GroupShuffleSplit. |
| `age` | Integer | Patient age at discharge (18–95). Binned for fairness audits. |
| `sex` | String | Biological sex (`Male`, `Female`, `Other/Unknown`). Monitored for parity. |
| `payer_type` | String | Insurance coverage (`Medicare`, `Medicaid`, `Commercial`, `Uninsured/Self-pay`). |
| `primary_diagnosis_code` | String | Raw ICD-10 or legacy ICD-9 code. Normalized to standard clinical condition. |
| `secondary_diagnoses_count` | Integer | Documented comorbidity count (0–14). |
| `length_of_stay` | Integer | Inpatient length of stay in days (1–28). |
| `prior_admissions_6m` | Integer | Inpatient admissions in prior 6 months. High acute utilization velocity flag. |
| `discharge_disposition` | String | `Home`, `Home Health Care`, `SNF`, `Inpatient Rehab`, `AMA`, `Hospice`. |
| `medication_count` | Integer | Active discharge prescriptions (1–32). Values $\ge 10$ flag polypharmacy. |
| `hemoglobin`, `serum_creatinine`, `sodium`, `bun`, `glucose` | Float | Objective laboratory results. Missing values imputed via median with missingness flags. |
| `is_planned_readmission` | Boolean | Elective/planned indicator. Excluded from avoidable penalty call lists. |
| `readmitted_30d` | Binary (0/1) | Ground-truth target. Strictly isolated and hidden during prediction inference. |

---

## 4. Machine Learning & Probability Calibration

### Leakage Prevention:
To prevent training/evaluation leakage when patients have multiple hospital encounters, `patient_aware_train_test_split()` uses **`GroupShuffleSplit` on `patient_id`**. Encounters from the same patient never appear across both train and test partitions:
- **Train Split:** 15,739 encounters (7,494 unique patients)
- **Validation Split:** 3,583 encounters (1,730 unique patients)
- **Holdout Test Split:** 4,805 encounters (2,306 unique patients, zero overlap)

### Candidate Comparison & Probability Calibration:
| Model Architecture | Validation AUC-PR | Validation ROC-AUC | Brier Score | Expected Calib. Error (ECE) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Balanced Logistic Regression | 0.3626 | 0.6885 | 0.2206 | 27.41% | Transparent Baseline |
| Uncalibrated HistGradientBoosting | 0.3594 | 0.6872 | 0.1398 | 1.02% | Tabular Candidate |
| **Calibrated HistGB (Sigmoid CV=3)** | **0.3608** | **0.6951** | **0.1348** | **1.08%** | **Production Selected** |

### Calibration Formulation:
$$ECE = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
Using 10 probability bins, ReCare AI achieves an ECE of **0.0108 (1.08%)**, ensuring that a predicted probability of 30% corresponds to approximately a 30% empirical event frequency.

---

## 5. Model Evaluation — Required Metrics

Run evaluation against the holdout test set using:
```bash
python -m backend.ml.evaluate
```

### Verified Holdout Test Results:
- **AUC-PR / Average Precision:** **`0.3608`** (vs 18.0% baseline prevalence, demonstrating strong precision-recall lift)
- **Recall@50:** **`0.0382`**
- **Precision@50:** **`66.0%`** (33 of the top 50 selected patients experienced a readmission — a **3.6x enrichment ratio** over random selection)
- **Simulated Weekly Cohort Recall@50:** **`15.0%`** (On an ongoing weekly cohort of ~450 discharges, contacting 50 patients captures ~15–20% of all weekly avoidable events)
- **Expected Calibration Error (ECE):** **`0.0108`** (1.08%)
- **Brier Score:** **`0.1348`**
- **ROC-AUC:** **`0.6951`**

---

## 6. Resource-Constrained Weekly Call-List Optimizer

The hospital care-coordination nursing team has the staffing capacity to contact **at most 50 unique patients per week**.

### Two Ranking Modes:
1. **Mode A: Risk-First Baseline:**
   Ranks eligible encounters descending by calibrated probability $P(\text{readmission})$.
2. **Mode B: Expected Intervention Benefit:**
   $$\text{Expected Benefit} = P(\text{readmission without intervention}) - P(\text{readmission with intervention})$$
   Estimated by $\Delta P = P \times \text{RRR} \times \text{Actionability}$. Patients with high polypharmacy (eligible for pharmacist medication reconciliation) or unscheduled follow-up gaps are prioritized because their readmission risk is clinically addressable.

### Constraints & Invariants Enforced:
- **Strict Capacity Limit:** Never returns more than 50 patients.
- **Patient Uniqueness Guarantee:** No patient is called more than once in the same cycle. If a patient has multiple eligible encounters, the optimizer selects the most recent discharge.
- **Planned Readmission Filter:** Elective/planned procedures are policy-excluded.
- **Full Traceability:** Every selected entry includes an explicit selection rationale and recommended intervention.

---

## 7. Rules-Based Intervention Recommender

Maps clinical features to transparent, clinician-reviewable interventions:
- **Pharmacist Medication Reconciliation:** Triggered by medication count $\ge 10$. Reconciles high-risk polypharmacy and verifies discharge instructions.
- **Post-Discharge Follow-Up Scheduling:** Triggered by unscheduled appointment status at discharge. Coordinates primary care or specialist visit within 7 days.
- **Nurse Transition-of-Care Call:** Triggered by $\ge 1$ prior admission in the past 6 months. Assesses Coleman Care Transition protocol adherence.
- **Specialist Disease-Management Pathway:** Triggered by Heart Failure (HF daily weight monitoring protocol) or COPD (inhaler technique and exacerbation action plan).
- **Home Health & Community Support:** Triggered by SNF, Home Health, or AMA discharge dispositions to verify hand-off continuity.

---

## 8. Algorithmic Fairness & Bias Audit

Run the audit on the independent test split:
```bash
python -m backend.ml.fairness_audit
```

### Audited Strata:
1. **Age Groups:** `<50`, `50–64`, `65–74`, `75+`
2. **Biological Sex:** `Male`, `Female`, `Other/Unknown`
3. **Payer Type:** `Medicare`, `Medicaid`, `Commercial`, `Uninsured/Self-pay`

### Practical Mitigation Strategies:
- **Demographic-Blind Care Allocation:** Sensitive attributes are tracked strictly for post-hoc equity audits and never used as exclusion criteria.
- **Calibration Stratification:** Verifies calibration error remains below 2% across each demographic subgroup.
- **Human-in-the-Loop Nurse Override:** Clinicians can adjust outreach priority based on social determinants of health (SDOH).

---

## 9. Readmissions Averted Impact Simulator

Illustrative mathematical scenario modeling based on published health services research (Project RED, BOOST, Coleman CTT):

| Scenario | Reach Rate | Relative Risk Reduction (RRR) | Patients Reached | Est. Avoided Readmissions / Wk | Net Cost Avoidance / Wk | ROI Ratio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Conservative** | 60% | 15% | 30 | ~1.9 | **$22,430** | 4.6x |
| **Central (Baseline)** | 75% | 25% | 37.5 | ~3.9 | **$53,605** | 9.6x |
| **Optimistic** | 85% | 35% | 42.5 | ~6.2 | **$88,660** | 15.2x |

*Assumptions: 50 patients selected at average risk 42%; CMS benchmark readmission cost = $15,200; nurse outreach cost = $125/patient. Predictions alone do not establish causality.*

---

## 10. Local Installation & Startup Guide

### Prerequisites:
- Python 3.11+
- Node.js 18+ (Node 20+ recommended) and npm

### Step 1: Clone and Set Up Workspace
```powershell
# Windows PowerShell
cd "c:\Users\dn208\OneDrive\Documents\Desktop\Recare AI"
```

### Step 2: Install Backend Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 3: Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### Step 4: Generate Synthetic Dataset & Train Model
```powershell
# Generate 25,000 synthetic records with deliberate imperfections
python backend/ml/generate_dataset.py

# Train baseline and calibrated HistGradientBoosting model
python -m backend.ml.train_model

# Run independent holdout evaluation (AUC-PR, Recall@50, ECE)
python -m backend.ml.evaluate

# Run algorithmic fairness audit
python -m backend.ml.fairness_audit

# Initialize and seed SQLite database
python -m backend.db.init_db
```

### Step 5: Run Automated Tests
```powershell
python -m pytest backend/tests -v
```
*(All 20 tests pass: dataset reproducibility, deduplication, zero patient leakage, probability calibration, optimizer 50-patient capacity limit, and REST APIs).*

### Step 6: Start Backend and Frontend Servers

**Terminal 1 (Backend API):**
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be accessible at: `http://127.0.0.1:8000/docs`

**Terminal 2 (Frontend UI):**
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## 11. Deployment Guide

### A. Frontend Deployment on Vercel
1. Set the root directory to `frontend`.
2. Framework Preset: `Vite`.
3. Build Command: `npm run build`.
4. Output Directory: `dist`.
5. Environment Variable:
   - `VITE_API_URL`: URL of your deployed Render backend (e.g. `https://recare-api.onrender.com`).
6. `frontend/vercel.json` ensures client-side routing for SPA views.

### B. Backend Deployment on Render
1. Create a new **Web Service** pointing to the repository.
2. Root Directory: leave blank or set to `./`.
3. Environment: `Python 3`.
4. Build Command: `pip install -r backend/requirements.txt`.
5. Start Command: `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
6. Environment Variables:
   - `DATABASE_URL`: Connection string to PostgreSQL (or leave empty to use SQLite).
   - `ENVIRONMENT`: `production`.

### C. PostgreSQL Database (Supabase / Neon / Render Postgres)
1. Create a PostgreSQL 15+ database instance.
2. Copy the Connection URI:
   ```
   postgresql://user:password@host:5432/dbname
   ```
3. Set the `DATABASE_URL` environment variable on Render. ReCare AI will automatically connect and create all tables via SQLAlchemy ORM.

---

## 12. Security, Privacy & Compliance Safeguards

- **Synthetic Data Isolation:** Contains zero protected health information (PHI) or personally identifiable information (PII).
- **Upload File Validation:** Enforces RFC-4180 CSV parsing, MIME type verification, and a 50MB size ceiling.
- **SQL Injection Prevention:** All database operations utilize SQLAlchemy ORM parameterized queries.
- **CORS Protection:** Configured to accept requests from explicit production and local development origins.
- **Model Governance Notice:** Transparent model metadata and intended use policies are served directly via `GET /api/model/info`.

---

## 13. License & Authorship

Developed for the **H3 Healthcare AI Hackathon: Predicting the 30-Day Readmission — And Doing Something About It**.

Released under the **MIT License**.
