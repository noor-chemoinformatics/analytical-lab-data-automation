# Analytical Lab Data Automation

A Python pipeline that automates quality control of analytical laboratory data.

I built this to understand what it takes to automate a real analytical QC workflow: taking raw instrument measurements, cleaning them, applying standard QC rules, and producing a report that a lab analyst could actually use.

---

## What it does

The pipeline takes a CSV of analytical measurements and runs six steps:

1. **Import** — load the file, standardise column names, parse dates
2. **Clean** — remove duplicate sample IDs, handle missing replicates
3. **Calculate QC metrics** — mean, standard deviation, RSD%, and recovery% for each sample
4. **Flag issues** — using precision, accuracy, and Grubbs' test rules
5. **Plot** — recovery distribution, RSD distribution, control chart, QC status by instrument
6. **Report** — export an Excel workbook and a PNG dashboard

It runs with one command and produces everything in a `qc_output/` folder.

---

## Why I built it

Analytical labs deal with large volumes of data every day. QC is critical but repetitive: check each sample against expected values, look at replicate agreement, spot outliers, and document the result.

Doing that manually for hundreds of samples is slow and easy to get wrong. I wanted to see how far a Python pipeline could go in automating that — while keeping the same QC logic that a chemist would use.

---

## QC rules it applies

These are standard rules used in analytical chemistry:

- **Precision:** RSD% must be ≤ 5% across replicates
- **Accuracy:** recovery must fall between 90% and 110%
- **Outlier detection:** Grubbs' test on triplicate measurements

If a sample fails any of these, it gets flagged **REVIEW**. Otherwise it's marked **PASS**.

The thresholds are set in one place (`detect_outliers()` method) so they can be adjusted for different lab standards.

---

## Test run

I tested it on 200 simulated samples with deliberately injected quality issues: one duplicate, eight missing values, and around 5% outliers.

The pipeline:

- Removed 1 duplicate
- Reported 8 missing values
- Flagged 5 samples as REVIEW
- Marked the remaining 195 as PASS
- Reported mean recovery of 99.9% and mean RSD of 0.90%

Output: a 4-panel dashboard and a 3-sheet Excel report.

## ML anomaly detection

Alongside the rule-based QC checks, the pipeline runs an Isolation 
Forest model on the same QC metrics (RSD%, recovery%, mean measured 
value). The model learns what a "normal" QC profile looks like and 
flags samples whose combination of metrics is unusual — even if no 
single rule was violated.

On the 200-sample test run:

- 5 samples flagged by rules only
- 5 samples flagged by both rules and ML
- 5 samples flagged by ML only (missed by rule-based checks)
- 185 samples cleared by both

The Excel report includes a dedicated "ML-only Detections" sheet, 
so reviewers can see which samples the classical rules would have 
missed.

This shows how ML complements rather than replaces classical QC 
rules: rules catch known failure modes, ML catches unfamiliar ones.

## Outputs

**`qc_output/qc_report.png`** — a 4-panel dashboard:
- Recovery distribution with 90% and 110% acceptance lines
- RSD% distribution with 5% threshold
- Control chart of recovery across samples
- QC status breakdown by instrument

**`qc_output/qc_results.xlsx`** — three sheets:
- **All Results** — full dataset with QC flags
- **Flagged for Review** — only the samples that failed QC
- **Summary** — pass/review counts, mean and max RSD, mean recovery

---

## How to run it

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate test data
python generate_lab_data.py

# Run the pipeline
python lab_qc_pipeline.py

