"""
advanced_analytics.py
=====================
Day 6 — Mutual Fund Analytics Project
Tasks:
  1. Historical VaR (95%) & CVaR for all 40 schemes
  2. Rolling 90-day Sharpe for 5 key funds
  3. Investor cohort analysis by first transaction year
  4. SIP continuity analysis — flag at-risk investors
  5. Simple fund recommender by risk appetite
  6. Sector HHI concentration index per equity fund
  7. Outputs: var_cvar_report.csv, rolling_sharpe_chart.png

Author: Tejaswini
"""

import os, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

RAW    = "data/raw"
OUT    = "reports/charts"
REP    = "reports"
os.makedirs(OUT, exist_ok=True)
os.makedirs(REP, exist_ok=True)

# ── Style ──────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f1117", "axes.facecolor": "#1a1d2e",
    "axes.edgecolor": "#3a3d5c",   "axes.labelcolor": "#e0e0e0",
    "xtick.color": "#a0a0b0",      "ytick.color": "#a0a0b0",
    "text.color": "#e0e0e0",       "grid.color": "#2a2d4e",
    "grid.linestyle": "--",        "grid.alpha": 0.4, "font.size": 10,
})
PALETTE = ["#7c6af7","#3ec9d6","#f7c948","#f76c6c","#4ecb71",
           "#f7934c","#a87cf7","#5bc8fa","#fa7eb0","#b0fa5b"]

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  ✅ Saved chart: {name}")

SEP = "=" * 65

# ── Load Data ──────────────────────────────────────────────
print(f"\n{SEP}\n  Loading data...\n{SEP}")
nav   = pd.read_csv(f"{RAW}/02_nav_history.csv", parse_dates=["date"])
fund  = pd.read_csv(f"{RAW}/01_fund_master.csv")
trans = pd.read_csv(f"{RAW}/08_investor_transactions.csv",
                    parse_dates=["transaction_date"])
hold  = pd.read_csv(f"{RAW}/09_portfolio_holdings.csv")
perf  = pd.read_csv(f"{RAW}/07_scheme_performance.csv")

nav = nav.merge(fund[["amfi_code","scheme_name","sub_category",
                       "plan","risk_category","fund_house"]],
                on="amfi_code", how="left")
nav.sort_values(["amfi_code","date"], inplace=True)
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
nav_clean = nav.dropna(subset=["daily_return"]).copy()

print(f"  NAV records   : {len(nav_clean):,}")
print(f"  Transactions  : {len(trans):,}")
print(f"  Holdings      : {len(hold):,}")


# ══════════════════════════════════════════════════════════
# TASK 1 — Historical VaR (95%) & CVaR
# ══════════════════════════════════════════════════════════
print(f"\n{SEP}\n  TASK 1 — HISTORICAL VaR (95%) & CVaR\n{SEP}")

var_rows = []
for code, grp in nav_clean.groupby("amfi_code"):
    r = grp["daily_return"].dropna()
    if len(r) < 50:
        continue

    # VaR: 5th percentile (worst 5% of daily returns)
    var_95 = np.percentile(r, 5)

    # CVaR (Expected Shortfall): mean of returns below VaR
    cvar_95 = r[r <= var_95].mean()

    # Annualised VaR
    var_ann  = var_95  * np.sqrt(252)
    cvar_ann = cvar_95 * np.sqrt(252)

    var_rows.append({
        "amfi_code":         code,
        "scheme_name":       grp["scheme_name"].iloc[0],
        "fund_house":        grp["fund_house"].iloc[0],
        "sub_category":      grp["sub_category"].iloc[0],
        "plan":              grp["plan"].iloc[0],
        "risk_category":     grp["risk_category"].iloc[0],
        "var_95_daily_pct":  round(var_95  * 100, 4),
        "cvar_95_daily_pct": round(cvar_95 * 100, 4),
        "var_95_ann_pct":    round(var_ann  * 100, 2),
        "cvar_95_ann_pct":   round(cvar_ann * 100, 2),
        "observations":      len(r),
    })

var_df = pd.DataFrame(var_rows).sort_values("var_95_daily_pct")

print(f"\n  Top 10 Riskiest Funds (Highest VaR):")
print(var_df[["scheme_name","var_95_daily_pct","cvar_95_daily_pct",
              "sub_category"]].head(10).to_string(index=False))

# Save
var_path = os.path.join(REP, "var_cvar_report.csv")
var_df.to_csv(var_path, index=False, encoding="utf-8")
print(f"\n  ✅ Saved: {var_path}")

