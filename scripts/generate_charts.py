"""
EDA Chart Generator — Day 3
Generates all 15 charts as PNG files for EDA_Analysis.ipynb
Run from project root: python generate_charts.py
"""

import os, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────
RAW  = "data/raw"
PROC = "data/processed"
OUT  = "reports/charts"
os.makedirs(OUT, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f1117",
    "axes.facecolor":   "#1a1d2e",
    "axes.edgecolor":   "#3a3d5c",
    "axes.labelcolor":  "#e0e0e0",
    "xtick.color":      "#a0a0b0",
    "ytick.color":      "#a0a0b0",
    "text.color":       "#e0e0e0",
    "grid.color":       "#2a2d4e",
    "grid.linestyle":   "--",
    "grid.alpha":       0.4,
    "font.family":      "sans-serif",
    "font.size":        10,
})

PALETTE = ["#7c6af7","#3ec9d6","#f7c948","#f76c6c","#4ecb71",
           "#f7934c","#a87cf7","#5bc8fa","#fa7eb0","#b0fa5b"]

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  ✅ Saved: {name}")


# ── Load data ──────────────────────────────────────────────────
nav   = pd.read_csv(f"{RAW}/02_nav_history.csv", parse_dates=["date"])
fund  = pd.read_csv(f"{RAW}/01_fund_master.csv")
aum   = pd.read_csv(f"{RAW}/03_aum_by_fund_house.csv", parse_dates=["date"])
sip   = pd.read_csv(f"{RAW}/04_monthly_sip_inflows.csv")
cat   = pd.read_csv(f"{RAW}/05_category_inflows.csv")
folio = pd.read_csv(f"{RAW}/06_industry_folio_count.csv")
perf  = pd.read_csv(f"{RAW}/07_scheme_performance.csv")
trans = pd.read_csv(f"{RAW}/08_investor_transactions.csv",
                    parse_dates=["transaction_date"])
hold  = pd.read_csv(f"{RAW}/09_portfolio_holdings.csv")
bench = pd.read_csv(f"{RAW}/10_benchmark_indices.csv", parse_dates=["date"])

nav   = nav.merge(fund[["amfi_code","scheme_name","sub_category","plan"]], on="amfi_code", how="left")
print("Data loaded.\n")


# ══════════════════════════════════════════════════════════════
# CHART 1 — NAV Trend: 10 Direct Large Cap funds 2022-2026
# ══════════════════════════════════════════════════════════════
print("Chart 1: NAV Trend...")
lc_direct = fund[(fund["sub_category"]=="Large Cap") & (fund["plan"]=="Direct")]["amfi_code"].tolist()
nav1 = nav[nav["amfi_code"].isin(lc_direct)].copy()

fig, ax = plt.subplots(figsize=(14, 6))
for i, code in enumerate(lc_direct[:8]):
    df_  = nav1[nav1["amfi_code"]==code].sort_values("date")
    name = df_["scheme_name"].iloc[0].replace(" - Direct Plan - Growth","").replace(" Fund","")
    ax.plot(df_["date"], df_["nav"], color=PALETTE[i % len(PALETTE)],
            linewidth=1.2, label=name, alpha=0.85)

# Annotate bull run & correction
ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"),
           alpha=0.10, color="#4ecb71", label="2023 Bull Run")
ax.axvspan(pd.Timestamp("2024-09-01"), pd.Timestamp("2024-12-31"),
           alpha=0.10, color="#f76c6c", label="2024 Correction")
ax.text(pd.Timestamp("2023-04-01"), ax.get_ylim()[1]*0.95,
        "2023 Bull Run", color="#4ecb71", fontsize=9, fontweight="bold")
ax.text(pd.Timestamp("2024-09-05"), ax.get_ylim()[1]*0.95,
        "2024 Correction", color="#f76c6c", fontsize=9, fontweight="bold")

ax.set_title("NAV Trend — Large Cap Direct Funds (2022–2026)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Date"); ax.set_ylabel("NAV (₹)")
ax.legend(loc="upper left", fontsize=7, framealpha=0.2, ncol=2)
ax.grid(True)
fig.tight_layout()
save(fig, "01_nav_trend.png")


