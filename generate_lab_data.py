"""
Generate realistic analytical laboratory data for QC pipeline testing.
Simulates HPLC/UV-Vis/GC measurement data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

n_samples = 200
analytes = ["Paracetamol", "Caffeine", "Ibuprofen", "Aspirin"]
instruments = ["HPLC-01", "HPLC-02", "UV-Vis-01", "GC-01"]
analysts = ["MN", "AB", "CD", "EF"]
batches = [f"BATCH-{i:03d}" for i in range(1, 11)]

true_concentrations = {
    "Paracetamol": 250.0,
    "Caffeine": 100.0,
    "Ibuprofen": 200.0,
    "Aspirin": 150.0,
}

records = []
start_date = datetime(2025, 1, 1)

for i in range(n_samples):
    analyte = np.random.choice(analytes)
    true_conc = true_concentrations[analyte]

    if np.random.random() < 0.05:
        measured = true_conc * np.random.uniform(0.7, 1.3)
    else:
        measured = true_conc * np.random.normal(1.0, 0.02)

    replicates = [
        measured * np.random.normal(1.0, 0.01) for _ in range(3)
    ]

    records.append({
        "sample_id": f"SAMPLE-{i+1:04d}",
        "batch": np.random.choice(batches),
        "date": start_date + timedelta(days=np.random.randint(0, 90)),
        "instrument": np.random.choice(instruments),
        "analyst": np.random.choice(analysts),
        "analyte": analyte,
        "expected_concentration": true_conc,
        "replicate_1": round(replicates[0], 2),
        "replicate_2": round(replicates[1], 2),
        "replicate_3": round(replicates[2], 2),
    })

df = pd.DataFrame(records)

missing_indices = np.random.choice(df.index, 8, replace=False)
df.loc[missing_indices, "replicate_2"] = np.nan

dup_row = df.iloc[5].copy()
df = pd.concat([df, pd.DataFrame([dup_row])], ignore_index=True)

df.to_csv("raw_lab_data.csv", index=False)
print(f"Generated {len(df)} records -> raw_lab_data.csv")
print(df.head(10))
