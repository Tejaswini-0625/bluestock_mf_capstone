"""
performance_analytics.py
========================
Day 4 — Mutual Fund Analytics Project
Tasks:
  1. Daily returns
  2. CAGR 1yr/3yr/5yr
  3. Sharpe Ratio (Rf=6.5%)
  4. Sortino Ratio
  5. Alpha & Beta (OLS regression vs Nifty 100)
  6. Maximum Drawdown
  7. Fund Scorecard (0-100)
  8. Benchmark comparison chart + tracking error

Author: Tejaswini
"""

import os, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

RAW    = "data/raw"
OUT    = "reports/charts"
os.makedirs(OUT, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f1117", "axes.facecolor": "#1a1d2e",
    "axes.edgecolor": "#3a3d5c",   "axes.labelcolor": "#e0e0e0",
    "xtick.color": "#a0a0b0",      "ytick.color": "#a0a0b0",
    "text.color": "#e0e0e0",       "grid.color": "#2a2d4e",
    "grid.linestyle": "--",        "grid.alpha": 0.4,
    "font.size": 10,
})
PALETTE = ["#7c6af7","#3ec9d6","#f7c948","#f76c6c","#4ecb71",
           "#f7934c","#a87cf7","#5bc8fa","#fa7eb0","#b0fa5b"]

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  ✅ Saved: {name}")

SEPARATOR = "=" * 65

# ── Load Data ──────────────────────────────────────────────────
print(f"\n{SEPARATOR}")
print("  Loading data...")
print(SEPARATOR)

nav   = pd.read_csv(f"{RAW}/02_nav_history.csv", parse_dates=["date"])
fund  = pd.read_csv(f"{RAW}/01_fund_master.csv")
bench = pd.read_csv(f"{RAW}/10_benchmark_indices.csv", parse_dates=["date"])

nav = nav.merge(fund[["amfi_code","scheme_name","sub_category",
                       "plan","expense_ratio_pct","fund_house"]], 
                on="amfi_code", how="left")
nav.sort_values(["amfi_code","date"], inplace=True)
nav.reset_index(drop=True, inplace=True)

RF_DAILY = 0.065 / 252   # Risk-free rate daily (6.5% annual)
TRADING_DAYS = 252

print(f"  NAV records : {len(nav):,}")
print(f"  Funds       : {nav['amfi_code'].nunique()}")
print(f"  Date range  : {nav['date'].min().date()} → {nav['date'].max().date()}")


# ══════════════════════════════════════════════════════════════
# TASK 1 — Daily Returns
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 1 — DAILY RETURNS")
print(SEPARATOR)

nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
nav_clean = nav.dropna(subset=["daily_return"]).copy()

print(f"  Returns computed: {len(nav_clean):,} rows")
print(f"\n  Distribution stats (all funds):")
print(nav_clean["daily_return"].describe().round(6).to_string())

# Validate — most returns should be between -10% and +10%
extreme = nav_clean[(nav_clean["daily_return"] < -0.1) | 
                    (nav_clean["daily_return"] > 0.1)]
print(f"\n  Extreme returns (>|10%|): {len(extreme)} rows — "
      f"{'✅ reasonable' if len(extreme) < 50 else '⚠ check data'}")


# ══════════════════════════════════════════════════════════════
# TASK 2 — CAGR 1yr / 3yr / 5yr
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 2 — CAGR COMPUTATION")
print(SEPARATOR)

def compute_cagr(df, years):
    """Compute CAGR for each fund over given number of years."""
    results = []
    end_date = df["date"].max()
    start_date = end_date - pd.DateOffset(years=years)

    for code, grp in df.groupby("amfi_code"):
        grp = grp.sort_values("date")
        # Get closest available dates
        end_nav_row   = grp[grp["date"] <= end_date].iloc[-1] if len(grp[grp["date"] <= end_date]) > 0 else None
        start_nav_row = grp[grp["date"] >= start_date].iloc[0] if len(grp[grp["date"] >= start_date]) > 0 else None

        if end_nav_row is None or start_nav_row is None:
            continue

        nav_end   = end_nav_row["nav"]
        nav_start = start_nav_row["nav"]

        if nav_start <= 0:
            continue

        # Actual years between dates
        actual_years = (end_nav_row["date"] - start_nav_row["date"]).days / 365.25
        if actual_years < years * 0.8:   # need at least 80% of period
            continue

        cagr = (nav_end / nav_start) ** (1 / actual_years) - 1
        results.append({
            "amfi_code":    code,
            "scheme_name":  end_nav_row["scheme_name"],
            "fund_house":   end_nav_row["fund_house"],
            "sub_category": end_nav_row["sub_category"],
            "plan":         end_nav_row["plan"],
            f"cagr_{years}yr_pct": round(cagr * 100, 2),
        })
    return pd.DataFrame(results)

