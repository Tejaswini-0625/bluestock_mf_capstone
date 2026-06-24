-- ============================================================
-- queries.sql — 10 Analytical SQL Queries
-- Day 2 — Bluestock MF Analytics Project
-- Database: bluestock_mf.db (SQLite)
-- Author: Tejaswini
-- ============================================================


-- ─────────────────────────────────────────────
-- Q1. Top 5 Funds by AUM (latest snapshot)
-- Business use: Identify market leaders by assets under management
-- ─────────────────────────────────────────────
SELECT
    scheme_name,
    fund_house,
    category,
    plan,
    aum_crore,
    RANK() OVER (ORDER BY aum_crore DESC) AS aum_rank
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- ─────────────────────────────────────────────
-- Q2. Average NAV Per Month (across all schemes)
-- Business use: Spot market-wide NAV trends over time
-- ─────────────────────────────────────────────
SELECT
    year,
    month,
    ROUND(AVG(nav), 2)   AS avg_nav,
    ROUND(MIN(nav), 2)   AS min_nav,
    ROUND(MAX(nav), 2)   AS max_nav,
    COUNT(DISTINCT amfi_code) AS schemes_count
FROM fact_nav
GROUP BY year, month
ORDER BY year, month;


-- ─────────────────────────────────────────────
-- Q3. SIP Year-on-Year Growth
-- Business use: Measure retail participation growth in MFs
-- ─────────────────────────────────────────────
SELECT
    month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    yoy_growth_pct,
    ROUND(
        (sip_inflow_crore - LAG(sip_inflow_crore, 12) OVER (ORDER BY month))
        * 100.0 / LAG(sip_inflow_crore, 12) OVER (ORDER BY month),
    2) AS calculated_yoy_growth_pct
FROM fact_sip_inflows
ORDER BY month;


-- ─────────────────────────────────────────────
-- Q4. Total Transactions by State
-- Business use: Geographic distribution of investor activity
-- ─────────────────────────────────────────────
SELECT
    state,
    COUNT(*)                    AS total_transactions,
    SUM(amount_inr)             AS total_amount_inr,
    ROUND(AVG(amount_inr), 0)   AS avg_transaction_amt,
    COUNT(DISTINCT investor_id) AS unique_investors
FROM fact_transactions
GROUP BY state
ORDER BY total_transactions DESC;


-- ─────────────────────────────────────────────
-- Q5. Funds with Expense Ratio < 1%
-- Business use: Identify cost-efficient schemes for investors
-- ─────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.sub_category,
    f.plan,
    f.expense_ratio_pct,
    p.return_3yr_pct,
    p.sharpe_ratio,
    p.aum_crore
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;


-- ─────────────────────────────────────────────
-- Q6. Top Performing Funds — 3-Year Returns vs Benchmark
-- Business use: Find alpha-generating funds (outperforming benchmark)
-- ─────────────────────────────────────────────
SELECT
    scheme_name,
    fund_house,
    category,
    plan,
    return_3yr_pct,
    benchmark_3yr_pct,
    ROUND(return_3yr_pct - benchmark_3yr_pct, 2) AS excess_return_pct,
    alpha,
    sharpe_ratio
FROM fact_performance
WHERE return_3yr_pct > benchmark_3yr_pct
ORDER BY excess_return_pct DESC
LIMIT 10;


-- ─────────────────────────────────────────────
-- Q7. SIP vs Lumpsum vs Redemption — Monthly Trend
-- Business use: Understand investor behaviour over time
-- ─────────────────────────────────────────────
SELECT
    transaction_year,
    transaction_month,
    transaction_type,
    COUNT(*)            AS num_transactions,
    SUM(amount_inr)     AS total_amount_inr,
    ROUND(AVG(amount_inr), 0) AS avg_amount
FROM fact_transactions
GROUP BY transaction_year, transaction_month, transaction_type
ORDER BY transaction_year, transaction_month, transaction_type;


-- ─────────────────────────────────────────────
-- Q8. Sector-wise Portfolio Concentration
-- Business use: Identify sector concentration risk across funds
-- ─────────────────────────────────────────────
SELECT
    h.sector,
    COUNT(DISTINCT h.amfi_code)     AS num_funds_holding,
    COUNT(DISTINCT h.stock_symbol)  AS num_stocks,
    ROUND(AVG(h.weight_pct), 2)     AS avg_weight_pct,
    ROUND(SUM(h.market_value_cr), 2) AS total_market_value_cr
FROM fact_holdings h
GROUP BY h.sector
ORDER BY total_market_value_cr DESC;


-- ─────────────────────────────────────────────
-- Q9. Risk-Adjusted Return Ranking (Sharpe Ratio)
-- Business use: Rank funds by risk-adjusted performance
-- ─────────────────────────────────────────────
SELECT
    scheme_name,
    fund_house,
    sub_category,
    plan,
    return_3yr_pct,
    std_dev_ann_pct,
    sharpe_ratio,
    sortino_ratio,
    max_drawdown_pct,
    morningstar_rating,
    RANK() OVER (PARTITION BY category ORDER BY sharpe_ratio DESC) AS sharpe_rank
FROM fact_performance
JOIN dim_fund USING (amfi_code)
ORDER BY sharpe_ratio DESC;


-- ─────────────────────────────────────────────
-- Q10. AUM Growth by Fund House (YoY)
-- Business use: Track which AMCs are gaining/losing market share
-- ─────────────────────────────────────────────
SELECT
    a.fund_house,
    a.date,
    a.aum_crore,
    LAG(a.aum_crore) OVER (
        PARTITION BY a.fund_house ORDER BY a.date
    ) AS prev_period_aum,
    ROUND(
        (a.aum_crore - LAG(a.aum_crore) OVER (
            PARTITION BY a.fund_house ORDER BY a.date)
        ) * 100.0 / LAG(a.aum_crore) OVER (
            PARTITION BY a.fund_house ORDER BY a.date),
    2) AS aum_growth_pct
FROM fact_aum a
ORDER BY a.fund_house, a.date;
