"""
ReCare AI - Unit Tests for Synthetic Dataset Generation
"""

import pytest
import pandas as pd
from backend.ml.generate_dataset import generate_synthetic_discharge_dataset, DATA_DICTIONARY


def test_dataset_reproducibility():
    """Verify that using the same seed produces identical datasets."""
    df1, _ = generate_synthetic_discharge_dataset(num_records=500, random_seed=99)
    df2, _ = generate_synthetic_discharge_dataset(num_records=500, random_seed=99)
    assert len(df1) == len(df2)
    assert df1["encounter_id"].equals(df2["encounter_id"])
    assert df1["readmitted_30d"].equals(df2["readmitted_30d"])


def test_dataset_deliberate_imperfections():
    """Verify presence of deliberate real-world data flaws: missing labs, duplicates, planned flags."""
    df, report = generate_synthetic_discharge_dataset(num_records=1000, random_seed=42)
    # 1. Deliberate missingness in labs (~15%)
    assert df["hemoglobin"].isna().sum() > 0
    assert df["serum_creatinine"].isna().sum() > 0
    # 2. Deliberate duplicate encounters
    assert report["duplicate_encounter_count"] > 0
    # 3. Planned readmissions flag present
    assert "is_planned_readmission" in df.columns
    assert df["is_planned_readmission"].sum() > 0
    # 4. Data dictionary covers all primary columns
    assert "encounter_id" in DATA_DICTIONARY
    assert "readmitted_30d" in DATA_DICTIONARY