cagr_1  = compute_cagr(nav, 1)
cagr_3  = compute_cagr(nav, 3)
cagr_5  = compute_cagr(nav, 5)

# Merge into one CAGR table
cagr = cagr_1.merge(cagr_3[["amfi_code","cagr_3yr_pct"]], on="amfi_code", how="outer")
cagr = cagr.merge(cagr_5[["amfi_code","cagr_5yr_pct"]], on="amfi_code", how="outer")

print(f"\n  CAGR Table ({len(cagr)} funds):")
print(cagr[["scheme_name","cagr_1yr_pct","cagr_3yr_pct","cagr_5yr_pct"]]
      .sort_values("cagr_3yr_pct", ascending=False)
      .head(10).to_string(index=False))


# ══════════════════════════════════════════════════════════════
# TASK 3 — Sharpe Ratio
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 3 — SHARPE RATIO (Rf = 6.5%)")
print(SEPARATOR)

sharpe_rows = []
for code, grp in nav_clean.groupby("amfi_code"):
    grp = grp.sort_values("date")
    r   = grp["daily_return"]
    excess_r  = r - RF_DAILY
    std_r     = r.std()
    if std_r == 0: continue
    sharpe    = (excess_r.mean() / std_r) * np.sqrt(TRADING_DAYS)
    sharpe_rows.append({
        "amfi_code":    code,
        "scheme_name":  grp["scheme_name"].iloc[0],
        "fund_house":   grp["fund_house"].iloc[0],
        "sub_category": grp["sub_category"].iloc[0],
        "plan":         grp["plan"].iloc[0],
        "sharpe_ratio": round(sharpe, 4),
        "ann_return_pct": round(r.mean() * TRADING_DAYS * 100, 2),
        "ann_std_pct":    round(std_r * np.sqrt(TRADING_DAYS) * 100, 2),
    })

sharpe_df = pd.DataFrame(sharpe_rows).sort_values("sharpe_ratio", ascending=False)
sharpe_df["sharpe_rank"] = range(1, len(sharpe_df)+1)

print(f"\n  Top 10 by Sharpe Ratio:")
print(sharpe_df[["scheme_name","sharpe_ratio","ann_return_pct","ann_std_pct","sharpe_rank"]]
      .head(10).to_string(index=False))


# ══════════════════════════════════════════════════════════════
# TASK 4 — Sortino Ratio
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 4 — SORTINO RATIO")
print(SEPARATOR)

sortino_rows = []
for code, grp in nav_clean.groupby("amfi_code"):
    grp = grp.sort_values("date")
    r   = grp["daily_return"]
    excess_r     = r - RF_DAILY
    downside_r   = r[r < 0]
    downside_std = downside_r.std()
    if downside_std == 0: continue
    sortino = (excess_r.mean() / downside_std) * np.sqrt(TRADING_DAYS)
    sortino_rows.append({
        "amfi_code":      code,
        "scheme_name":    grp["scheme_name"].iloc[0],
        "sortino_ratio":  round(sortino, 4),
        "downside_std_pct": round(downside_std * np.sqrt(TRADING_DAYS) * 100, 2),
    })

sortino_df = pd.DataFrame(sortino_rows).sort_values("sortino_ratio", ascending=False)
sortino_df["sortino_rank"] = range(1, len(sortino_df)+1)

print(f"\n  Top 10 by Sortino Ratio:")
print(sortino_df[["scheme_name","sortino_ratio","downside_std_pct","sortino_rank"]]
      .head(10).to_string(index=False))


# ══════════════════════════════════════════════════════════════
# TASK 5 — Alpha & Beta (OLS vs Nifty 100)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 5 — ALPHA & BETA (OLS vs NIFTY100)")
print(SEPARATOR)