# ══════════════════════════════════════════════════════════════
# CHART 2 — AUM Grouped Bar by Fund House & Year
# ══════════════════════════════════════════════════════════════
print("Chart 2: AUM Bar Chart...")
aum["year"] = aum["date"].dt.year
aum_yr = aum.groupby(["fund_house","year"])["aum_crore"].max().reset_index()
aum_yr["aum_lakh_cr"] = aum_yr["aum_crore"] / 100000

pivot = aum_yr.pivot(index="fund_house", columns="year", values="aum_lakh_cr").fillna(0)
pivot = pivot.sort_values(pivot.columns[-1], ascending=False)

fig, ax = plt.subplots(figsize=(14, 7))
x      = np.arange(len(pivot))
years  = pivot.columns.tolist()
width  = 0.18
for i, yr in enumerate(years):
    bars = ax.bar(x + i*width, pivot[yr], width, label=str(yr),
                  color=PALETTE[i], alpha=0.88)

# Highlight SBI
sbi_idx = list(pivot.index).index("SBI Mutual Fund")
ax.annotate("SBI ₹12.5L Cr\ndominance",
            xy=(sbi_idx + (len(years)-1)*width/2, pivot.iloc[sbi_idx].max()),
            xytext=(sbi_idx + 2, pivot.iloc[sbi_idx].max() + 0.5),
            color="#f7c948", fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#f7c948", lw=1.5))

ax.set_xticks(x + width*(len(years)-1)/2)
ax.set_xticklabels(pivot.index, rotation=30, ha="right", fontsize=9)
ax.set_title("AUM by Fund House Per Year (Lakh Crore ₹)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("AUM (₹ Lakh Crore)"); ax.set_xlabel("Fund House")
ax.legend(title="Year", fontsize=9)
ax.grid(True, axis="y")
fig.tight_layout()
save(fig, "02_aum_bar.png")


# ══════════════════════════════════════════════════════════════
# CHART 3 — SIP Inflow Time Series
# ══════════════════════════════════════════════════════════════
print("Chart 3: SIP Inflow...")
sip["date"] = pd.to_datetime(sip["month"])
fig, ax = plt.subplots(figsize=(14, 5))
ax.fill_between(sip["date"], sip["sip_inflow_crore"]/1000,
                alpha=0.25, color="#7c6af7")
ax.plot(sip["date"], sip["sip_inflow_crore"]/1000,
        color="#7c6af7", linewidth=2)

# Annotate ATH
ath_row = sip.loc[sip["sip_inflow_crore"].idxmax()]
ax.annotate(f"ATH ₹31,002 Cr\n(Dec 2025)",
            xy=(ath_row["date"], ath_row["sip_inflow_crore"]/1000),
            xytext=(ath_row["date"] - pd.DateOffset(months=8),
                    ath_row["sip_inflow_crore"]/1000 - 3),
            color="#f7c948", fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#f7c948", lw=1.5))

ax.set_title("Monthly SIP Inflows — Jan 2022 to Dec 2025 (₹ '000 Crore)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Month"); ax.set_ylabel("SIP Inflow (₹ '000 Crore)")
ax.grid(True)
fig.tight_layout()
save(fig, "03_sip_inflow.png")


# ══════════════════════════════════════════════════════════════
# CHART 4 — Category Inflow Heatmap
# ══════════════════════════════════════════════════════════════
print("Chart 4: Category Heatmap...")
cat_pivot = cat.pivot(index="category", columns="month", values="net_inflow_crore").fillna(0)
fig, ax = plt.subplots(figsize=(14, 7))
sns.heatmap(cat_pivot, ax=ax, cmap="RdYlGn", linewidths=0.4,
            linecolor="#1a1d2e", annot=True, fmt=".0f",
            annot_kws={"size": 7},
            cbar_kws={"label": "Net Inflow (₹ Crore)"})
ax.set_title("Category-wise Net Inflow Heatmap (₹ Crore)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Month"); ax.set_ylabel("Fund Category")
plt.xticks(rotation=45, ha="right", fontsize=8)
plt.yticks(fontsize=8)
fig.tight_layout()
save(fig, "04_category_heatmap.png")


# ══════════════════════════════════════════════════════════════
# CHART 5a — Age Group Distribution Pie
# ══════════════════════════════════════════════════════════════
print("Chart 5a: Age Pie...")
age_counts = trans["age_group"].value_counts()
order = ["18-25","26-35","36-45","46-55","56+"]
age_counts = age_counts.reindex(order)

fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    age_counts, labels=age_counts.index, autopct="%1.1f%%",
    colors=PALETTE[:5], startangle=140,
    pctdistance=0.82, textprops={"color":"#e0e0e0"},
    wedgeprops={"edgecolor":"#0f1117","linewidth":1.5})
for at in autotexts: at.set_fontsize(9)
ax.set_title("Investor Age Group Distribution", fontsize=13, fontweight="bold", pad=12)
fig.tight_layout()
save(fig, "05a_age_pie.png")


# ══════════════════════════════════════════════════════════════
# CHART 5b — SIP Amount Box Plot by Age Group
# ══════════════════════════════════════════════════════════════
print("Chart 5b: SIP Box Plot...")
sip_only = trans[trans["transaction_type"]=="SIP"].copy()
fig, ax = plt.subplots(figsize=(10, 6))
age_order = ["18-25","26-35","36-45","46-55","56+"]
data_by_age = [sip_only[sip_only["age_group"]==ag]["amount_inr"].values for ag in age_order]
bp = ax.boxplot(data_by_age, labels=age_order, patch_artist=True,
                medianprops={"color":"#f7c948","linewidth":2},
                flierprops={"marker":"o","markersize":2,"alpha":0.3})
for patch, color in zip(bp["boxes"], PALETTE):
    patch.set_facecolor(color); patch.set_alpha(0.7)
ax.set_title("SIP Investment Amount by Age Group (₹)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Age Group"); ax.set_ylabel("SIP Amount (₹)")
ax.grid(True, axis="y")
fig.tight_layout()
save(fig, "05b_sip_boxplot.png")


# ══════════════════════════════════════════════════════════════
# CHART 5c — Gender Split
# ══════════════════════════════════════════════════════════════
print("Chart 5c: Gender Split...")
gender = trans["gender"].value_counts()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(gender, labels=gender.index, autopct="%1.1f%%",
       colors=["#7c6af7","#f76c6c"], startangle=90,
       wedgeprops={"edgecolor":"#0f1117","linewidth":2},
       textprops={"color":"#e0e0e0"})
ax.set_title("Investor Gender Split", fontsize=13, fontweight="bold", pad=12)
fig.tight_layout()
save(fig, "05c_gender_pie.png")


# ══════════════════════════════════════════════════════════════
# CHART 6a — SIP Amount by State (Horizontal Bar)
# ══════════════════════════════════════════════════════════════
print("Chart 6a: State Bar...")
state_amt = (trans.groupby("state")["amount_inr"]
             .sum().sort_values(ascending=True) / 1e7)  # in crore
top15 = state_amt.tail(15)

fig, ax = plt.subplots(figsize=(10, 8))
bars = ax.barh(top15.index, top15.values,
               color=PALETTE[:len(top15)], alpha=0.85)
for bar, val in zip(bars, top15.values):
    ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
            f"₹{val:.0f}Cr", va="center", fontsize=8, color="#e0e0e0")
ax.set_title("Total Transaction Amount by State (Top 15)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Total Amount (₹ Crore)"); ax.set_ylabel("State")
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "06a_state_bar.png")


