"""
Automated Analytical Data Quality-Control Pipeline
====================================================
Author: Manahil Noor
Purpose: Automated QC for analytical laboratory data,
         with rule-based and ML-based outlier detection.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from sklearn.ensemble import IsolationForest
warnings.filterwarnings("ignore")


class AnalyticalQCPipeline:
    """Automated quality-control pipeline for analytical chemistry data."""

    def __init__(self, input_file, output_dir="qc_output"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.raw_data = None
        self.cleaned_data = None
        self.qc_results = None
        self.flags = []
        self.replicate_cols = []
        os.makedirs(output_dir, exist_ok=True)

    # ---------------------------------------------------------
    # 1. DATA IMPORT
    # ---------------------------------------------------------
    def import_data(self):
        print("[1/6] Importing data...")
        self.raw_data = pd.read_csv(self.input_file)
        print(f"      Loaded {len(self.raw_data)} records")
        return self

    # ---------------------------------------------------------
    # 2. DATA CLEANING
    # ---------------------------------------------------------
    def clean_dataset(self):
        print("[2/6] Cleaning data...")
        df = self.raw_data.copy()
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        before = len(df)
        df = df.drop_duplicates(subset=["sample_id"], keep="first")
        dupes_removed = before - len(df)
        if dupes_removed > 0:
            self.flags.append(f"Removed {dupes_removed} duplicate sample(s)")

        rep_cols = [c for c in df.columns if c.startswith("replicate_")]
        self.replicate_cols = rep_cols

        missing_before = df[rep_cols].isna().sum().sum()
        if missing_before > 0:
            self.flags.append(
                f"Found {missing_before} missing replicate value(s)"
            )

        df = df.dropna(subset=rep_cols, how="all")
        self.cleaned_data = df
        print(f"      Clean dataset: {len(df)} records")
        return self

    # ---------------------------------------------------------
    # 3. QC METRICS
    # ---------------------------------------------------------
    def calculate_qc_metrics(self):
        print("[3/6] Calculating QC metrics...")
        df = self.cleaned_data.copy()
        rep_cols = self.replicate_cols

        df["mean_measured"] = df[rep_cols].mean(axis=1, skipna=True)
        df["sd_measured"] = df[rep_cols].std(axis=1, skipna=True)
        df["n_replicates"] = df[rep_cols].notna().sum(axis=1)

        df["rsd_percent"] = np.where(
            df["mean_measured"] > 0,
            (df["sd_measured"] / df["mean_measured"]) * 100,
            np.nan,
        )

        if "expected_concentration" in df.columns:
            df["recovery_percent"] = (
                df["mean_measured"] / df["expected_concentration"]
            ) * 100
        else:
            df["recovery_percent"] = np.nan

        self.cleaned_data = df
        return self

    # ---------------------------------------------------------
    # 4. RULE-BASED OUTLIER DETECTION
    # ---------------------------------------------------------
    def detect_outliers(self):
        print("[4/6] Detecting outliers and quality issues...")
        df = self.cleaned_data.copy()

        df["flag_precision"] = df["rsd_percent"] > 5.0
        df["flag_accuracy"] = (df["recovery_percent"] < 90) | (
            df["recovery_percent"] > 110
        )

        def grubbs_flag(row):
            vals = row[self.replicate_cols].dropna().values
            if len(vals) < 3:
                return False
            mean = vals.mean()
            sd = vals.std(ddof=1)
            if sd == 0:
                return False
            g = np.max(np.abs(vals - mean)) / sd
            g_crit = 1.155
            return g > g_crit

        df["flag_grubbs"] = df.apply(grubbs_flag, axis=1)

        df["qc_status"] = np.where(
            df[["flag_precision", "flag_accuracy", "flag_grubbs"]].any(axis=1),
            "REVIEW",
            "PASS",
        )

        n_review = (df["qc_status"] == "REVIEW").sum()
        self.flags.append(f"{n_review} sample(s) flagged for review")

        self.qc_results = df
        print(f"      PASS: {(df['qc_status'] == 'PASS').sum()}")
        print(f"      REVIEW: {n_review}")
        return self

    # ---------------------------------------------------------
    # 4b. ML-BASED ANOMALY DETECTION
    # ---------------------------------------------------------
    def ml_anomaly_detection(self):
        """Detect multivariate anomalies using Isolation Forest."""
        print("[4b/6] Running ML anomaly detection...")
        df = self.qc_results.copy()

        feature_cols = ["rsd_percent", "recovery_percent", "mean_measured"]
        feature_df = df[feature_cols].dropna()

        if len(feature_df) < 10:
            print("      Not enough data - skipping ML detection")
            df["ml_anomaly"] = False
            df["ml_score"] = np.nan
            self.qc_results = df
            return self

        model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100,
        )
        model.fit(feature_df)

        preds = model.predict(feature_df)
        scores = model.decision_function(feature_df)

        df.loc[feature_df.index, "ml_anomaly"] = preds == -1
        df.loc[feature_df.index, "ml_score"] = scores
        df["ml_anomaly"] = df["ml_anomaly"].fillna(False).astype(bool)

        n_ml = int(df["ml_anomaly"].sum())
        self.flags.append(f"{n_ml} sample(s) flagged by ML anomaly detection")

        rule_flagged = df["qc_status"] == "REVIEW"
        ml_flagged = df["ml_anomaly"]
        both = (rule_flagged & ml_flagged).sum()
        rules_only = (rule_flagged & ~ml_flagged).sum()
        ml_only = (~rule_flagged & ml_flagged).sum()

        print(f"      ML flagged: {n_ml}")
        print(f"      Both rule + ML: {both}")
        print(f"      Rule only: {rules_only}")
        print(f"      ML only (missed by rules): {ml_only}")

        self.flags.append(f"ML-only detections: {ml_only}")
        self.qc_results = df
        return self

    # ---------------------------------------------------------
    # 5. VISUALISATION
    # ---------------------------------------------------------
    def generate_plots(self):
        print("[5/6] Generating visualisations...")
        df = self.qc_results

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle("Analytical QC Report", fontsize=16, fontweight="bold")

        # Panel 1: Recovery
        ax = axes[0, 0]
        ax.hist(df["recovery_percent"].dropna(), bins=30,
                color="steelblue", edgecolor="white")
        ax.axvline(90, color="red", linestyle="--", label="90% limit")
        ax.axvline(110, color="red", linestyle="--", label="110% limit")
        ax.set_xlabel("Recovery (%)")
        ax.set_ylabel("Frequency")
        ax.set_title("Recovery Distribution")
        ax.legend()

        # Panel 2: RSD
        ax = axes[0, 1]
        ax.hist(df["rsd_percent"].dropna(), bins=30,
                color="seagreen", edgecolor="white")
        ax.axvline(5.0, color="red", linestyle="--", label="5% limit")
        ax.set_xlabel("RSD (%)")
        ax.set_ylabel("Frequency")
        ax.set_title("Precision (RSD%) Distribution")
        ax.legend()

        # Panel 3: Control chart
        ax = axes[0, 2]
        df_sorted = df.sort_values("date")
        ax.plot(range(len(df_sorted)), df_sorted["recovery_percent"],
                "o-", markersize=3, color="navy", alpha=0.6)
        ax.axhline(100, color="green", linestyle="-", label="Target 100%")
        ax.axhline(90, color="red", linestyle="--", label="+/-10% limits")
        ax.axhline(110, color="red", linestyle="--")
        ax.set_xlabel("Sample sequence")
        ax.set_ylabel("Recovery (%)")
        ax.set_title("Control Chart - Recovery")
        ax.legend()

        # Panel 4: QC status by instrument
        ax = axes[1, 0]
        status_by_instrument = pd.crosstab(
            df["instrument"], df["qc_status"]
        )
        status_by_instrument.plot(kind="bar", ax=ax,
                                  color=["green", "orange"])
        ax.set_xlabel("Instrument")
        ax.set_ylabel("Number of samples")
        ax.set_title("QC Status by Instrument")
        ax.legend(title="Status")

        # Panel 5: ML score distribution
        ax = axes[1, 1]
        if "ml_score" in df.columns:
            ml_anomaly_bool = df["ml_anomaly"].astype(bool)
            normal = df.loc[~df["ml_anomaly"], "ml_score"].dropna()
            anomaly = df.loc[df["ml_anomaly"], "ml_score"].dropna()
            ax.hist(normal, bins=30, color="steelblue",
                    edgecolor="white", label="Normal", alpha=0.8)
            ax.hist(anomaly, bins=15, color="crimson",
                    edgecolor="white", label="Anomaly", alpha=0.8)
            ax.axvline(0, color="black", linestyle="--",
                       label="Decision boundary")
            ax.set_xlabel("Isolation Forest score")
            ax.set_ylabel("Frequency")
            ax.set_title("ML Anomaly Detection")
            ax.legend()

        # Panel 6: Rules vs ML comparison
        ax = axes[1, 2]
        rule_flagged = df["qc_status"] == "REVIEW"
        ml_flagged = df["ml_anomaly"]
        both = (rule_flagged & ml_flagged).sum()
        rules_only = (rule_flagged & ~ml_flagged).sum()
        ml_only = (~rule_flagged & ml_flagged).sum()
        clean = (~rule_flagged & ~ml_flagged).sum()

        categories = ["Both", "Rules only", "ML only", "Neither"]
        values = [both, rules_only, ml_only, clean]
        colors = ["crimson", "orange", "purple", "green"]
        ax.bar(categories, values, color=colors, edgecolor="white")
        ax.set_ylabel("Number of samples")
        ax.set_title("Rule-based vs ML Detection")
        for i, v in enumerate(values):
            ax.text(i, v + 0.5, str(v), ha="center", fontweight="bold")

        plt.tight_layout()
        plot_path = os.path.join(self.output_dir, "qc_report.png")
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"      Saved: {plot_path}")
        return self

    # ---------------------------------------------------------
    # 6. AUTOMATED REPORT
    # ---------------------------------------------------------
    def generate_report(self):
        print("[6/6] Generating report...")
        df = self.qc_results

        results_path = os.path.join(self.output_dir, "qc_results.xlsx")
        with pd.ExcelWriter(results_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="All Results", index=False)

            flagged = df[df["qc_status"] == "REVIEW"]
            flagged.to_excel(writer, sheet_name="Flagged for Review",
                             index=False)

            ml_only = df[(df["ml_anomaly"]) & (df["qc_status"] == "PASS")]
            ml_only.to_excel(writer, sheet_name="ML-only Detections",
                             index=False)

            summary = pd.DataFrame({
                "Metric": [
                    "Total samples",
                    "Passed QC (rules)",
                    "Flagged by rules",
                    "Flagged by ML",
                    "Flagged by both",
                    "ML-only detections",
                    "Mean recovery (%)",
                    "Mean RSD (%)",
                    "Max RSD (%)",
                ],
                "Value": [
                    len(df),
                    (df["qc_status"] == "PASS").sum(),
                    (df["qc_status"] == "REVIEW").sum(),
                    int(df["ml_anomaly"].sum()),
                    int(((df["qc_status"] == "REVIEW") &
                         df["ml_anomaly"]).sum()),
                    int(((df["qc_status"] == "PASS") &
                         df["ml_anomaly"]).sum()),
                    round(df["recovery_percent"].mean(), 2),
                    round(df["rsd_percent"].mean(), 2),
                    round(df["rsd_percent"].max(), 2),
                ],
            })
            summary.to_excel(writer, sheet_name="Summary", index=False)

        print(f"      Saved: {results_path}")

        print("\n" + "=" * 50)
        print("QC PIPELINE SUMMARY")
        print("=" * 50)
        for flag in self.flags:
            print(f"  - {flag}")
        print(f"  - Mean recovery: {df['recovery_percent'].mean():.1f}%")
        print(f"  - Mean RSD: {df['rsd_percent'].mean():.2f}%")
        print("=" * 50)

        return self

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------
    def run(self):
        print("\n" + "=" * 50)
        print("AUTOMATED ANALYTICAL QC PIPELINE")
        print("=" * 50 + "\n")

        self.import_data()
        self.clean_dataset()
        self.calculate_qc_metrics()
        self.detect_outliers()
        self.ml_anomaly_detection()
        self.generate_plots()
        self.generate_report()

        print("\n[OK] Pipeline complete.\n")
        return self.qc_results


if __name__ == "__main__":
    pipeline = AnalyticalQCPipeline(
        input_file="raw_lab_data.csv",
        output_dir="qc_output",
    )
    results = pipeline.run()