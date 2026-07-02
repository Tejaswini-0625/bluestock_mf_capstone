"""
recommender.py
==============
Simple Mutual Fund Recommender System
Day 6 — Bluestock Fintech Capstone

Usage:
    python recommender.py

Input : Risk appetite — Low / Moderate / High
Output: Top 3 fund recommendations ranked by Sharpe Ratio

Author: Tejaswini
"""

import os
import pandas as pd

RAW = "data/raw"

# ── Risk Appetite → Risk Category Mapping ──────────────────
RISK_MAP = {
    "Low":      ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High"],
}

RISK_DESCRIPTIONS = {
    "Low":      "Debt/Liquid funds with capital preservation focus",
    "Moderate": "Large Cap/Hybrid funds with balanced growth",
    "High":     "Mid Cap/Small Cap funds with aggressive growth",
}


def load_data():
    """Load fund master and performance data."""
    fund = pd.read_csv(f"{RAW}/01_fund_master.csv")
    perf = pd.read_csv(f"{RAW}/07_scheme_performance.csv")
    return fund, perf


def recommend_funds(risk_appetite: str, fund: pd.DataFrame,
                    perf: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """
    Recommend top N funds based on investor risk appetite.

    Logic:
      1. Filter funds matching investor's risk_category
      2. Merge with performance metrics
      3. Rank by Sharpe Ratio (best risk-adjusted return)
      4. Return top N recommendations

    Args:
        risk_appetite : "Low", "Moderate", or "High"
        fund          : fund_master DataFrame
        perf          : scheme_performance DataFrame
        top_n         : Number of recommendations (default 3)

    Returns:
        DataFrame with ranked fund recommendations
    """
    risk_appetite = risk_appetite.strip().title()

    if risk_appetite not in RISK_MAP:
        print(f"\n  ❌ Invalid input '{risk_appetite}'")
        print(f"     Please enter one of: Low / Moderate / High")
        return pd.DataFrame()

    valid_categories = RISK_MAP[risk_appetite]

    # Filter matching funds
    matching = fund[fund["risk_category"].isin(valid_categories)].copy()

    if len(matching) == 0:
        print(f"  ⚠  No funds found for: {risk_appetite}")
        return pd.DataFrame()

    # Merge with performance
    reco = matching.merge(
        perf[["amfi_code","sharpe_ratio","sortino_ratio",
              "return_1yr_pct","return_3yr_pct","return_5yr_pct",
              "max_drawdown_pct","aum_crore","morningstar_rating"]],
        on="amfi_code", how="left"
    ).dropna(subset=["sharpe_ratio"])

    # Rank by Sharpe Ratio
    reco = reco.sort_values("sharpe_ratio", ascending=False).head(top_n)
    reco = reco.reset_index(drop=True)
    reco.index += 1

    return reco[["scheme_name","fund_house","sub_category","plan",
                 "risk_category","expense_ratio_pct","sharpe_ratio",
                 "return_3yr_pct","max_drawdown_pct",
                 "aum_crore","morningstar_rating"]]


def print_recommendation(risk_appetite: str, result: pd.DataFrame) -> None:
    """Print formatted recommendation table."""
    print(f"\n{'='*70}")
    print(f"  📊 FUND RECOMMENDATIONS — {risk_appetite.upper()} RISK APPETITE")
    print(f"  {RISK_DESCRIPTIONS.get(risk_appetite, '')}")
    print(f"{'='*70}")

    if result.empty:
        print("  No recommendations available.")
        return

    for rank, row in result.iterrows():
        print(f"\n  #{rank} — {row['scheme_name']}")
        print(f"       Fund House    : {row['fund_house']}")
        print(f"       Category      : {row['sub_category']} ({row['plan']})")
        print(f"       Sharpe Ratio  : {row['sharpe_ratio']:.3f}")
        print(f"       3yr Return    : {row['return_3yr_pct']:.2f}%")
        print(f"       Expense Ratio : {row['expense_ratio_pct']:.2f}%")
        print(f"       Max Drawdown  : {row['max_drawdown_pct']:.2f}%")
        print(f"       AUM           : ₹{row['aum_crore']:,} Crore")
        print(f"       ⭐ Rating     : {'⭐' * int(row['morningstar_rating'])}")


def main():
    print("\n" + "="*70)
    print("  🏦 BLUESTOCK FINTECH — MUTUAL FUND RECOMMENDER")
    print("  Powered by Sharpe Ratio Ranking & Risk-Category Matching")
    print("="*70)

    # Load data
    fund, perf = load_data()

    # Interactive input
    print("\n  Risk Appetite Options:")
    print("    Low      — Suitable for conservative investors")
    print("    Moderate — Suitable for balanced investors")
    print("    High     — Suitable for aggressive investors")

    risk = input("\n  Enter your risk appetite (Low / Moderate / High): ").strip()

    result = recommend_funds(risk, fund, perf)
    print_recommendation(risk, result)

    # Save to CSV
    if not result.empty:
        out_path = f"reports/recommendations_{risk.lower()}.csv"
        result.to_csv(out_path, encoding="utf-8")
        print(f"\n  💾 Saved to: {out_path}")

    print(f"\n{'='*70}")
    print("  ⚠  Disclaimer: This is for educational purposes only.")
    print("     Past performance does not guarantee future returns.")
    print("     Please consult a SEBI-registered advisor before investing.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Demo mode — show all 3 risk levels
    fund, perf = load_data()
    for appetite in ["Low", "Moderate", "High"]:
        result = recommend_funds(appetite, fund, perf)
        print_recommendation(appetite, result)
