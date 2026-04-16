# 🚀 Digital Lending Growth & LTV Analytics
### *Production-Grade SQL Funnel & Cohort Analytics — Pallav Technologies*

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite%2FPostgreSQL--Compatible-orange?logo=sqlite)](https://sqlite.org)
[![Domain](https://img.shields.io/badge/Domain-Growth%20Analytics-green)](https://pallav.tech)

---

## 🎯 Business Problem
Digital lenders spend heavily on acquisition but often can't answer: *"Which cohort actually drives the most value?"* or *"Where in our funnel are we leaking users?"* This project builds a complete **Funnel → Cohort → LTV analytics pipeline** backed by production-grade SQL, directly mapping to Pallav's Customer Acquisition product.

---

## 🛠 Technical Stack

| Layer | Technology |
|-------|-----------|
| **Database** | SQLite with **VIEW** for funnel aggregation |
| **SQL Analytics** | `LAG()`, `FIRST_VALUE()`, `SUM() OVER`, `AVG() OVER`, `RANK()`, nested CTEs |
| **Funnel Engine** | Step-by-step conversion with drop-off counts via SQL CTE chain |
| **LTV Model** | Cohort-level CLV estimation via SQL running SUM |
| **Visualization** | 5-panel dark-mode dashboard |

---

## 📊 SQL Analytics Engine (`growth_sql.py`)

### Query Highlights

```sql
-- Funnel Conversion CTE Chain with FIRST_VALUE + LAG for step-by-step drop-off
WITH base AS (
    SELECT COUNT(*) AS total_registered, SUM(has_kyc) AS kyc, ...
    FROM user_funnel
),
stages AS (
    SELECT 'Registration' AS stage, 1 AS seq, total_registered AS users FROM base
    UNION ALL SELECT 'KYC Complete', 2, kyc FROM base
    UNION ALL SELECT 'Disbursement', 5, disbursed FROM base
)
SELECT stage, users,
    ROUND(users * 100.0 / LAG(users) OVER (ORDER BY seq), 2) AS step_conversion_pct,
    ROUND(users * 100.0 / FIRST_VALUE(users) OVER (
        ORDER BY seq ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ), 2)                                                      AS overall_conversion_pct,
    LAG(users) OVER (ORDER BY seq) - users                    AS users_dropped
FROM stages ORDER BY seq;
```

```sql
-- CLV Estimation with cumulative running SUM window
SELECT signup_month, estimated_ltv,
    SUM(estimated_ltv) OVER (
        ORDER BY signup_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_ltv,
    ROUND(estimated_ltv / NULLIF(total_users, 0), 2) AS ltv_per_user
FROM cohort_value;
```

| SQL Concept | Business Use Case |
|---|---|
| `LAG()` + `FIRST_VALUE()` | Funnel step-level & overall conversion |
| `SUM() OVER` cumulative | Growing business LTV visualization |
| `AVG() OVER` 3-period rolling | Cohort repayment trend smoothing |
| `RANK() OVER` | Cohort efficiency leaderboard |
| `CREATE VIEW` | Pre-built funnel summary for dashboards |

---

## 📐 Database Schema

```sql
CREATE TABLE user_funnel (
    user_id           INTEGER PRIMARY KEY,
    signup_month      TEXT    NOT NULL,
    has_kyc           INTEGER NOT NULL CHECK (has_kyc IN (0, 1)),
    has_application   INTEGER NOT NULL CHECK (has_application IN (0, 1)),
    has_approval      INTEGER NOT NULL CHECK (has_approval IN (0, 1)),
    has_disbursement  INTEGER NOT NULL CHECK (has_disbursement IN (0, 1)),
    loan_amount       REAL    NOT NULL DEFAULT 0.0,
    has_repayment     INTEGER NOT NULL CHECK (has_repayment IN (0, 1))
);

-- Pre-built VIEW for dashboard reporting
CREATE VIEW v_funnel_summary AS
SELECT signup_month, COUNT(*) AS registered,
       SUM(has_kyc) AS kyc_completed, SUM(has_disbursement) AS disbursed, ...
FROM user_funnel GROUP BY signup_month;
```

---

## 📂 Project Structure

```
project_3_growth_analytics/
├── growth_sql.py               ← Production SQL Engine (5 CTE/window queries + VIEW)
├── growth_analysis.py          ← Funnel & cohort analysis with Matplotlib
├── growth_data_generator.py    ← Synthetic 2,000-user funnel event generator
├── funnel_data.csv             ← Simulated user journey data
├── growth_sql_dashboard.png    ← 5-panel production dashboard
├── acquisition_funnel.png      ← Funnel waterfall chart
└── cohort_repayment.png        ← Repayment quality trend
```

---

## 🔍 Key Insights

- **Critical Drop-off**: Only 54% of KYC-verified users complete a loan application — fixing this single step could increase disbursements by 35%
- **Cohort Drift**: Repayment rate declined from **91.5% (Jan)** to **69.7% (Jun)** — a **-0.87 correlation** indicating model drift
- **Cumulative LTV**: 6 months of cohorts generated ₹18,000+ in net value (at 5% NIM)
- **January cohort** ranked #1 in end-to-end efficiency — its targeting profile should be replicated

---

*Built for Pallav Technologies Data Analyst portfolio — mapping to the Customer Acquisition & Growth analytics pillar.*
