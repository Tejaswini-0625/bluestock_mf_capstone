"""
data_ingestion.py
=================
Day 1 — Mutual Fund Analytics Project
Tasks covered:
  3. Load all 10 CSV datasets → shape, dtypes, head, anomalies
  6. Explore fund_master (unique fund houses, categories, sub-categories, risk grades)
  7. Validate AMFI codes — every fund_master code must exist in nav_history
     → Write data quality summary to reports/data_quality_summary.txt

Author : Tejaswini
Date   : 2025
"""

import os
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
RAW_DIR        = os.path.join("data", "raw")
PROCESSED_DIR  = os.path.join("data", "processed")
REPORTS_DIR    = "reports"

for d in [PROCESSED_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

DATASETS = {
    "fund_master":           "01_fund_master.csv",
    "nav_history":           "02_nav_history.csv",
    "aum_by_fund_house":     "03_aum_by_fund_house.csv",
    "monthly_sip_inflows":   "04_monthly_sip_inflows.csv",
    "category_inflows":      "05_category_inflows.csv",
    "industry_folio_count":  "06_industry_folio_count.csv",
    "scheme_performance":    "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings":    "09_portfolio_holdings.csv",
    "benchmark_indices":     "10_benchmark_indices.csv",
}

SEPARATOR = "=" * 65


# ─────────────────────────────────────────────
# TASK 3 — Load & Inspect Each CSV
# ─────────────────────────────────────────────

def load_and_inspect(name: str, filename: str) -> pd.DataFrame:
    """Load a CSV, print shape / dtypes / head, flag anomalies."""
    path = os.path.join(RAW_DIR, filename)
    df   = pd.read_csv(path)

    print(f"\n{SEPARATOR}")
    print(f"  DATASET : {name.upper()}")
    print(SEPARATOR)

    # Shape
    print(f"\n📐 Shape : {df.shape[0]:,} rows × {df.shape[1]} columns")

    # dtypes
    print("\n🔠 Data Types:")
    print(df.dtypes.to_string())

    # Head
    print("\n👀 First 3 rows:")
    print(df.head(3).to_string(index=False))

    # Anomaly detection
    anomalies = []

    # Missing values
    null_counts = df.isnull().sum()
    missing = null_counts[null_counts > 0]
    if not missing.empty:
        for col, cnt in missing.items():
            pct = cnt / len(df) * 100
            anomalies.append(f"  ⚠  Missing values in '{col}': {cnt} ({pct:.1f}%)")

    # Duplicate rows
    dupes = df.duplicated().sum()
    if dupes > 0:
        anomalies.append(f"  ⚠  Duplicate rows detected: {dupes}")

    # Negative NAV / AUM
    for col in df.select_dtypes(include=[np.number]).columns:
        if col.lower() in ("nav", "aum_cr", "amount", "units_allotted", "nav_value"):
            neg = (df[col] < 0).sum()
            if neg:
                anomalies.append(f"  ⚠  Negative values in '{col}': {neg} rows")

    # Zero NAV
    if "nav" in df.columns:
        zeros = (df["nav"] == 0).sum()
        if zeros:
            anomalies.append(f"  ⚠  Zero NAV rows: {zeros}")

    # Date column parsing check
    for col in df.columns:
        if "date" in col.lower() or "month" in col.lower():
            try:
                pd.to_datetime(df[col])
            except Exception:
                anomalies.append(f"  ⚠  Column '{col}' has unparseable date values")

    if anomalies:
        print("\n🔍 Anomalies Found:")
        for a in anomalies:
            print(a)
    else:
        print("\n✅ No anomalies detected.")

    return df


def load_all_datasets() -> dict:
    """Load all 10 datasets and return as a dict of DataFrames."""
    print(f"\n{'#'*65}")
    print("  TASK 3 — LOADING ALL 10 CSV DATASETS")
    print(f"{'#'*65}")

    dfs = {}
    for name, filename in DATASETS.items():
        dfs[name] = load_and_inspect(name, filename)

    print(f"\n\n✅ All {len(dfs)} datasets loaded successfully.\n")
    return dfs


# ─────────────────────────────────────────────
# TASK 6 — Explore fund_master
# ─────────────────────────────────────────────

def explore_fund_master(df: pd.DataFrame) -> None:
    """Print unique fund houses, categories, sub-categories, risk grades
       and explain the AMFI scheme code structure."""
    print(f"\n{'#'*65}")
    print("  TASK 6 — FUND MASTER EXPLORATION")
    print(f"{'#'*65}")

    print(f"\n📋 Total Schemes in Master : {len(df)}")

    print("\n🏦 Unique Fund Houses:")
    for i, fh in enumerate(sorted(df["fund_house"].unique()), 1):
        count = (df["fund_house"] == fh).sum()
        print(f"  {i:2}. {fh:<35} ({count} scheme/s)")

    print("\n📂 Categories:")
    for cat in df["category"].unique():
        print(f"  • {cat}")

    print("\n📁 Sub-Categories:")
    for sub in sorted(df["sub_category"].unique()):
        count = (df["sub_category"] == sub).sum()
        print(f"  • {sub:<25} → {count} scheme/s")

    print("\n⚠  Risk Categories:")
    risk_col = "risk_category" if "risk_category" in df.columns else "risk_grade"
    for rg in df[risk_col].unique():
        count = (df[risk_col] == rg).sum()
        print(f"  • {str(rg):<25} → {count} scheme/s")

    print("\n📌 AMFI Scheme Code Structure:")
    print("""
  AMFI (Association of Mutual Funds in India) assigns each scheme
  a unique numeric Scheme Code used across:
    ─ AMFI website (amfiindia.com)
    ─ mfapi.in (free NAV API)
    ─ BSE/NSE platforms

  Format    : Pure integer (5–6 digits), e.g. 125497
  Structure :
    • No internal hierarchy — codes are sequentially assigned
    • Regular vs Direct plans get *different* codes
      e.g. HDFC Top 100 Regular ≠ HDFC Top 100 Direct (125497)
    • Growth vs Dividend options may also carry separate codes
    • Codes are permanent; discontinued funds retain their code

  Sample codes in this dataset:
""")
    code_col = "amfi_code" if "amfi_code" in df.columns else "scheme_code"
    sample = df[[code_col, "scheme_name", "fund_house"]].head(6)
    print(sample.to_string(index=False))


# ─────────────────────────────────────────────
# TASK 7 — Validate AMFI Codes + Data Quality
# ─────────────────────────────────────────────

def validate_amfi_codes(fund_master: pd.DataFrame,
                        nav_history: pd.DataFrame) -> None:
    """Check every scheme_code in fund_master exists in nav_history.
       Write summary to reports/data_quality_summary.txt."""

    print(f"\n{'#'*65}")
    print("  TASK 7 — AMFI CODE VALIDATION & DATA QUALITY")
    print(f"{'#'*65}\n")

    # detect correct code column name
    master_code_col  = "amfi_code" if "amfi_code" in fund_master.columns else "scheme_code"
    history_code_col = "amfi_code" if "amfi_code" in nav_history.columns else "scheme_code"

    master_codes  = set(fund_master[master_code_col].unique())
    history_codes = set(nav_history[history_code_col].unique())

    missing_in_history = master_codes - history_codes
    orphan_in_history  = history_codes - master_codes

    print(f"  Fund Master   — unique scheme codes : {len(master_codes)}")
    print(f"  NAV History   — unique scheme codes : {len(history_codes)}")
    print(f"  Missing in nav_history              : {len(missing_in_history)}")
    print(f"  Orphan codes in nav_history          : {len(orphan_in_history)}")

    if missing_in_history:
        print(f"\n  ⚠  Codes in fund_master NOT found in nav_history:")
        for code in sorted(missing_in_history):
            name = fund_master.loc[fund_master[master_code_col]==code, "scheme_name"].values
            print(f"      {code}  —  {name[0] if len(name) else 'Unknown'}")
    else:
        print("\n  ✅ All fund_master codes have NAV history.")

    # Additional quality checks across all datasets
    checks = []

    # fund_master
    fm_dupes = fund_master.duplicated(subset=master_code_col).sum()
    checks.append(("fund_master", "Duplicate scheme_code rows", fm_dupes,
                   "PASS" if fm_dupes == 0 else "FAIL"))

    fm_null = fund_master.isnull().sum().sum()
    checks.append(("fund_master", "Total null values", fm_null,
                   "PASS" if fm_null == 0 else "WARNING"))

    # nav_history — detect nav and date columns
    nav_col  = "nav" if "nav" in nav_history.columns else nav_history.select_dtypes("number").columns[0]
    date_col = "date" if "date" in nav_history.columns else "nav_date"

    nav_neg = (nav_history[nav_col] < 0).sum()
    checks.append(("nav_history", "Negative NAV rows", nav_neg,
                   "PASS" if nav_neg == 0 else "FAIL"))

    nav_zero = (nav_history[nav_col] == 0).sum()
    checks.append(("nav_history", "Zero NAV rows", nav_zero,
                   "PASS" if nav_zero == 0 else "FAIL"))

    # nav_history date range
    nav_history[date_col] = pd.to_datetime(nav_history[date_col], errors="coerce")
    date_range = f"{nav_history[date_col].min().date()} → {nav_history[date_col].max().date()}"
    checks.append(("nav_history", "Date range", date_range, "INFO"))

    # AMFI code coverage
    coverage_pct = round(len(master_codes & history_codes) / len(master_codes) * 100, 1)
    checks.append(("cross-dataset", "AMFI code coverage in NAV history",
                   f"{coverage_pct}%", "PASS" if coverage_pct == 100 else "WARNING"))

    # Build report
    report_lines = []
    report_lines.append("DATA QUALITY SUMMARY — Mutual Fund Analytics Project")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append(f"{'Dataset':<20} {'Check':<45} {'Value':<15} {'Status'}")
    report_lines.append("-" * 100)
    for dataset, check, value, status in checks:
        report_lines.append(f"{dataset:<20} {check:<45} {str(value):<15} {status}")
    report_lines.append("\n")
    report_lines.append("AMFI Code Validation")
    report_lines.append("-" * 40)
    report_lines.append(f"Codes in fund_master       : {len(master_codes)}")
    report_lines.append(f"Codes in nav_history       : {len(history_codes)}")
    report_lines.append(f"Missing in nav_history     : {len(missing_in_history)}")
    report_lines.append(f"Orphan codes in nav_history: {len(orphan_in_history)}")

    if missing_in_history:
        report_lines.append(f"\nMissing codes: {sorted(missing_in_history)}")
    else:
        report_lines.append("\n✅ All fund_master scheme codes validated in nav_history.")

    report_lines.append("\n")
    report_lines.append("DATASET OVERVIEW")
    report_lines.append("-" * 40)
    for name, filename in DATASETS.items():
        path = os.path.join(RAW_DIR, filename)
        df   = pd.read_csv(path)
        report_lines.append(f"  {name:<25}: {df.shape[0]:>6,} rows × {df.shape[1]:>2} cols")

    report_text = "\n".join(report_lines)

    # Print to console
    print("\n" + report_text)

    # Save to file
    report_path = os.path.join(REPORTS_DIR, "data_quality_summary.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n📄 Report saved → {report_path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # ── Task 3: Load all 10 CSVs ──
    dfs = load_all_datasets()

    # ── Task 6: Explore fund_master ──
    explore_fund_master(dfs["fund_master"])

    # ── Task 7: Validate AMFI codes ──
    validate_amfi_codes(dfs["fund_master"], dfs["nav_history"])

    print(f"\n{'='*65}")
    print("  ✅  data_ingestion.py — ALL TASKS COMPLETE")
    print(f"{'='*65}\n")
