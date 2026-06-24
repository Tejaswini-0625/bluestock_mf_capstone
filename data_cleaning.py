"""
data_cleaning.py
================
Day 2 — Mutual Fund Analytics Project
Tasks covered:
  1. Clean nav_history       — parse dates, sort, forward-fill, dedup, validate NAV > 0
  2. Clean investor_transactions — standardise types, validate amount, fix dates, KYC enum
  3. Clean scheme_performance    — validate numeric returns, flag anomalies, expense ratio range
  4-5. Load all cleaned CSVs into SQLite (bluestock_mf.db) via pandas + sqlite3/SQLAlchemy
       Verify row counts match source CSVs

Author : Tejaswini
Date   : 2025
"""

import os
import sqlite3
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
RAW_DIR       = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
DB_PATH       = os.path.join("data", "bluestock_mf.db")
REPORTS_DIR   = "reports"

for d in [PROCESSED_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

SEPARATOR = "=" * 65


# ─────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────

def log(msg): print(f"\n  {msg}")
def ok(msg):  print(f"  ✅ {msg}")
def warn(msg): print(f"  ⚠  {msg}")


def save_processed(df: pd.DataFrame, filename: str) -> None:
    path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8")
    ok(f"Saved → {path}  ({len(df):,} rows)")


# ─────────────────────────────────────────────
# TASK 1 — Clean nav_history
# ─────────────────────────────────────────────

def clean_nav_history() -> pd.DataFrame:
    print(f"\n{SEPARATOR}")
    print("  TASK 1 — CLEAN: nav_history")
    print(SEPARATOR)

    df = pd.read_csv(os.path.join(RAW_DIR, "02_nav_history.csv"))
    log(f"Raw shape: {df.shape}")

    # 1a. Parse date to datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = df["date"].isna().sum()
    if invalid_dates:
        warn(f"{invalid_dates} rows with unparseable dates — dropped")
        df.dropna(subset=["date"], inplace=True)
    else:
        ok("All dates parsed successfully")

    # 1b. Sort by amfi_code + date
    df.sort_values(["amfi_code", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    ok("Sorted by amfi_code + date")

    # 1c. Remove duplicates
    before = len(df)
    df.drop_duplicates(subset=["amfi_code", "date"], inplace=True)
    dupes = before - len(df)
    ok(f"Duplicates removed: {dupes}")

    # 1d. Validate NAV > 0
    invalid_nav = (df["nav"] <= 0).sum()
    if invalid_nav:
        warn(f"{invalid_nav} rows with NAV <= 0 — dropped")
        df = df[df["nav"] > 0]
    else:
        ok("All NAV values > 0")

    # 1e. Forward-fill missing NAV for weekends/holidays
    # Create complete date range per scheme and ffill
    all_schemes = df["amfi_code"].unique()
    date_min = df["date"].min()
    date_max = df["date"].max()
    full_dates = pd.date_range(date_min, date_max, freq="D")

    filled_dfs = []
    for code in all_schemes:
        scheme_df = df[df["amfi_code"] == code].set_index("date")
        scheme_df = scheme_df.reindex(full_dates)
        scheme_df["amfi_code"] = code
        scheme_df["nav"] = scheme_df["nav"].ffill()
        scheme_df = scheme_df.dropna(subset=["nav"])
        scheme_df.index.name = "date"
        scheme_df.reset_index(inplace=True)
        filled_dfs.append(scheme_df)

    df_filled = pd.concat(filled_dfs, ignore_index=True)
    ok(f"Forward-fill complete: {len(df):,} → {len(df_filled):,} rows (weekends/holidays filled)")

    # 1f. Add derived columns
    df_filled["year"]  = df_filled["date"].dt.year
    df_filled["month"] = df_filled["date"].dt.month
    df_filled["date"]  = df_filled["date"].dt.strftime("%Y-%m-%d")

    log(f"Clean shape: {df_filled.shape}")
    print(f"\n  Sample (first 3 rows):")
    print(df_filled.head(3).to_string(index=False))

    save_processed(df_filled, "02_nav_history_clean.csv")
    return df_filled


# ─────────────────────────────────────────────
# TASK 2 — Clean investor_transactions
# ─────────────────────────────────────────────

def clean_investor_transactions() -> pd.DataFrame:
    print(f"\n{SEPARATOR}")
    print("  TASK 2 — CLEAN: investor_transactions")
    print(SEPARATOR)

    df = pd.read_csv(os.path.join(RAW_DIR, "08_investor_transactions.csv"))
    log(f"Raw shape: {df.shape}")

    # 2a. Fix date formats
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    bad_dates = df["transaction_date"].isna().sum()
    if bad_dates:
        warn(f"{bad_dates} invalid dates dropped")
        df.dropna(subset=["transaction_date"], inplace=True)
    else:
        ok("All transaction dates valid")

    # 2b. Standardise transaction_type values
    valid_types = {"SIP", "Lumpsum", "Redemption"}
    type_map = {
        "sip":        "SIP",
        "lumpsum":    "Lumpsum",
        "lump sum":   "Lumpsum",
        "lump_sum":   "Lumpsum",
        "redemption": "Redemption",
        "redeem":     "Redemption",
        "withdraw":   "Redemption",
    }
    df["transaction_type"] = (
        df["transaction_type"]
        .str.strip()
        .replace(type_map)
    )
    invalid_types = df[~df["transaction_type"].isin(valid_types)]
    if len(invalid_types):
        warn(f"{len(invalid_types)} rows with unrecognised transaction_type — dropped")
        df = df[df["transaction_type"].isin(valid_types)]
    else:
        ok(f"Transaction types valid: {df['transaction_type'].unique().tolist()}")

    # 2c. Validate amount > 0
    bad_amount = (df["amount_inr"] <= 0).sum()
    if bad_amount:
        warn(f"{bad_amount} rows with amount <= 0 — dropped")
        df = df[df["amount_inr"] > 0]
    else:
        ok("All amounts > 0")

    # 2d. KYC status enum check
    valid_kyc = {"Verified", "Pending", "Rejected"}
    bad_kyc = df[~df["kyc_status"].isin(valid_kyc)]
    if len(bad_kyc):
        warn(f"{len(bad_kyc)} rows with invalid KYC status: {bad_kyc['kyc_status'].unique()}")
    else:
        ok(f"KYC status values valid: {df['kyc_status'].unique().tolist()}")

    # 2e. Format date back to string
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")

    # 2f. Add derived columns
    df["transaction_year"]  = pd.to_datetime(df["transaction_date"]).dt.year
    df["transaction_month"] = pd.to_datetime(df["transaction_date"]).dt.month

    log(f"Clean shape: {df.shape}")
    print(f"\n  Transaction type distribution:")
    print(df["transaction_type"].value_counts().to_string())
    print(f"\n  KYC status distribution:")
    print(df["kyc_status"].value_counts().to_string())

    save_processed(df, "08_investor_transactions_clean.csv")
    return df


# ─────────────────────────────────────────────
# TASK 3 — Clean scheme_performance
# ─────────────────────────────────────────────

def clean_scheme_performance() -> pd.DataFrame:
    print(f"\n{SEPARATOR}")
    print("  TASK 3 — CLEAN: scheme_performance")
    print(SEPARATOR)

    df = pd.read_csv(os.path.join(RAW_DIR, "07_scheme_performance.csv"))
    log(f"Raw shape: {df.shape}")

    return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                   "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
                   "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"]

    # 3a. Validate all return values are numeric
    anomalies = []
    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        null_count = df[col].isna().sum()
        if null_count:
            warn(f"  {col}: {null_count} non-numeric values coerced to NaN")
            anomalies.append((col, "non-numeric", null_count))
        else:
            ok(f"{col}: all numeric ✓")

    # 3b. Flag anomalies — extreme returns
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
        extreme = df[(df[col] > 100) | (df[col] < -50)]
        if len(extreme):
            warn(f"Extreme return in {col}: {len(extreme)} rows flagged")
            anomalies.append((col, "extreme_value", len(extreme)))
            df.loc[(df[col] > 100) | (df[col] < -50), col + "_flagged"] = True

    # 3c. Validate expense_ratio range (0.1% – 2.5%)
    exp_out  = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
    if len(exp_out):
        warn(f"expense_ratio_pct out of range (0.1–2.5%): {len(exp_out)} rows")
        for _, row in exp_out.iterrows():
            print(f"    {row['scheme_name']}: {row['expense_ratio_pct']}%")
        anomalies.append(("expense_ratio_pct", "out_of_range", len(exp_out)))
    else:
        ok("All expense ratios within 0.1%–2.5% range")

    # 3d. Validate beta range (typically 0 – 2)
    beta_out = df[(df["beta"] < 0) | (df["beta"] > 2)]
    if len(beta_out):
        warn(f"Beta out of normal range (0–2): {len(beta_out)} rows")
    else:
        ok("All beta values in normal range")

    # 3e. Save anomaly log
    if anomalies:
        anom_df = pd.DataFrame(anomalies, columns=["column", "issue", "count"])
        anom_path = os.path.join(REPORTS_DIR, "scheme_performance_anomalies.csv")
        anom_df.to_csv(anom_path, index=False)
        log(f"Anomaly log saved → {anom_path}")

    log(f"Clean shape: {df.shape}")
    print(f"\n  Return stats summary:")
    print(df[["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
              "expense_ratio_pct"]].describe().round(2).to_string())

    save_processed(df, "07_scheme_performance_clean.csv")
    return df


# ─────────────────────────────────────────────
# CLEAN REMAINING 7 DATASETS (light cleaning)
# ─────────────────────────────────────────────

def clean_remaining() -> dict:
    print(f"\n{SEPARATOR}")
    print("  CLEANING REMAINING 7 DATASETS")
    print(SEPARATOR)

    cleaned = {}

    specs = [
        ("01_fund_master.csv",        "01_fund_master_clean.csv",        ["launch_date"]),
        ("03_aum_by_fund_house.csv",   "03_aum_by_fund_house_clean.csv",  ["date"]),
        ("04_monthly_sip_inflows.csv", "04_monthly_sip_inflows_clean.csv",["month"]),
        ("05_category_inflows.csv",    "05_category_inflows_clean.csv",   ["month"]),
        ("06_industry_folio_count.csv","06_industry_folio_count_clean.csv",["month"]),
        ("09_portfolio_holdings.csv",  "09_portfolio_holdings_clean.csv", ["portfolio_date"]),
        ("10_benchmark_indices.csv",   "10_benchmark_indices_clean.csv",  ["date"]),
    ]

    for raw_file, clean_file, date_cols in specs:
        df = pd.read_csv(os.path.join(RAW_DIR, raw_file))
        before = len(df)

        # Parse date columns
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].dt.strftime("%Y-%m-%d")

        # Drop full-duplicate rows
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        after = len(df)

        print(f"\n  {raw_file}")
        ok(f"Shape: {df.shape}  (dropped {before-after} dupes)")

        save_processed(df, clean_file)
        cleaned[clean_file] = df

    return cleaned


# ─────────────────────────────────────────────
# TASKS 4 & 5 — Load into SQLite
# ─────────────────────────────────────────────

def load_to_sqlite(dfs: dict) -> None:
    print(f"\n{SEPARATOR}")
    print("  TASKS 4 & 5 — LOAD INTO SQLite: bluestock_mf.db")
    print(SEPARATOR)

    # Using sqlite3 directly (pandas .to_sql works with both sqlite3 and SQLAlchemy)
    # SQLAlchemy equivalent (for your machine):
    #   from sqlalchemy import create_engine
    #   engine = create_engine(f"sqlite:///{DB_PATH}")
    #   df.to_sql("table_name", engine, if_exists="replace", index=False)

    conn = sqlite3.connect(DB_PATH)

    table_map = {
        "dim_fund":           ("01_fund_master_clean.csv",         None),
        "fact_nav":           ("02_nav_history_clean.csv",         None),
        "fact_aum":           ("03_aum_by_fund_house_clean.csv",   None),
        "fact_sip_inflows":   ("04_monthly_sip_inflows_clean.csv", None),
        "fact_cat_inflows":   ("05_category_inflows_clean.csv",    None),
        "fact_folio":         ("06_industry_folio_count_clean.csv",None),
        "fact_performance":   ("07_scheme_performance_clean.csv",  None),
        "fact_transactions":  ("08_investor_transactions_clean.csv",None),
        "fact_holdings":      ("09_portfolio_holdings_clean.csv",  None),
        "fact_benchmark":     ("10_benchmark_indices_clean.csv",   None),
    }

    print(f"\n  {'Table':<25} {'Source Rows':>12} {'DB Rows':>10} {'Status':>8}")
    print(f"  {'-'*60}")

    for table_name, (filename, _) in table_map.items():
        path = os.path.join(PROCESSED_DIR, filename)
        if not os.path.exists(path):
            warn(f"File not found: {path}")
            continue

        df = pd.read_csv(path)
        source_rows = len(df)

        # Load into SQLite using pandas to_sql
        df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Verify row count
        db_rows = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table_name}", conn).iloc[0]["cnt"]
        status = "✅ PASS" if db_rows == source_rows else "❌ FAIL"
        print(f"  {table_name:<25} {source_rows:>12,} {db_rows:>10,} {status:>8}")

    conn.close()
    ok(f"Database saved → {DB_PATH}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(SEPARATOR)
    print("  data_cleaning.py — Day 2 ETL Pipeline")
    print(SEPARATOR)

    # Task 1
    nav_df   = clean_nav_history()

    # Task 2
    trans_df = clean_investor_transactions()

    # Task 3
    perf_df  = clean_scheme_performance()

    # Clean remaining 7
    others   = clean_remaining()

    # Tasks 4 & 5 — Load to SQLite
    all_dfs = {
        "nav":   nav_df,
        "trans": trans_df,
        "perf":  perf_df,
    }
    load_to_sqlite(all_dfs)

    print(f"\n{SEPARATOR}")
    print("  ✅  data_cleaning.py — ALL TASKS COMPLETE")
    print(f"  DB  → {DB_PATH}")
    print(f"  CSVs → {PROCESSED_DIR}/")
    print(SEPARATOR)