# VaR Bar Chart
fig, ax = plt.subplots(figsize=(13, 7))
top15 = var_df.head(15)
x = np.arange(len(top15))
short_names = (top15["scheme_name"]
               .str.replace(" - Direct Plan - Growth","")
               .str.replace(" - Regular Plan - Growth","")
               .str[:28])
ax.barh(short_names[::-1], top15["var_95_daily_pct"].abs()[::-1],
        color="#f76c6c", alpha=0.85, label="VaR 95%")
ax.barh(short_names[::-1], top15["cvar_95_daily_pct"].abs()[::-1],
        color="#f7934c", alpha=0.6, label="CVaR 95%")
ax.set_title("Historical VaR & CVaR (95%) — Riskiest 15 Funds",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Daily Loss (%)")
ax.legend(fontsize=9)
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "var_cvar_chart.png")


# ══════════════════════════════════════════════════════════
# TASK 2 — Rolling 90-day Sharpe for 5 Key Funds
# ══════════════════════════════════════════════════════════
print(f"\n{SEP}\n  TASK 2 — ROLLING 90-DAY SHARPE RATIO\n{SEP}")

RF_DAILY = 0.065 / 252

# Pick top 5 by overall Sharpe (best representation)
top5_codes = (nav_clean.groupby("amfi_code")
              .apply(lambda g: (g["daily_return"].mean() - RF_DAILY) /
                               g["daily_return"].std() * np.sqrt(252))
              .nlargest(5).index.tolist())

fig, ax = plt.subplots(figsize=(14, 6))

for i, code in enumerate(top5_codes):
    grp = nav_clean[nav_clean["amfi_code"]==code].sort_values("date").copy()
    r   = grp.set_index("date")["daily_return"]

    rolling_sharpe = (
        (r.rolling(90).mean() - RF_DAILY) /
        r.rolling(90).std()
    ) * np.sqrt(252)

    name = grp["scheme_name"].iloc[0].replace(" - Direct Plan - Growth","").replace(" - Regular Plan - Growth","")[:28]
    ax.plot(rolling_sharpe.index, rolling_sharpe.values,
            color=PALETTE[i], linewidth=1.8, label=name, alpha=0.9)

ax.axhline(0, color="#888", linestyle="--", linewidth=1, alpha=0.5)
ax.axhline(1, color="#4ecb71", linestyle=":", linewidth=1, alpha=0.5, label="Sharpe = 1 (Good)")
ax.set_title("Rolling 90-Day Sharpe Ratio — Top 5 Funds (Rf = 6.5%)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Date"); ax.set_ylabel("Rolling Sharpe Ratio")
ax.legend(fontsize=8, framealpha=0.2)
ax.grid(True)
fig.tight_layout()
save(fig, "rolling_sharpe_chart.png")
print(f"  Rolling Sharpe computed for {len(top5_codes)} funds")


# ══════════════════════════════════════════════════════════
# TASK 3 — Investor Cohort Analysis
# ══════════════════════════════════════════════════════════
print(f"\n{SEP}\n  TASK 3 — INVESTOR COHORT ANALYSIS\n{SEP}")

trans["year"] = trans["transaction_date"].dt.year

# First transaction year per investor
first_year = (trans.groupby("investor_id")["transaction_date"]
              .min().dt.year.reset_index())
first_year.columns = ["investor_id","cohort_year"]
trans = trans.merge(first_year, on="investor_id", how="left")

# SIP only for amount analysis
sip_trans = trans[trans["transaction_type"]=="SIP"]

cohort = (sip_trans.groupby("cohort_year").agg(
    num_investors    = ("investor_id", "nunique"),
    avg_sip_amount   = ("amount_inr", "mean"),
    total_invested   = ("amount_inr", "sum"),
    num_transactions = ("investor_id", "count"),
).round(2).reset_index())

# Top fund preference per cohort
top_fund = (sip_trans.groupby(["cohort_year","amfi_code"])
            .size().reset_index(name="count")
            .sort_values("count", ascending=False)
            .groupby("cohort_year").first().reset_index())
top_fund = top_fund.merge(fund[["amfi_code","scheme_name"]], on="amfi_code", how="left")
top_fund = top_fund[["cohort_year","scheme_name"]].rename(columns={"scheme_name":"top_fund"})

cohort = cohort.merge(top_fund, on="cohort_year", how="left")

print(f"\n  Investor Cohort Table:")
print(cohort.to_string(index=False))

cohort.to_csv(os.path.join(REP, "cohort_analysis.csv"), index=False, encoding="utf-8")
print(f"\n  ✅ Saved: reports/cohort_analysis.csv")

# Cohort Bar Chart
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(cohort["cohort_year"].astype(str),
       cohort["avg_sip_amount"], color=PALETTE[:len(cohort)], alpha=0.88)