# Prepare Nifty 100 benchmark returns
nifty100 = (bench[bench["index_name"]=="NIFTY100"]
            .sort_values("date")
            .set_index("date")["close_value"]
            .pct_change()
            .dropna())
nifty100.name = "nifty100_return"

alpha_beta_rows = []
for code, grp in nav_clean.groupby("amfi_code"):
    grp = grp.sort_values("date").set_index("date")
    fund_ret = grp["daily_return"]

    # Align dates
    aligned = pd.concat([fund_ret, nifty100], axis=1).dropna()
    if len(aligned) < 100: continue

    x = aligned["nifty100_return"].values
    y = aligned["daily_return"].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    beta  = round(slope, 4)
    # Alpha annualised: intercept * 252
    alpha = round(intercept * TRADING_DAYS * 100, 4)
    r_sq  = round(r_value ** 2, 4)

    alpha_beta_rows.append({
        "amfi_code":    code,
        "scheme_name":  grp["scheme_name"].iloc[0],
        "fund_house":   grp["fund_house"].iloc[0],
        "sub_category": grp["sub_category"].iloc[0],
        "plan":         grp["plan"].iloc[0],
        "alpha_ann_pct": alpha,
        "beta":          beta,
        "r_squared":     r_sq,
        "p_value":       round(p_value, 4),
        "data_points":   len(aligned),
    })

alpha_beta_df = pd.DataFrame(alpha_beta_rows).sort_values("alpha_ann_pct", ascending=False)
alpha_beta_df["alpha_rank"] = range(1, len(alpha_beta_df)+1)

print(f"\n  Alpha & Beta Table ({len(alpha_beta_df)} funds):")
print(alpha_beta_df[["scheme_name","alpha_ann_pct","beta","r_squared","alpha_rank"]]
      .head(10).to_string(index=False))

# Save alpha_beta.csv
alpha_beta_df.to_csv("reports/alpha_beta.csv", index=False, encoding="utf-8")
print(f"\n  ✅ Saved: reports/alpha_beta.csv")


# ══════════════════════════════════════════════════════════════
# TASK 6 — Maximum Drawdown
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 6 — MAXIMUM DRAWDOWN")
print(SEPARATOR)

mdd_rows = []
for code, grp in nav.groupby("amfi_code"):
    grp = grp.sort_values("date").copy()
    grp["running_max"] = grp["nav"].cummax()
    grp["drawdown"]    = grp["nav"] / grp["running_max"] - 1

    max_dd     = grp["drawdown"].min()
    max_dd_row = grp.loc[grp["drawdown"].idxmin()]

    # Find peak (start of drawdown)
    peak_date = grp.loc[grp["date"] <= max_dd_row["date"], "running_max"].idxmax()
    peak_date = grp.loc[peak_date, "date"] if peak_date in grp.index else max_dd_row["date"]

    # Find recovery (first date NAV >= running_max after trough)
    trough_date = max_dd_row["date"]
    trough_nav  = max_dd_row["nav"]
    recovery_df = grp[(grp["date"] > trough_date) & 
                      (grp["nav"] >= max_dd_row["running_max"])]
    recovery_date = recovery_df["date"].iloc[0] if len(recovery_df) > 0 else "Not yet recovered"

    mdd_rows.append({
        "amfi_code":       code,
        "scheme_name":     grp["scheme_name"].iloc[0],
        "fund_house":      grp["fund_house"].iloc[0],
        "sub_category":    grp["sub_category"].iloc[0],
        "max_drawdown_pct": round(max_dd * 100, 2),
        "trough_date":     str(trough_date.date()),
        "recovery_date":   str(recovery_date) if isinstance(recovery_date, str) 
                           else str(recovery_date.date()),
        "drawdown_duration_days": (trough_date - peak_date).days if isinstance(peak_date, pd.Timestamp) else 0,
    })

mdd_df = pd.DataFrame(mdd_rows).sort_values("max_drawdown_pct")
mdd_df["mdd_rank"] = range(1, len(mdd_df)+1)   # worst DD = rank 1