# ══════════════════════════════════════════════════════════════
# CHART 6b — T30 vs B30 City Tier Pie
# ══════════════════════════════════════════════════════════════
print("Chart 6b: City Tier Pie...")
tier = trans["city_tier"].value_counts()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(tier, labels=tier.index, autopct="%1.1f%%",
       colors=["#3ec9d6","#f7934c"], startangle=90,
       wedgeprops={"edgecolor":"#0f1117","linewidth":2},
       textprops={"color":"#e0e0e0"})
ax.set_title("T30 vs B30 City Tier Distribution", fontsize=13, fontweight="bold", pad=12)
fig.tight_layout()
save(fig, "06b_city_tier_pie.png")


# ══════════════════════════════════════════════════════════════
# CHART 7 — Folio Count Growth Line Chart
# ══════════════════════════════════════════════════════════════
print("Chart 7: Folio Growth...")
folio["date"] = pd.to_datetime(folio["month"])
fig, ax = plt.subplots(figsize=(13, 5))

ax.plot(folio["date"], folio["total_folios_crore"], color="#7c6af7",
        linewidth=2.5, marker="o", markersize=5, label="Total Folios")
ax.fill_between(folio["date"], folio["total_folios_crore"],
                alpha=0.15, color="#7c6af7")

# Milestones
milestones = [
    ("2022-01", 13.26, "13.26 Cr\nJan 2022"),
    ("2024-01", 17.78, "17.78 Cr\nJan 2024"),
    ("2025-12", 26.12, "26.12 Cr\nDec 2025"),
]
for m_date, m_val, m_label in milestones:
    ax.annotate(m_label,
                xy=(pd.Timestamp(m_date), m_val),
                xytext=(pd.Timestamp(m_date) + pd.DateOffset(months=2), m_val + 1.2),
                color="#f7c948", fontsize=8, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#f7c948", lw=1.2))

ax.set_title("Industry Folio Count Growth (Crore)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Month"); ax.set_ylabel("Total Folios (Crore)")
ax.grid(True)
fig.tight_layout()
save(fig, "07_folio_growth.png")


# ══════════════════════════════════════════════════════════════
# CHART 8 — NAV Return Correlation Matrix
# ══════════════════════════════════════════════════════════════
print("Chart 8: Correlation Matrix...")
# Pick 10 funds with most data
top10 = nav.groupby("amfi_code").size().nlargest(10).index.tolist()
nav_pivot = nav[nav["amfi_code"].isin(top10)].pivot(
    index="date", columns="amfi_code", values="nav")
returns = nav_pivot.pct_change().dropna()

# Short names for labels
name_map = {code: fund.loc[fund["amfi_code"]==code,"scheme_name"].values[0]
            .replace(" - Direct Plan - Growth","")
            .replace(" - Regular Plan - Growth","")
            .replace(" Fund","")[:20]
            for code in top10}
returns.columns = [name_map.get(c, str(c)) for c in returns.columns]
corr = returns.corr()

fig, ax = plt.subplots(figsize=(11, 9))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, ax=ax, mask=mask, annot=True, fmt=".2f",
            cmap="coolwarm", vmin=0.5, vmax=1.0,
            linewidths=0.5, linecolor="#1a1d2e",
            annot_kws={"size": 8},
            cbar_kws={"label": "Pearson Correlation"})