for i, (yr, amt) in enumerate(zip(cohort["cohort_year"], cohort["avg_sip_amount"])):
    ax.text(i, amt + 50, f"₹{amt:,.0f}", ha="center", fontsize=9)
ax.set_title("Average SIP Amount by Investor Cohort Year",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Cohort Year (First Transaction)"); ax.set_ylabel("Avg SIP Amount (₹)")
ax.grid(True, axis="y")
fig.tight_layout()
save(fig, "cohort_analysis_chart.png")


# ══════════════════════════════════════════════════════════
# TASK 4 — SIP Continuity Analysis
# ══════════════════════════════════════════════════════════
print(f"\n{SEP}\n  TASK 4 — SIP CONTINUITY ANALYSIS\n{SEP}")

sip_df = (trans[trans["transaction_type"]=="SIP"]
          .sort_values(["investor_id","transaction_date"])
          .copy())

# Investors with 6+ SIP transactions
sip_counts = sip_df.groupby("investor_id").size()
eligible   = sip_counts[sip_counts >= 6].index

sip_eligible = sip_df[sip_df["investor_id"].isin(eligible)].copy()

# Compute avg gap between SIP dates per investor
sip_eligible["prev_date"] = sip_eligible.groupby("investor_id")["transaction_date"].shift(1)
sip_eligible["gap_days"]  = (sip_eligible["transaction_date"] -
                              sip_eligible["prev_date"]).dt.days

gap_stats = (sip_eligible.groupby("investor_id")["gap_days"]
             .agg(avg_gap_days="mean", max_gap_days="max", sip_count="count")
             .reset_index())

# Flag at-risk investors (avg gap > 35 days)
gap_stats["status"] = gap_stats["avg_gap_days"].apply(
    lambda x: "At-Risk" if x > 35 else "Regular")

at_risk  = gap_stats[gap_stats["status"]=="At-Risk"]
regular  = gap_stats[gap_stats["status"]=="Regular"]

print(f"\n  Total eligible investors (6+ SIPs): {len(gap_stats):,}")
print(f"  Regular investors (gap ≤ 35 days) : {len(regular):,}")
print(f"  At-Risk investors (gap > 35 days) : {len(at_risk):,}")
print(f"  SIP continuity rate               : {len(regular)/len(gap_stats)*100:.1f}%")

print(f"\n  At-Risk Sample (first 10):")
print(at_risk[["investor_id","avg_gap_days","max_gap_days","sip_count"]]
      .head(10).round(1).to_string(index=False))

gap_stats.to_csv(os.path.join(REP, "sip_continuity.csv"), index=False, encoding="utf-8")
print(f"\n  ✅ Saved: reports/sip_continuity.csv")

# SIP Continuity Pie
fig, ax = plt.subplots(figsize=(7, 7))
sizes  = [len(regular), len(at_risk)]
labels = [f"Regular\n({len(regular):,})", f"At-Risk\n({len(at_risk):,})"]
ax.pie(sizes, labels=labels, autopct="%1.1f%%",
       colors=["#4ecb71","#f76c6c"], startangle=90,
       wedgeprops={"edgecolor":"#0f1117","linewidth":2},
       textprops={"color":"#e0e0e0"})
ax.set_title("SIP Continuity Analysis — Regular vs At-Risk Investors",
             fontsize=12, fontweight="bold", pad=12)
fig.tight_layout()
save(fig, "sip_continuity_chart.png")


# ══════════════════════════════════════════════════════════
# TASK 5 — Simple Fund Recommender
# ══════════════════════════════════════════════════════════
print(f"\n{SEP}\n  TASK 5 — FUND RECOMMENDER\n{SEP}")

# Map risk appetite to risk_category values in dataset
RISK_MAP = {
    "Low":      ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High"],
}

def recommend_funds(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Recommend top N funds based on investor risk appetite.
    Matches risk appetite to fund risk_category and ranks by Sharpe ratio.

    Args:
        risk_appetite : "Low", "Moderate", or "High"
        top_n         : Number of funds to recommend (default 3)

    Returns:
        DataFrame with top fund recommendations
    """
    risk_appetite = risk_appetite.strip().title()
    if risk_appetite not in RISK_MAP:
        print(f"  ⚠  Invalid risk appetite. Choose: Low / Moderate / High")
        return pd.DataFrame()

    valid_categories = RISK_MAP[risk_appetite]

    # Get funds matching risk category
    matching_funds = fund[fund["risk_category"].isin(valid_categories)].copy()

    if len(matching_funds) == 0:
        print(f"  ⚠  No funds found for risk appetite: {risk_appetite}")
        return pd.DataFrame()

    # Merge with performance data for Sharpe ratio
    reco = matching_funds.merge(
        perf[["amfi_code","sharpe_ratio","return_3yr_pct",
              "max_drawdown_pct","aum_crore"]],
        on="amfi_code", how="left"
    ).dropna(subset=["sharpe_ratio"])

    # Rank by Sharpe ratio
    reco = reco.sort_values("sharpe_ratio", ascending=False).head(top_n)

    result = reco[["scheme_name","fund_house","sub_category","plan",
                   "risk_category","sharpe_ratio","return_3yr_pct",
                   "expense_ratio_pct","aum_crore"]].reset_index(drop=True)
    result.index += 1  # 1-based ranking

    return result

# Demo — run recommender for all 3 risk levels
for appetite in ["Low", "Moderate", "High"]:
    print(f"\n  📋 Recommendations for {appetite} risk appetite:")
    result = recommend_funds(appetite)
    if not result.empty:
        print(result[["scheme_name","sub_category","sharpe_ratio",
                       "return_3yr_pct","expense_ratio_pct"]].to_string())


# ══════════════════════════════════════════════════════════
# TASK 6 — Sector HHI Concentration
# ══════════════════════════════════════════════════════════
print(f"\n{SEP}\n  TASK 6 — SECTOR HHI CONCENTRATION INDEX\n{SEP}")

equity_codes = fund[fund["category"]=="Equity"]["amfi_code"].tolist()
eq_hold = hold[hold["amfi_code"].isin(equity_codes)].copy()

hhi_rows = []
for code, grp in eq_hold.groupby("amfi_code"):
    # Normalise weights to sum to 100
    total_wt = grp["weight_pct"].sum()
    if total_wt == 0: continue

    weights_norm = grp["weight_pct"] / total_wt * 100

    # HHI = sum of squared weights (in % form → divide by 100 for 0-1 scale)
    hhi = ((weights_norm / 100) ** 2).sum()

    # Get scheme name
    fname = fund.loc[fund["amfi_code"]==code, "scheme_name"]
    fname = fname.values[0] if len(fname) > 0 else str(code)

    # Top sector
    top_sector = grp.loc[grp["weight_pct"].idxmax(), "sector"]
    top_weight = grp["weight_pct"].max()

    hhi_rows.append({
        "amfi_code":      code,
        "scheme_name":    fname,
        "hhi_score":      round(hhi, 4),
        "concentration":  "High" if hhi > 0.15 else "Moderate" if hhi > 0.10 else "Low",
        "top_sector":     top_sector,
        "top_sector_wt":  round(top_weight, 2),
        "num_stocks":     len(grp),
        "num_sectors":    grp["sector"].nunique(),
    })

hhi_df = pd.DataFrame(hhi_rows).sort_values("hhi_score", ascending=False)
print(f"\n  HHI Concentration Table:")
print(hhi_df[["scheme_name","hhi_score","concentration",
              "top_sector","num_stocks"]].to_string(index=False))

hhi_df.to_csv(os.path.join(REP, "hhi_concentration.csv"), index=False, encoding="utf-8")
print(f"\n  ✅ Saved: reports/hhi_concentration.csv")

# HHI Chart
fig, ax = plt.subplots(figsize=(12, 7))
short = (hhi_df["scheme_name"]
         .str.replace(" - Direct Plan - Growth","")
         .str.replace(" - Regular Plan - Growth","")
         .str[:28])
colors_hhi = ["#f76c6c" if c=="High" else "#f7c948" if c=="Moderate" else "#4ecb71"
              for c in hhi_df["concentration"]]
ax.barh(short[::-1], hhi_df["hhi_score"][::-1],
        color=colors_hhi[::-1], alpha=0.88)
legend_patches = [
    mpatches.Patch(color="#f76c6c", label="High Concentration"),
    mpatches.Patch(color="#f7c948", label="Moderate"),
    mpatches.Patch(color="#4ecb71", label="Low Concentration"),
]
ax.legend(handles=legend_patches, fontsize=9)
ax.axvline(0.15, color="#f76c6c", linestyle="--", linewidth=1, alpha=0.7)
ax.axvline(0.10, color="#f7c948", linestyle="--", linewidth=1, alpha=0.7)
ax.set_title("Sector HHI Concentration Index — Equity Funds",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("HHI Score (higher = more concentrated)")
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "hhi_concentration_chart.png")


print(f"\n{SEP}")
print("  ✅  advanced_analytics.py — ALL TASKS COMPLETE")
print(f"  Reports → {REP}/")
print(f"  Charts  → {OUT}/")
print(SEP)