print(f"\n  Worst 10 Maximum Drawdowns:")
print(mdd_df[["scheme_name","max_drawdown_pct","trough_date","recovery_date"]]
      .head(10).to_string(index=False))


# ══════════════════════════════════════════════════════════════
# TASK 7 — Fund Scorecard (0–100)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 7 — FUND SCORECARD (0–100)")
print(SEPARATOR)

# Merge all metrics
scorecard = (cagr[["amfi_code","scheme_name","fund_house",
                    "sub_category","plan","cagr_3yr_pct"]]
             .merge(sharpe_df[["amfi_code","sharpe_ratio","sharpe_rank","ann_std_pct"]], 
                    on="amfi_code", how="left")
             .merge(alpha_beta_df[["amfi_code","alpha_ann_pct","beta","alpha_rank"]], 
                    on="amfi_code", how="left")
             .merge(mdd_df[["amfi_code","max_drawdown_pct","mdd_rank"]], 
                    on="amfi_code", how="left")
             .merge(fund[["amfi_code","expense_ratio_pct"]], 
                    on="amfi_code", how="left"))

n = len(scorecard)

# Rank 3yr CAGR (higher = better rank 1)
scorecard["cagr_rank"] = scorecard["cagr_3yr_pct"].rank(ascending=False).astype(int)

# Expense ratio rank (lower expense = better, so rank ascending)
scorecard["exp_rank"] = scorecard["expense_ratio_pct"].rank(ascending=True).astype(int)

# MDD rank (less negative = better, rank descending of mdd_pct)
scorecard["mdd_score_rank"] = scorecard["max_drawdown_pct"].rank(ascending=False).astype(int)

# Convert ranks to scores (n - rank + 1) / n * 100
def rank_to_score(rank_series, n):
    return ((n - rank_series + 1) / n * 100).round(2)

scorecard["cagr_score"]   = rank_to_score(scorecard["cagr_rank"],       n)
scorecard["sharpe_score"] = rank_to_score(scorecard["sharpe_rank"],      n)
scorecard["alpha_score"]  = rank_to_score(scorecard["alpha_rank"],       n)
scorecard["exp_score"]    = rank_to_score(scorecard["exp_rank"],         n)
scorecard["mdd_score"]    = rank_to_score(scorecard["mdd_score_rank"],   n)

# Composite: 30% CAGR + 25% Sharpe + 20% Alpha + 15% Expense + 10% MDD
scorecard["composite_score"] = (
    0.30 * scorecard["cagr_score"]   +
    0.25 * scorecard["sharpe_score"] +
    0.20 * scorecard["alpha_score"]  +
    0.15 * scorecard["exp_score"]    +
    0.10 * scorecard["mdd_score"]
).round(2)

scorecard.sort_values("composite_score", ascending=False, inplace=True)
scorecard["final_rank"] = range(1, len(scorecard)+1)
scorecard.reset_index(drop=True, inplace=True)

print(f"\n  🏆 Fund Scorecard — Top 15:")
cols = ["scheme_name","cagr_3yr_pct","sharpe_ratio","alpha_ann_pct",
        "expense_ratio_pct","max_drawdown_pct","composite_score","final_rank"]
print(scorecard[cols].head(15).to_string(index=False))

# Save
scorecard.to_csv("reports/fund_scorecard.csv", index=False, encoding="utf-8")
print(f"\n  ✅ Saved: reports/fund_scorecard.csv")


# ══════════════════════════════════════════════════════════════
# TASK 8 — Benchmark Comparison Chart + Tracking Error
# ══════════════════════════════════════════════════════════════
print(f"\n{SEPARATOR}")
print("  TASK 8 — BENCHMARK COMPARISON + TRACKING ERROR")
print(SEPARATOR)

# Top 5 funds by composite score
top5_codes = scorecard.head(5)["amfi_code"].tolist()
top5_names = scorecard.head(5)["scheme_name"].tolist()

# 3-year window
end_dt   = nav["date"].max()
start_dt = end_dt - pd.DateOffset(years=3)

# Prepare benchmark data
nifty50  = (bench[bench["index_name"]=="NIFTY50"]
            .sort_values("date").set_index("date")["close_value"])
nifty100_price = (bench[bench["index_name"]=="NIFTY100"]
                  .sort_values("date").set_index("date")["close_value"])

