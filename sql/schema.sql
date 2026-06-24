-- ============================================================
-- schema.sql — Bluestock MF Analytics: SQLite Star Schema
-- Day 2 — Mutual Fund Analytics Project
-- Author: Tejaswini
-- ============================================================
-- Star Schema Design:
--   Dimensions : dim_fund, dim_date
--   Facts      : fact_nav, fact_transactions, fact_performance,
--                fact_aum, fact_sip_inflows, fact_holdings,
--                fact_benchmark
-- ============================================================

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- DIMENSION TABLES
-- ─────────────────────────────────────────────

-- dim_fund: One row per mutual fund scheme
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER     PRIMARY KEY,
    fund_house          TEXT        NOT NULL,
    scheme_name         TEXT        NOT NULL,
    category            TEXT        NOT NULL,        -- Equity / Debt
    sub_category        TEXT        NOT NULL,        -- Large Cap / Mid Cap etc.
    plan                TEXT        NOT NULL,        -- Direct / Regular
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL,                        -- TER (0.1 – 2.5%)
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,                        -- Low/Moderate/High/Very High
    sebi_category_code  TEXT
);

-- dim_date: Calendar dimension for time-based analysis
CREATE TABLE IF NOT EXISTS dim_date (
    date_id     TEXT    PRIMARY KEY,                 -- YYYY-MM-DD
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    day         INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,                    -- 0=Mon, 6=Sun
    is_weekend  INTEGER NOT NULL DEFAULT 0,          -- 0/1 boolean
    month_name  TEXT    NOT NULL,
    quarter_name TEXT   NOT NULL
);

-- ─────────────────────────────────────────────
-- FACT TABLES
-- ─────────────────────────────────────────────

-- fact_nav: Daily NAV for each scheme
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL,
    date        TEXT    NOT NULL,
    nav         REAL    NOT NULL CHECK (nav > 0),
    year        INTEGER,
    month       INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date)      REFERENCES dim_date(date_id),
    UNIQUE (amfi_code, date)
);

-- fact_transactions: Investor buy/sell/SIP transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT    NOT NULL,
    transaction_date    TEXT    NOT NULL,
    amfi_code           INTEGER NOT NULL,
    transaction_type    TEXT    NOT NULL CHECK (transaction_type IN ('SIP','Lumpsum','Redemption')),
    amount_inr          INTEGER NOT NULL CHECK (amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT    CHECK (kyc_status IN ('Verified','Pending','Rejected')),
    transaction_year    INTEGER,
    transaction_month   INTEGER,
    FOREIGN KEY (amfi_code)        REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date_id)
);

-- fact_performance: Scheme-level performance metrics
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL,
    scheme_name         TEXT,
    fund_house          TEXT,
    category            TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    morningstar_rating  INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- fact_aum: AUM by fund house (semi-annual)
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL,
    fund_house      TEXT    NOT NULL,
    aum_lakh_crore  REAL,
    aum_crore       INTEGER,
    num_schemes     INTEGER,
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- fact_sip_inflows: Monthly industry-level SIP data
CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    sip_id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    month                       TEXT    NOT NULL,
    sip_inflow_crore            INTEGER,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

-- fact_holdings: Portfolio stock holdings per scheme
CREATE TABLE IF NOT EXISTS fact_holdings (
    holding_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL,
    stock_symbol        TEXT    NOT NULL,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL    CHECK (weight_pct BETWEEN 0 AND 100),
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- fact_benchmark: Daily index closing values
CREATE TABLE IF NOT EXISTS fact_benchmark (
    benchmark_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL,
    index_name      TEXT    NOT NULL,
    close_value     REAL    NOT NULL,
    FOREIGN KEY (date) REFERENCES dim_date(date_id),
    UNIQUE (date, index_name)
);

-- ─────────────────────────────────────────────
-- INDEXES for query performance
-- ─────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_nav_amfi_date    ON fact_nav(amfi_code, date);
CREATE INDEX IF NOT EXISTS idx_nav_date         ON fact_nav(date);
CREATE INDEX IF NOT EXISTS idx_trans_date       ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_trans_amfi       ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_trans_type       ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_trans_state      ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_perf_amfi        ON fact_performance(amfi_code);
CREATE INDEX IF NOT EXISTS idx_holdings_amfi    ON fact_holdings(amfi_code);
CREATE INDEX IF NOT EXISTS idx_benchmark_date   ON fact_benchmark(date);
