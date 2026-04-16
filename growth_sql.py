"""
=============================================================================
PROJECT 3: Digital Lending Growth & Portfolio Quality (Real-World Case)
SQL Analytics Engine — Production-Grade Edition
=============================================================================
Dataset: LendingClub (Real P2P Loan Performance Data)
Demonstrates:
  - Monthly Cohort growth in loan volume
  - Portfolio Quality Mix (Grade distribution over time)
  - Interest Margin trends vs Portfolio Aging
=============================================================================
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

BASE = Path(".")
DATA_DIR = Path(".")
DB   = BASE / "growth_analytics.db"

# ---------------------------------------------------------------------------
# 1. SCHEMA DESIGN (Growth & Quality Schema)
# ---------------------------------------------------------------------------
DDL = """
DROP TABLE IF EXISTS portfolio_growth;

CREATE TABLE portfolio_growth (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_amount          REAL NOT NULL,
    grade                TEXT,
    interest_rate        REAL,
    issue_month          TEXT,
    loan_status          TEXT,
    paid_total           REAL,
    ingested_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_issue_month ON portfolio_growth(issue_month);
CREATE INDEX idx_grade        ON portfolio_growth(grade);
"""

# ---------------------------------------------------------------------------
# 2. ANALYTICAL SQL QUERIES (Production-Grade Growth Analytics)
# ---------------------------------------------------------------------------

QUERIES = {

    # Query 1: Monthly Cohort Volume Growth
    "monthly_volume_growth": """
        SELECT
            issue_month,
            COUNT(*)                        AS loan_count,
            ROUND(SUM(loan_amount), 0)      AS total_disbursed,
            ROUND(AVG(loan_amount), 0)      AS avg_ticket_size,
            ROUND(AVG(interest_rate), 2)    AS avg_int_rate
        FROM portfolio_growth
        GROUP BY issue_month
        ORDER BY issue_month;
    """,

    # Query 2: Portfolio Quality Mix by Cohort
    "quality_mix_by_month": """
        WITH grade_counts AS (
            SELECT
                issue_month,
                grade,
                COUNT(*) AS count
            FROM portfolio_growth
            GROUP BY issue_month, grade
        )
        SELECT
            issue_month,
            grade,
            count,
            ROUND(count * 100.0 / SUM(count) OVER (PARTITION BY issue_month), 2) AS mix_pct
        FROM grade_counts
        ORDER BY issue_month, grade;
    """,

    # Query 3: Cohort Profitability & Loss (LTV Proxy)
    "cohort_profitability": """
        SELECT
            issue_month,
            ROUND(SUM(loan_amount), 0) AS disbursed,
            ROUND(SUM(paid_total), 0)  AS recovered,
            ROUND((SUM(paid_total) - SUM(loan_amount)), 0) AS net_recovery_margin,
            ROUND(AVG(paid_total / loan_amount) * 100, 2) AS recovery_perf_pct
        FROM portfolio_growth
        GROUP BY issue_month
        ORDER BY issue_month;
    """,

    # Query 4: Growth KPIs (Dashboard Header)
    "growth_kpis": """
        SELECT
            COUNT(*)                                      AS total_loans,
            ROUND(SUM(loan_amount), 0)                    AS lifetime_disbursed,
            ROUND(AVG(interest_rate), 2)                  AS portfolio_yield_pct,
            COUNT(DISTINCT issue_month)                   AS cohorts_tracked
        FROM portfolio_growth;
    """
}

# ---------------------------------------------------------------------------
# 3. EXECUTION ENGINE
# ---------------------------------------------------------------------------

def load_data():
    csv_path = DATA_DIR / "lending_club_openintro.csv"
    if not csv_path.exists():
        print(f"❌ Data file not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    # Column Selection
    cols = {
        'loan_amount': 'loan_amount', 'grade': 'grade', 'interest_rate': 'interest_rate',
        'issue_month': 'issue_month', 'loan_status': 'loan_status', 'paid_total': 'paid_total'
    }
    df_clean = df[list(cols.keys())].rename(columns=cols)

    con = sqlite3.connect(DB)
    con.executescript(DDL)
    df_clean.to_sql("portfolio_growth", con, if_exists="append", index=False)
    con.commit()
    print(f"✅ Growth & Quality data loaded: {len(df_clean)} records.")
    return con

def run_analytics(con):
    results = {}
    for name, sql in QUERIES.items():
        try:
            df = pd.read_sql_query(sql, con)
            results[name] = df
            print(f"\n📊 {name.upper().replace('_', ' ')}")
            print(df.head(10).to_string(index=False))
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
    return results

def plot_visuals(results):
    sns.set_theme(style="whitegrid", palette="muted")
    fig = plt.figure(figsize=(20, 12), facecolor="#ffffff")
    fig.suptitle("Pallav Technologies — Lending Growth & Portfolio Quality Dashboard",
                 fontsize=22, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.25)

    # Plot 1: Monthly Volume Growth
    ax1 = fig.add_subplot(gs[0, 0])
    d1 = results["monthly_volume_growth"]
    sns.lineplot(x="issue_month", y="total_disbursed", data=d1, ax=ax1, marker="o", color="#0d6efd", linewidth=3)
    ax1.set_title("Monthly Disbursement Volume Growth (₹)", fontsize=15)
    ax1.set_ylabel("Total Disbursed (₹)")
    plt.setp(ax1.get_xticklabels(), rotation=45)

    # Plot 2: Yield Trend
    ax2 = fig.add_subplot(gs[0, 1])
    sns.barplot(x="issue_month", y="avg_int_rate", data=d1, ax=ax2, palette="Greens")
    ax2.set_title("Average Portfolio Yield Trend (% Interest Rate)", fontsize=15)
    ax2.set_ylabel("Avg Int Rate (%)")
    plt.setp(ax2.get_xticklabels(), rotation=45)

    # Plot 3: Quality Mix Heatmap
    ax3 = fig.add_subplot(gs[1, 0])
    d2_pivot = results["quality_mix_by_month"].pivot(index="grade", columns="issue_month", values="mix_pct").fillna(0)
    sns.heatmap(d2_pivot, annot=True, cmap="YlGnBu", ax=ax3, fmt=".1f")
    ax3.set_title("Cohort Quality Mix (%) - Loan Grades over Time", fontsize=15)

    # Plot 4: KPI Text Box
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis("off")
    kpi = results["growth_kpis"].iloc[0]
    summary_text = (
        f"  Total Loans Disbursed    : {int(kpi['total_loans']):,}\n\n"
        f"  Cumulative Volume        : ₹{int(kpi['lifetime_disbursed']):,}\n"
        f"  Portfolio Average Yield  : {kpi['portfolio_yield_pct']}%\n"
        f"  Active Cohorts Tracked   : {int(kpi['cohorts_tracked'])}\n"
    )
    ax4.text(0.1, 0.45, summary_text, fontsize=18, family="monospace",
             bbox=dict(boxstyle="round", facecolor="#f8f9fa", alpha=0.9, edgecolor="#198754"))
    ax4.set_title("Business Growth KPIs", fontsize=18, fontweight="bold")

    out_path = BASE / "growth_sql_dashboard.png"
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    print(f"✅ Growth Dashboard generated: {out_path}")

if __name__ == "__main__":
    connection = load_data()
    if connection:
        analytical_results = run_analytics(connection)
        plot_visuals(analytical_results)
        connection.close()