fig, ax = plt.subplots(figsize=(14, 7))

tracking_errors = []
colors = PALETTE[:5]

for i, (code, name) in enumerate(zip(top5_codes, top5_names)):
    fund_nav = (nav[(nav["amfi_code"]==code) & 
                    (nav["date"] >= start_dt)]
                .sort_values("date")
                .set_index("date")["nav"])

    # Normalise to 100
    base = fund_nav.iloc[0]
    norm = fund_nav / base * 100

    short_name = name.replace(" - Direct Plan - Growth","").replace(" - Regular Plan - Growth","")[:28]
    ax.plot(norm.index, norm.values, color=colors[i],
            linewidth=2, label=short_name, alpha=0.9)

    # Tracking error vs Nifty 100
    fund_ret  = fund_nav.pct_change().dropna()
    bench_ret = nifty100_price.pct_change().dropna()
    aligned   = pd.concat([fund_ret, bench_ret], axis=1).dropna()
    aligned.columns = ["fund","bench"]
    te = (aligned["fund"] - aligned["bench"]).std() * np.sqrt(TRADING_DAYS) * 100

    tracking_errors.append({
        "scheme_name": short_name,
        "tracking_error_vs_nifty100_pct": round(te, 2)
    })
    print(f"  {short_name[:35]:<35} | TE vs NIFTY100: {te:.2f}%")

# Plot benchmarks
for bm_name, bm_series, bm_color in [
    ("NIFTY 50",  nifty50,       "#ffffff"),
    ("NIFTY 100", nifty100_price,"#aaaaaa"),
]:
    bm_3yr = bm_series[bm_series.index >= start_dt]
    if len(bm_3yr) == 0: continue
    base = bm_3yr.iloc[0]
    norm_bm = bm_3yr / base * 100
    ax.plot(norm_bm.index, norm_bm.values, color=bm_color,
            linewidth=2.5, linestyle="--", label=bm_name, alpha=0.7)

ax.set_title("Top 5 Funds vs NIFTY 50 & NIFTY 100 — 3 Year Performance\n(Normalised to 100)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Date"); ax.set_ylabel("Indexed Value (Base = 100)")
ax.legend(fontsize=8, framealpha=0.2, loc="upper left")
ax.grid(True)
fig.tight_layout()
save(fig, "benchmark_comparison.png")

# ── Scorecard Bar Chart ──────────────────────────────────────
print("\n  Generating scorecard chart...")
top20 = scorecard.head(20).copy()
top20["short_name"] = (top20["scheme_name"]
    .str.replace(" - Direct Plan - Growth","")
    .str.replace(" - Regular Plan - Growth","")
    .str[:32])

fig, ax = plt.subplots(figsize=(12, 9))
bar_colors = [PALETTE[0] if p=="Direct" else PALETTE[3] 
              for p in top20["plan"]]
bars = ax.barh(top20["short_name"][::-1], 
               top20["composite_score"][::-1],
               color=bar_colors[::-1], alpha=0.88)
for bar, val in zip(bars, top20["composite_score"][::-1]):
    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}", va="center", fontsize=8)

legend_patches = [
    mpatches.Patch(color=PALETTE[0], label="Direct Plan"),
    mpatches.Patch(color=PALETTE[3], label="Regular Plan"),
]
ax.legend(handles=legend_patches, fontsize=9)
ax.set_title("Fund Scorecard — Top 20 (Composite Score 0–100)\n"
             "30% CAGR + 25% Sharpe + 20% Alpha + 15% Expense Ratio + 10% Max DD",
             fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Composite Score (0–100)")
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "fund_scorecard_chart.png")

# ── Sharpe Ratio Chart ───────────────────────────────────────
print("  Generating Sharpe ratio chart...")
top_sharpe = sharpe_df.head(20).copy()
top_sharpe["short_name"] = (top_sharpe["scheme_name"]
    .str.replace(" - Direct Plan - Growth","")
    .str.replace(" - Regular Plan - Growth","")
    .str[:30])

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(top_sharpe["short_name"][::-1],
               top_sharpe["sharpe_ratio"][::-1],
               color=PALETTE[:20][::-1], alpha=0.88)
for bar, val in zip(bars, top_sharpe["sharpe_ratio"][::-1]):
    ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
            f"{val:.3f}", va="center", fontsize=8)
