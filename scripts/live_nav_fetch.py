"""
live_nav_fetch.py
=================
Day 1 — Mutual Fund Analytics Project
Tasks covered:
  4. Fetch live NAV for HDFC Top 100 Direct (code: 125497) from mfapi.in
     → Parse JSON → Save as data/raw/nav_hdfc_top100_live.csv
  5. Fetch NAV for 5 key large-cap schemes → Save each + combined CSV

API Base : https://api.mfapi.in/mf/{scheme_code}
Docs     : https://www.mfapi.in/

Schema returned by API:
  {
    "meta": { "scheme_name": ..., "fund_house": ..., ... },
    "data": [ {"date": "DD-MM-YYYY", "nav": "123.4567"}, ... ]
  }

Author : Tejaswini
Date   : 2025
"""

import os
import time
import json
import requests
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

BASE_URL = "https://api.mfapi.in/mf"

# Task 4 — Single scheme
HDFC_TOP100 = {
    "code": 125497,
    "label": "HDFC Top 100 Direct"
}

# Task 5 — 5 key large-cap schemes
KEY_SCHEMES = [
    {"code": 119551, "label": "SBI Bluechip Direct"},
    {"code": 120503, "label": "ICICI Pru Bluechip Direct"},
    {"code": 118632, "label": "Nippon India Large Cap Direct"},
    {"code": 119092, "label": "Axis Bluechip Direct"},
    {"code": 120841, "label": "Kotak Bluechip Direct"},
]

SEPARATOR = "─" * 60


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def fetch_nav(scheme_code: int, retries: int = 3, delay: float = 1.5) -> dict | None:
    """
    Fetch NAV data for a single scheme from mfapi.in.
    Returns parsed JSON dict or None on failure.

    Args:
        scheme_code : AMFI scheme code (integer)
        retries     : Number of retry attempts on timeout/5xx
        delay       : Seconds to wait between retries
    """
    url = f"{BASE_URL}/{scheme_code}"
    print(f"  📡 GET {url}")

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()                  # raise on 4xx/5xx
            data = response.json()
            print(f"     ✅ Status {response.status_code} | "
                  f"{len(data.get('data', []))} NAV records received")
            return data

        except requests.exceptions.Timeout:
            print(f"     ⏱  Timeout (attempt {attempt}/{retries})")

        except requests.exceptions.HTTPError as e:
            print(f"     ❌ HTTP Error: {e}")
            break                                        # don't retry 4xx

        except requests.exceptions.ConnectionError:
            print(f"     🔌 Connection error (attempt {attempt}/{retries})")

        except json.JSONDecodeError:
            print("     ❌ Invalid JSON in response")
            break

        if attempt < retries:
            time.sleep(delay)

    return None