ax.set_title("Daily Return Correlation Matrix — 10 Selected Funds",
             fontsize=13, fontweight="bold", pad=12)
plt.xticks(rotation=40, ha="right", fontsize=8)
plt.yticks(fontsize=8)
fig.tight_layout()
save(fig, "08_correlation_matrix.png")


# ══════════════════════════════════════════════════════════════
# CHART 9 — Sector Allocation Donut
# ══════════════════════════════════════════════════════════════
print("Chart 9: Sector Donut...")
# Only equity funds
equity_codes = fund[fund["category"]=="Equity"]["amfi_code"].tolist()
eq_hold = hold[hold["amfi_code"].isin(equity_codes)]
sector_wt = eq_hold.groupby("sector")["market_value_cr"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(9, 9))
wedges, texts, autotexts = ax.pie(
    sector_wt, labels=sector_wt.index,
    autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
    colors=PALETTE * 2, startangle=90,
    pctdistance=0.82,
    wedgeprops={"edgecolor":"#0f1117","linewidth":1.5,"width":0.55},
    textprops={"color":"#e0e0e0","fontsize":9})
for at in autotexts: at.set_fontsize(8)
ax.text(0, 0, "Sector\nAllocation", ha="center", va="center",
        fontsize=12, color="#e0e0e0", fontweight="bold")
