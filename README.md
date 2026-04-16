# 🚀 Digital Lending Growth & Portfolio Quality
### *Production-Grade SQL Cohort Analytics — Pallav Technologies*

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite%2FPostgreSQL--Compatible-orange?logo=sqlite)](https://sqlite.org)
[![Dataset](https://img.shields.io/badge/Dataset-LendingClub-blue)](https://www.lendingclub.com)

---

## 🎯 Business Problem
Growth isn't just about book size; it's about the quality of the book being built. This project performs **Cohort Analytics** on the **LendingClub** dataset to track how disbursement volume, interest yield, and portfolio quality (loan grades) evolve over time.

---

## 📊 SQL Analytics Engine (`growth_sql.py`)

The analytics engine focuses on time-series cohort health and volume scalability.

### Key Analysis:
- **Monthly Volume Growth**: Tracking month-on-month (MoM) disbursement growth.
- **Yield Trend Monitoring**: Analyzing how the weighted average interest rate (Yield) changes as the business scales.
- **Quality Mix Heatmap**: Using `SUM() OVER(PARTITION BY issue_month)` to monitor how the distribution of loan grades (A-G) shifts over time.
- **Cohort Profitability**: Tracking `Recovered Amount vs. Disbursed` at a cohort level.

---

## 📂 Data Sources
This project uses real-world loan issuance data from LendingClub.
- **Key Columns**: Issue Month, Loan Amount, Interest Rate, Grade.
- **Volume**: 10,000 credit records.

---

## 🔍 Visual Insights
Generated dashboards include:
1. **Monthly Disbursement Volume**: Line chart showing growth scalability.
2. **Yield Trend**: Bar chart tracking pricing discipline.
3. **Quality Mix Heatmap**: Identifying periods where loan quality may have drifted.
4. **Growth KPIs Header**: Summary of lifetime volume and portfolio yield.

---

*Built for Pallav Technologies Portfolio — Advanced Growth Pillar.*
