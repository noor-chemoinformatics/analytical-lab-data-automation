# Analytical Lab Data Automation

A Python-based pipeline that automates quality control and data processing workflows in analytical chemistry laboratories. Designed to improve laboratory efficiency, standardise QC reporting, and support digitalisation of analytical data processes.

---

## Why This Project

Modern analytical laboratories — whether in cosmetics, pharmaceuticals, or materials science — generate large volumes of instrument data across multiple instruments, analysts, and batches.

Manual QC and data handling creates several problems:

- Repetitive manual processing of analytical results
- Inconsistent application of acceptance criteria
- Difficulty tracing data lineage and decisions
- Limited scalability as sample volumes grow
- Time spent on routine checks instead of scientific work

This project demonstrates how a Python pipeline can automate these workflows end-to-end — from raw instrument export to structured QC report — while remaining transparent, reproducible, and easy to extend.

---

## Alignment with Laboratory Digitalisation Goals

This project directly addresses common objectives in analytical R&D and QC environments:

| Laboratory need | How this project addresses it |
|---|---|
| Automate repetitive data processing | Full pipeline runs in one command |
| Improve data reliability | Standardised QC rules and traceable outputs |
| Reduce manual intervention | Automated import, cleaning, calculation, reporting |
| Support analytical data interpretation | RSD%, recovery%, control charts |
| Enable continuous improvement | Modular design, extendable to new instruments |
| Interface with existing tools | CSV/Excel input, Excel/PNG output |
| Reduce environmental impact of operations | Less paper, less manual processing, faster turnaround |

---

## Features

### Data Handling
- Automatic import of instrument export files (CSV/Excel)
- Column standardisation and date parsing
- Duplicate detection by sample ID
- Missing-value detection and handling

### Quality-Control Metrics
- Mean and standard deviation across replicates
- Relative standard deviation (RSD%) as precision indicator
- Recovery percentage against expected concentration
- Replicate count tracking

### Statistical Analysis
- Grubbs' test for outlier detection within replicates
- Acceptance-criteria flagging:
  - Precision: RSD% > 5%
  - Accuracy: recovery outside 90–110%
- Sample-level QC status (PASS / REVIEW)

### Visualisation
- Recovery distribution with acceptance limits
- Precision (RSD%) distribution with threshold
- Levey-Jennings control chart for recovery trends
- Instrument-level QC status breakdown

### Reporting
- Structured Excel report (all results, flagged samples, summary)
- PNG dashboard with 4 QC panels
- Real-time console feedback

---

## Pipeline Architecture
Raw instrument data (CSV / Excel)
|
v

DATA IMPORT ............... Column standardisation, date parsing
|
v

DATA CLEANING ............. Deduplication, missing-value handling
|
v

QC METRICS ................ Mean, SD, RSD%, recovery%
|
v

OUTLIER DETECTION ......... Grubbs' test, acceptance criteria
|v

VISUALISATION ............. Distributions, control charts, summaries
|
v

AUTOMATED REPORT .......... Excel workbook + PNG dashboard + console
---

## Quality-Control Rules

| Rule | Threshold | Purpose |
|---|---|---|
| Precision | RSD% ≤ 5% | Repeatability across replicates |
| Accuracy | Recovery 90–110% | Agreement with expected value |
| Grubbs' test | G > G_crit (n=3, α=0.05) | Single-outlier detection |

A sample is flagged **REVIEW** if any rule is violated; otherwise **PASS**.

Thresholds are defined in the `detect_outliers()` method and can be adapted to specific laboratory SOPs.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/noor-chemoinformatics/analytical-lab-data-automation.git
cd analytical-lab-data-automation

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt# 