ax.set_title("Sector Allocation — Equity Fund Portfolio Holdings",
             fontsize=13, fontweight="bold", pad=12)
fig.tight_layout()
save(fig, "09_sector_donut.png")


# ══════════════════════════════════════════════════════════════
# CHART 10 — Scheme Performance: Return vs Risk Scatter
# ══════════════════════════════════════════════════════════════
print("Chart 10: Risk-Return Scatter...")
fig, ax = plt.subplots(figsize=(11, 7))
cats = perf["category"].unique()
cat_colors = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cats)}

for cat_name in cats:
    sub = perf[perf["category"]==cat_name]
    ax.scatter(sub["std_dev_ann_pct"], sub["return_3yr_pct"],
               color=cat_colors[cat_name], s=sub["aum_crore"]/500,
               alpha=0.8, label=cat_name, edgecolors="white", linewidths=0.5)

# Annotate top 5 by return
for _, row in perf.nlargest(5, "return_3yr_pct").iterrows():
    name = row["scheme_name"].replace(" - Direct Plan - Growth","")[:22]
    ax.annotate(name, (row["std_dev_ann_pct"], row["return_3yr_pct"]),
                textcoords="offset points", xytext=(6, 4),
                fontsize=7, color="#f7c948")

ax.axhline(y=perf["return_3yr_pct"].mean(), color="#f7c948",
           linestyle="--", linewidth=1, alpha=0.6, label="Avg Return")