def parse_and_save(raw: dict, scheme_code: int, filename: str) -> pd.DataFrame | None:
    """
    Parse the mfapi JSON response → clean DataFrame → save CSV.

    Returns the DataFrame, or None if parse failed.
    """
    if raw is None:
        print(f"     ⚠  No data to parse for scheme {scheme_code}")
        return None

    # Extract metadata
    meta = raw.get("meta", {})
    scheme_name = meta.get("scheme_name", "Unknown")
    fund_house  = meta.get("fund_house",  "Unknown")
    scheme_type = meta.get("scheme_type", "Unknown")
    scheme_cat  = meta.get("scheme_category", "Unknown")

    # Extract NAV history list
    nav_records = raw.get("data", [])
    if not nav_records:
        print("     ⚠  Empty NAV data in response")
        return None

    df = pd.DataFrame(nav_records)                       # columns: date, nav

    # Type coercion
    df["date"]        = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"]         = pd.to_numeric(df["nav"], errors="coerce")
    df["scheme_code"] = scheme_code
    df["scheme_name"] = scheme_name
    df["fund_house"]  = fund_house
    df["scheme_type"] = scheme_type
    df["category"]    = scheme_cat
    df["fetched_at"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Drop bad rows
    before = len(df)
    df.dropna(subset=["date", "nav"], inplace=True)
    dropped = before - len(df)
    if dropped:
        print(f"     ℹ  Dropped {dropped} rows with null date/nav after coercion")

    # Sort chronologically
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Save
    save_path = os.path.join(RAW_DIR, filename)
    df.to_csv(save_path, index=False)
    print(f"     💾 Saved → {save_path}  ({len(df):,} rows)")

    # Print quick summary
    print(f"     📊 Scheme  : {scheme_name}")
    print(f"     🏦 House   : {fund_house}")
    print(f"     📅 Range   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"     💰 Latest NAV : ₹ {df.iloc[-1]['nav']:.4f}  "
          f"(as of {df.iloc[-1]['date'].date()})")

    return df


# ─────────────────────────────────────────────
# TASK 4 — Fetch HDFC Top 100 Direct
# ─────────────────────────────────────────────

def task4_fetch_hdfc_top100() -> pd.DataFrame | None:
    print(f"\n{'#'*60}")
    print("  TASK 4 — HDFC Top 100 Direct Plan NAV (Live)")
    print(f"{'#'*60}\n")

    code = HDFC_TOP100["code"]
    raw  = fetch_nav(code)
    df   = parse_and_save(raw, code, "nav_hdfc_top100_live.csv")

    if df is not None:
        print(f"\n  📈 Sample NAV (last 5 entries):")
        print(df[["date", "nav"]].tail().to_string(index=False))

    return df


# ─────────────────────────────────────────────
# TASK 5 — Fetch 5 Key Large-Cap Schemes
# ─────────────────────────────────────────────

def task5_fetch_five_schemes() -> pd.DataFrame:
    print(f"\n{'#'*60}")
    print("  TASK 5 — 5 Key Large-Cap Schemes (Live NAV)")
    print(f"{'#'*60}")

    all_dfs = []

    for scheme in KEY_SCHEMES:
        code  = scheme["code"]
        label = scheme["label"]
        print(f"\n  {SEPARATOR}")
        print(f"  ▶  {label}  [code: {code}]")
        print(f"  {SEPARATOR}")

        raw = fetch_nav(code)
        df  = parse_and_save(raw, code, f"nav_{code}_live.csv")

        if df is not None:
            all_dfs.append(df)

        time.sleep(0.5)        # polite rate limiting

    # Combine all into one master file
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_path = os.path.join(RAW_DIR, "nav_five_schemes_combined.csv")
        combined.to_csv(combined_path, index=False)

        print(f"\n{'='*60}")
        print(f"  ✅ Combined CSV saved → {combined_path}")
        print(f"     Total rows : {len(combined):,}")
        print(f"\n  📋 Latest NAV snapshot:")
        snapshot = (
            combined.sort_values("date")
                    .groupby("scheme_code")
                    .last()
                    .reset_index()[["scheme_code", "scheme_name", "date", "nav"]]
        )
        print(snapshot.to_string(index=False))
    else:
        combined = pd.DataFrame()
        print("\n  ⚠  No data fetched for any scheme.")

    return combined


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  live_nav_fetch.py — Mutual Fund NAV Fetcher")
    print(f"  Run at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Task 4 ──
    hdfc_df = task4_fetch_hdfc_top100()

    # ── Task 5 ──
    five_df = task5_fetch_five_schemes()

    print(f"\n{'='*60}")
    print("  ✅  live_nav_fetch.py — ALL TASKS COMPLETE")
    print(f"{'='*60}\n")

    # ── Quick verification print ──
    print("  Files written to data/raw/:")
    for f in sorted(os.listdir(RAW_DIR)):
        if "live" in f or "five" in f:
            size = os.path.getsize(os.path.join(RAW_DIR, f))
            print(f"    {f}  ({size/1024:.1f} KB)")