ax.set_title("Sharpe Ratio Ranking — Top 20 Funds (Rf = 6.5%)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Sharpe Ratio")
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "sharpe_ratio_chart.png")

# ── Alpha vs Beta Scatter ────────────────────────────────────
print("  Generating Alpha vs Beta scatter...")
fig, ax = plt.subplots(figsize=(11, 7))
cats = alpha_beta_df["sub_category"].unique()
cat_colors = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cats)}

for cat in cats:
    sub = alpha_beta_df[alpha_beta_df["sub_category"]==cat]
    ax.scatter(sub["beta"], sub["alpha_ann_pct"],
               color=cat_colors[cat], s=100, label=cat,
               alpha=0.8, edgecolors="white", linewidths=0.5)

# Annotate top 5 alpha
for _, row in alpha_beta_df.head(5).iterrows():
    name = row["scheme_name"].replace(" - Direct Plan - Growth","")[:20]
    ax.annotate(name, (row["beta"], row["alpha_ann_pct"]),
                textcoords="offset points", xytext=(6, 4),
                fontsize=7, color="#f7c948")

ax.axhline(0, color="#888", linestyle="--", linewidth=1, alpha=0.6)
ax.axvline(1, color="#888", linestyle="--", linewidth=1, alpha=0.6)
ax.set_title("Alpha vs Beta — All 40 Funds (vs NIFTY 100)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Beta (Market Sensitivity)"); ax.set_ylabel("Alpha (Annualised %)")
ax.legend(fontsize=8, framealpha=0.2)
ax.grid(True)
fig.tight_layout()
save(fig, "alpha_beta_scatter.png")

# ── Max Drawdown Chart ───────────────────────────────────────
print("  Generating Max Drawdown chart...")
mdd_plot = mdd_df.head(20).copy()
mdd_plot["short_name"] = (mdd_plot["scheme_name"]
    .str.replace(" - Direct Plan - Growth","")
    .str.replace(" - Regular Plan - Growth","")
    .str[:30])

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(mdd_plot["short_name"],
               mdd_plot["max_drawdown_pct"],
               color="#f76c6c", alpha=0.8)
for bar, val in zip(bars, mdd_plot["max_drawdown_pct"]):
    ax.text(val - 0.3, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}%", va="center", ha="right", fontsize=8)
ax.set_title("Maximum Drawdown — All Funds (Worst to Best)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Maximum Drawdown (%)")
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "max_drawdown_chart.png")

# ── CAGR Comparison Chart ────────────────────────────────────
print("  Generating CAGR comparison chart...")
cagr_plot = cagr.dropna(subset=["cagr_3yr_pct"]).nlargest(15, "cagr_3yr_pct").copy()
cagr_plot["short_name"] = (cagr_plot["scheme_name"]
    .str.replace(" - Direct Plan - Growth","")
    .str.replace(" - Regular Plan - Growth","")
    .str[:30])

x = np.arange(len(cagr_plot))
width = 0.25
fig, ax = plt.subplots(figsize=(14, 7))
b1 = ax.bar(x - width, cagr_plot["cagr_1yr_pct"], width, 
            color=PALETTE[0], label="1-Year CAGR", alpha=0.88)
b2 = ax.bar(x,          cagr_plot["cagr_3yr_pct"], width,
            color=PALETTE[1], label="3-Year CAGR", alpha=0.88)
b3 = ax.bar(x + width,  cagr_plot["cagr_5yr_pct"].fillna(0), width,
            color=PALETTE[2], label="5-Year CAGR", alpha=0.88)
ax.set_xticks(x)
ax.set_xticklabels(cagr_plot["short_name"], rotation=35, ha="right", fontsize=8)
ax.set_title("CAGR Comparison — Top 15 Funds (1yr / 3yr / 5yr)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("CAGR (%)")
ax.legend(fontsize=9)
ax.grid(True, axis="y")
fig.tight_layout()
save(fig, "cagr_comparison.png")

print(f"\n{SEPARATOR}")
print("  ✅ performance_analytics.py — ALL TASKS COMPLETE")
print(f"  Charts → reports/charts/")
print(f"  CSVs   → reports/")
print(SEPARATOR)