ax.set_title("Risk vs Return (3-Year) — Bubble Size = AUM",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Risk (Annualised Std Dev %)"); ax.set_ylabel("3-Year Return (%)")
ax.legend(fontsize=8, framealpha=0.2)
ax.grid(True)
fig.tight_layout()
save(fig, "10_risk_return_scatter.png")


# ══════════════════════════════════════════════════════════════
# CHART 11 — Top 10 Funds by AUM Bar
# ══════════════════════════════════════════════════════════════
print("Chart 11: Top 10 AUM...")
top10_aum = perf.nlargest(10, "aum_crore")[["scheme_name","aum_crore","fund_house"]]
top10_aum["short_name"] = top10_aum["scheme_name"].str.replace(" - Regular Plan - Growth","").str.replace(" - Direct Plan - Growth","").str[:30]

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(top10_aum["short_name"][::-1],
               top10_aum["aum_crore"][::-1] / 1000,
               color=PALETTE[:10][::-1], alpha=0.88)
for bar, val in zip(bars, top10_aum["aum_crore"][::-1] / 1000):
    ax.text(val + 100, bar.get_y() + bar.get_height()/2,
            f"₹{val:,.0f}K Cr", va="center", fontsize=8)
ax.set_title("Top 10 Mutual Funds by AUM (₹ '000 Crore)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("AUM (₹ '000 Crore)")
ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "11_top10_aum.png")


# ══════════════════════════════════════════════════════════════
# CHART 12 — Expense Ratio Distribution
# ══════════════════════════════════════════════════════════════
print("Chart 12: Expense Ratio...")
fig, ax = plt.subplots(figsize=(10, 5))
direct  = perf[perf["plan"]=="Direct"]["expense_ratio_pct"]
regular = perf[perf["plan"]=="Regular"]["expense_ratio_pct"]
ax.hist(regular, bins=12, alpha=0.7, color="#f76c6c", label="Regular")
ax.hist(direct,  bins=12, alpha=0.7, color="#7c6af7", label="Direct")
ax.axvline(direct.mean(),  color="#a87cf7", linestyle="--", linewidth=1.5,
           label=f"Direct avg: {direct.mean():.2f}%")
ax.axvline(regular.mean(), color="#f7a0a0", linestyle="--", linewidth=1.5,
           label=f"Regular avg: {regular.mean():.2f}%")
ax.set_title("Expense Ratio Distribution — Direct vs Regular Plans",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Expense Ratio (%)"); ax.set_ylabel("Number of Schemes")
ax.legend(fontsize=9)
ax.grid(True, axis="y")
fig.tight_layout()
save(fig, "12_expense_ratio.png")


# ══════════════════════════════════════════════════════════════
# CHART 13 — Benchmark Index Comparison
# ══════════════════════════════════════════════════════════════
print("Chart 13: Benchmark Indices...")
fig, ax = plt.subplots(figsize=(13, 5))
indices = bench["index_name"].unique()
colors13 = ["#7c6af7","#3ec9d6","#f7c948","#f76c6c","#4ecb71","#f7934c","#a87cf7"]
for i, idx in enumerate(indices):
    df_ = bench[bench["index_name"]==idx].sort_values("date")
    base = df_["close_value"].iloc[0]
    c = colors13[i % len(colors13)]
    ax.plot(df_["date"], df_["close_value"]/base*100,
            color=c, linewidth=1.8, label=idx, alpha=0.9)

ax.axhline(100, color="#aaaaaa", linestyle="--", linewidth=0.8, alpha=0.5)
ax.set_title("Benchmark Index Performance — Normalised to 100 (Jan 2022)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Date"); ax.set_ylabel("Indexed Value (Base=100)")
ax.legend(fontsize=9, framealpha=0.2)
ax.grid(True)
fig.tight_layout()
save(fig, "13_benchmark_comparison.png")


# ══════════════════════════════════════════════════════════════
# CHART 14 — Monthly Transaction Volume Trend
# ══════════════════════════════════════════════════════════════
print("Chart 14: Transaction Volume...")
trans["ym"] = trans["transaction_date"].dt.to_period("M")
vol = trans.groupby(["ym","transaction_type"])["amount_inr"].sum().reset_index()
vol["ym_dt"] = vol["ym"].dt.to_timestamp()
vol["amount_cr"] = vol["amount_inr"] / 1e7

fig, ax = plt.subplots(figsize=(13, 5))
for i, tt in enumerate(["SIP","Lumpsum","Redemption"]):
    sub = vol[vol["transaction_type"]==tt].sort_values("ym_dt")
    ax.plot(sub["ym_dt"], sub["amount_cr"], color=PALETTE[i],
            linewidth=2, marker="o", markersize=3, label=tt)

ax.set_title("Monthly Transaction Volume by Type (₹ Crore)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Month"); ax.set_ylabel("Amount (₹ Crore)")
ax.legend(fontsize=9)
ax.grid(True)
fig.tight_layout()
save(fig, "14_transaction_volume.png")


# ══════════════════════════════════════════════════════════════
# CHART 15 — Sharpe Ratio Ranking
# ══════════════════════════════════════════════════════════════
print("Chart 15: Sharpe Ranking...")
top_sharpe = perf.nlargest(15, "sharpe_ratio").copy()
top_sharpe["short_name"] = (top_sharpe["scheme_name"]
    .str.replace(" - Direct Plan - Growth","")
    .str.replace(" - Regular Plan - Growth","")
    .str[:28])

fig, ax = plt.subplots(figsize=(12, 7))
colors = ["#f7c948" if p=="Direct" else "#7c6af7"
          for p in top_sharpe["plan"]]
bars = ax.barh(top_sharpe["short_name"][::-1],
               top_sharpe["sharpe_ratio"][::-1],
               color=colors[::-1], alpha=0.88)
for bar, val in zip(bars, top_sharpe["sharpe_ratio"][::-1]):
    ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
            f"{val:.2f}", va="center", fontsize=8)

legend_patches = [
    mpatches.Patch(color="#f7c948", label="Direct"),
    mpatches.Patch(color="#7c6af7", label="Regular"),
]
ax.legend(handles=legend_patches, fontsize=9)
ax.set_title("Top 15 Funds by Sharpe Ratio (Risk-Adjusted Return)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Sharpe Ratio"); ax.grid(True, axis="x")
fig.tight_layout()
save(fig, "15_sharpe_ranking.png")

print("\n✅ All 15 charts generated in reports/charts/")
