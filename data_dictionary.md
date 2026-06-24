# Data Dictionary — Bluestock MF Analytics Project

**Project:** Capstone Project I — Mutual Fund Analytics  
**Author:** Tejaswini  
**Last Updated:** June 2026  
**Database:** `bluestock_mf.db` (SQLite)

---

## Table of Contents
1. [01_fund_master](#1-fund_master)
2. [02_nav_history](#2-nav_history)
3. [03_aum_by_fund_house](#3-aum_by_fund_house)
4. [04_monthly_sip_inflows](#4-monthly_sip_inflows)
5. [05_category_inflows](#5-category_inflows)
6. [06_industry_folio_count](#6-industry_folio_count)
7. [07_scheme_performance](#7-scheme_performance)
8. [08_investor_transactions](#8-investor_transactions)
9. [09_portfolio_holdings](#9-portfolio_holdings)
10. [10_benchmark_indices](#10-benchmark_indices)

---

## 1. fund_master
**Source:** AMFI India / Bluestock Fintech  
**Rows:** 40 | **Columns:** 15  
**Description:** Master reference table for all mutual fund schemes. One row per scheme.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `amfi_code` | INTEGER (PK) | Unique AMFI scheme code assigned by AMFI India | 119551 |
| `fund_house` | TEXT | Name of the Asset Management Company (AMC) | SBI Mutual Fund |
| `scheme_name` | TEXT | Full name of the mutual fund scheme | SBI Bluechip Fund - Regular Plan - Growth |
| `category` | TEXT | Broad category — Equity or Debt | Equity |
| `sub_category` | TEXT | SEBI-defined sub-category | Large Cap, Mid Cap, Small Cap, Gilt, Liquid |
| `plan` | TEXT | Plan type — Direct (no commission) or Regular | Direct |
| `launch_date` | DATE | Date the scheme was launched | 2006-02-14 |
| `benchmark` | TEXT | Index used as performance benchmark | NIFTY 100 TRI |
| `expense_ratio_pct` | REAL | Total Expense Ratio charged annually (%) | 1.54 |
| `exit_load_pct` | REAL | Exit load charged on early redemption (%) | 1.0 |
| `min_sip_amount` | INTEGER | Minimum SIP investment amount (INR) | 500 |
| `min_lumpsum_amount` | INTEGER | Minimum one-time investment amount (INR) | 1000 |
| `fund_manager` | TEXT | Name of the fund manager | Sohini Andani |
| `risk_category` | TEXT | SEBI risk classification | Moderate, High, Very High, Low |
| `sebi_category_code` | TEXT | SEBI internal category code | EC01 |

**Notes:**
- `amfi_code` is the primary key used to join all other tables
- Direct plans have lower `expense_ratio_pct` than Regular plans
- `expense_ratio_pct` valid range: 0.1% – 2.5%

---

## 2. nav_history
**Source:** mfapi.in API  
**Rows:** 46,000 (raw) | **Columns:** 3  
**Description:** Daily Net Asset Value (NAV) for each scheme from Jan 2022 to May 2026.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `amfi_code` | INTEGER (FK) | AMFI scheme code — joins to fund_master | 119551 |
| `date` | DATE | NAV date (business days only; weekends forward-filled) | 2022-01-03 |
| `nav` | REAL | Net Asset Value per unit in INR | 54.3856 |
| `year` | INTEGER | Derived: year extracted from date | 2022 |
| `month` | INTEGER | Derived: month extracted from date | 1 |

**Notes:**
- NAV is published only on business days; weekends/holidays forward-filled in cleaned version
- NAV must always be > 0 (validated during cleaning)
- Date range: 2022-01-03 to 2026-05-29

---

## 3. aum_by_fund_house
**Source:** AMFI Monthly Data  
**Rows:** 90 | **Columns:** 5  
**Description:** AUM (Assets Under Management) aggregated by fund house, semi-annually.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `date` | DATE | Reporting date (semi-annual: Mar 31, Sep 30) | 2022-03-31 |
| `fund_house` | TEXT | Name of the AMC | SBI Mutual Fund |
| `aum_lakh_crore` | REAL | AUM in lakh crore INR | 6.05 |
| `aum_crore` | INTEGER | AUM in crore INR | 605000 |
| `num_schemes` | INTEGER | Number of active schemes managed | 186 |

---

## 4. monthly_sip_inflows
**Source:** AMFI Monthly SIP Data  
**Rows:** 48 | **Columns:** 6  
**Description:** Industry-level monthly SIP (Systematic Investment Plan) statistics.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `month` | TEXT | Year-Month in YYYY-MM format | 2022-01 |
| `sip_inflow_crore` | INTEGER | Total SIP inflows in crore INR | 11517 |
| `active_sip_accounts_crore` | REAL | Active SIP accounts in crore units | 4.91 |
| `new_sip_accounts_lakh` | REAL | New SIP accounts opened (lakh) | 9.1 |
| `sip_aum_lakh_crore` | REAL | Total SIP AUM in lakh crore | 4.80 |
| `yoy_growth_pct` | REAL | Year-on-year growth (%) — null for first 12 months | 18.5 |

**Notes:**
- `yoy_growth_pct` is null for Jan 2022 – Dec 2022 (no prior year data)

---

## 5. category_inflows
**Source:** AMFI Category-wise Data  
**Rows:** 144 | **Columns:** 3  
**Description:** Monthly net inflows by fund category.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `month` | TEXT | Year-Month in YYYY-MM format | 2024-04 |
| `category` | TEXT | Fund category | Large Cap, Mid Cap, Small Cap |
| `net_inflow_crore` | REAL | Net inflow into category in crore INR | 2413.0 |

---

## 6. industry_folio_count
**Source:** AMFI Quarterly Data  
**Rows:** 21 | **Columns:** 6  
**Description:** Quarterly folio (investor account) counts across fund types.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `month` | TEXT | Quarter start month (YYYY-MM) | 2022-01 |
| `total_folios_crore` | REAL | Total folios in crore | 13.26 |
| `equity_folios_crore` | REAL | Equity fund folios in crore | 9.28 |
| `debt_folios_crore` | REAL | Debt fund folios in crore | 1.86 |
| `hybrid_folios_crore` | REAL | Hybrid fund folios in crore | 0.80 |
| `others_folios_crore` | REAL | Other category folios in crore | 1.33 |

---

## 7. scheme_performance
**Source:** Bluestock Fintech / Value Research  
**Rows:** 40 | **Columns:** 19  
**Description:** Performance metrics and risk ratios for each scheme.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `amfi_code` | INTEGER (FK) | AMFI scheme code | 119551 |
| `scheme_name` | TEXT | Full scheme name | SBI Bluechip Fund - Regular Plan |
| `fund_house` | TEXT | AMC name | SBI Mutual Fund |
| `category` | TEXT | Fund category | Large Cap |
| `plan` | TEXT | Direct or Regular | Regular |
| `return_1yr_pct` | REAL | 1-year trailing return (%) | 12.42 |
| `return_3yr_pct` | REAL | 3-year CAGR return (%) | 12.36 |
| `return_5yr_pct` | REAL | 5-year CAGR return (%) | 14.45 |
| `benchmark_3yr_pct` | REAL | Benchmark 3-year CAGR (%) | 11.49 |
| `alpha` | REAL | Excess return over benchmark (Jensen's Alpha) | 0.87 |
| `beta` | REAL | Market sensitivity (1 = same as market) | 0.89 |
| `sharpe_ratio` | REAL | Risk-adjusted return (higher = better) | 0.88 |
| `sortino_ratio` | REAL | Downside risk-adjusted return | 1.29 |
| `std_dev_ann_pct` | REAL | Annualised standard deviation of returns (%) | 14.0 |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough loss (%) — negative | -21.70 |
| `aum_crore` | INTEGER | Assets Under Management in crore INR | 14288 |
| `expense_ratio_pct` | REAL | Annual expense ratio (%) — valid: 0.1–2.5 | 1.54 |
| `morningstar_rating` | INTEGER | Star rating 1–5 | 4 |
| `risk_grade` | TEXT | Risk classification | Moderate |

**Validation Rules:**
- `expense_ratio_pct` must be between 0.1% and 2.5%
- `morningstar_rating` must be between 1 and 5
- `beta` typically between 0 and 2
- Returns flagged if > 100% or < -50%

---

## 8. investor_transactions
**Source:** Bluestock Fintech (Simulated)  
**Rows:** 32,778 | **Columns:** 13  
**Description:** Individual investor transaction records (SIP, Lumpsum, Redemption).

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `investor_id` | TEXT | Unique investor identifier | INV003054 |
| `transaction_date` | DATE | Date of transaction | 2024-01-01 |
| `amfi_code` | INTEGER (FK) | AMFI scheme code | 119092 |
| `transaction_type` | TEXT | Type of transaction | SIP, Lumpsum, Redemption |
| `amount_inr` | INTEGER | Transaction amount in INR | 1834 |
| `state` | TEXT | Investor's state | Telangana |
| `city` | TEXT | Investor's city | Hyderabad |
| `city_tier` | TEXT | City tier classification | T30, B30 |
| `age_group` | TEXT | Investor's age group | 18-25, 26-35, 36-45, 46-55, 56+ |
| `gender` | TEXT | Investor gender | Male, Female |
| `annual_income_lakh` | REAL | Annual income in lakh INR | 77.1 |
| `payment_mode` | TEXT | Mode of payment | UPI, Mandate, Cheque, NEFT |
| `kyc_status` | TEXT | KYC verification status | Verified, Pending, Rejected |

**Validation Rules:**
- `transaction_type` must be one of: SIP, Lumpsum, Redemption
- `amount_inr` must be > 0
- `kyc_status` must be one of: Verified, Pending, Rejected

---

## 9. portfolio_holdings
**Source:** Bluestock Fintech / AMFI Disclosure  
**Rows:** 322 | **Columns:** 8  
**Description:** Stock-level holdings for each mutual fund scheme.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `amfi_code` | INTEGER (FK) | AMFI scheme code | 119551 |
| `stock_symbol` | TEXT | NSE/BSE stock ticker symbol | POWERGRID |
| `stock_name` | TEXT | Full company name | Power Grid Corporation |
| `sector` | TEXT | Business sector | Banking, IT, Pharma, Utilities |
| `weight_pct` | REAL | Portfolio weight (% of total holdings) | 13.85 |
| `market_value_cr` | REAL | Market value of holding in crore INR | 737.09 |
| `current_price_inr` | REAL | Stock price at portfolio date (INR) | 6011.08 |
| `portfolio_date` | DATE | Date of portfolio disclosure | 2025-12-31 |

**Notes:**
- `weight_pct` values per scheme should sum to approximately 100%

---

## 10. benchmark_indices
**Source:** NSE India / BSE India  
**Rows:** 8,050 | **Columns:** 3  
**Description:** Daily closing values for major Indian market indices.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `date` | DATE | Trading date | 2022-01-03 |
| `index_name` | TEXT | Name of the index | NIFTY50, NIFTY100, NIFTY_MIDCAP150, BSE_SMALLCAP, NIFTY500 |
| `close_value` | REAL | Closing index value | 17492.79 |

---

## Relationships (Star Schema)

```
dim_fund (amfi_code PK)
    ├── fact_nav          (amfi_code FK)
    ├── fact_transactions (amfi_code FK)
    ├── fact_performance  (amfi_code FK)
    └── fact_holdings     (amfi_code FK)

dim_date (date_id PK)
    ├── fact_nav          (date FK)
    ├── fact_transactions (transaction_date FK)
    ├── fact_aum          (date FK)
    └── fact_benchmark    (date FK)
```

---

## Data Quality Summary

| Dataset | Rows | Nulls | Duplicates | Issues Found |
|---------|------|-------|------------|--------------|
| fund_master | 40 | 0 | 0 | None |
| nav_history | 46,000 | 0 | 0 | Forward-filled weekends/holidays |
| aum_by_fund_house | 90 | 0 | 0 | None |
| monthly_sip_inflows | 48 | 12 (yoy_growth) | 0 | First 12 months have no YoY |
| category_inflows | 144 | 0 | 0 | None |
| industry_folio_count | 21 | 0 | 0 | None |
| scheme_performance | 40 | 0 | 0 | None |
| investor_transactions | 32,778 | 0 | 0 | None |
| portfolio_holdings | 322 | 0 | 0 | None |
| benchmark_indices | 8,050 | 0 | 0 | None |
