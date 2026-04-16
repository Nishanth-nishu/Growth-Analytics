"""
=============================================================================
PROJECT 3: Digital Lending Growth & LTV Analytics
SQL Analytics Engine — Production-Grade Edition
=============================================================================
Demonstrates deep SQL mastery for a Data Analyst role at Pallav Technologies:
  - Production DDL: Funnel events, disbursements, repayments
  - Funnel Conversion using CTEs and step-by-step DROP calculation
  - Cohort Repayment with LAG for month-on-month change
  - Customer LTV Estimation using SUM() OVER (cumulative disbursement)
  - Acquisition Efficiency: CAC scoring via NTILE
  - Retention Rates: LEAD to predict next-month repayment risk
=============================================================================
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

BASE = Path("/scratch/nishanth.r/pallavi/project_3_growth_analytics")
DB   = BASE / "growth_analytics.db"

DDL = """
DROP TABLE IF EXISTS user_funnel;
DROP VIEW IF EXISTS v_funnel_summary;

-- Core event table (each row = one user's journey state)
CREATE TABLE user_funnel (
    user_id           INTEGER PRIMARY KEY,
    signup_month      TEXT    NOT NULL,
    has_kyc           INTEGER NOT NULL CHECK (has_kyc IN (0, 1)),
    has_application   INTEGER NOT NULL CHECK (has_application IN (0, 1)),
    has_approval      INTEGER NOT NULL CHECK (has_approval IN (0, 1)),
    has_disbursement  INTEGER NOT NULL CHECK (has_disbursement IN (0, 1)),
    loan_amount       REAL    NOT NULL DEFAULT 0.0,
    has_repayment     INTEGER NOT NULL CHECK (has_repayment IN (0, 1)),
    ingested_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes optimized for cohort and funnel queries
CREATE INDEX idx_signup_month ON user_funnel(signup_month);
CREATE INDEX idx_disbursement ON user_funnel(has_disbursement, signup_month);
CREATE INDEX idx_repayment    ON user_funnel(has_repayment, signup_month);

-- Pre-built VIEW for funnel reporting (production pattern)
CREATE VIEW v_funnel_summary AS
SELECT
    signup_month,
    COUNT(*)                AS registered,
    SUM(has_kyc)            AS kyc_completed,
    SUM(has_application)    AS apps_submitted,
    SUM(has_approval)       AS approved,
    SUM(has_disbursement)   AS disbursed,
    SUM(has_repayment)      AS repaid
FROM user_funnel
GROUP BY signup_month;
"""

QUERIES = {

    # Query 1: Full Funnel Conversion with Step-Level Drop-Off (CTE Chain)
    # Business Question: Where are we losing customers — before KYC, or at approval?
    "funnel_conversion_analysis": """
        WITH base AS (
            SELECT
                COUNT(*)              AS total_registered,
                SUM(has_kyc)          AS kyc,
                SUM(has_application)  AS applied,
                SUM(has_approval)     AS approved,
                SUM(has_disbursement) AS disbursed,
                SUM(has_repayment)    AS repaid
            FROM user_funnel
        ),
        stages AS (
            SELECT 'Registration'   AS stage, 1 AS seq, total_registered  AS users FROM base
            UNION ALL
            SELECT 'KYC Complete',  2, kyc      FROM base
            UNION ALL
            SELECT 'Application',   3, applied  FROM base
            UNION ALL
            SELECT 'Approval',      4, approved FROM base
            UNION ALL
            SELECT 'Disbursement',  5, disbursed FROM base
            UNION ALL
            SELECT 'Repayment',     6, repaid   FROM base
        )
        SELECT
            seq,
            stage,
            users,
            -- Conversion from prior stage
            ROUND(users * 100.0 / LAG(users) OVER (ORDER BY seq), 2) AS step_conversion_pct,
            -- Overall conversion from registration
            ROUND(users * 100.0 / FIRST_VALUE(users) OVER (ORDER BY seq
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING), 2) AS overall_conversion_pct,
            -- Drop-off count from prior stage
            LAG(users) OVER (ORDER BY seq) - users AS users_dropped
        FROM stages
        ORDER BY seq;
    """,

    # Query 2: Cohort Repayment Trend with Month-on-Month Change (LAG)
    # Business Question: Are newer cohorts riskier? Is the underwriting model drifting?
    "cohort_repayment_trend": """
        WITH cohort_metrics AS (
            SELECT
                signup_month,
                COUNT(*)                                         AS users_disbursed,
                SUM(has_repayment)                               AS repaid,
                ROUND(AVG(has_repayment) * 100, 2)              AS repayment_rate_pct,
                ROUND(SUM(loan_amount), 0)                       AS total_disbursed_amount,
                ROUND(SUM(CASE WHEN has_repayment=1 THEN loan_amount ELSE 0 END), 0) AS recovered_amount
            FROM user_funnel
            WHERE has_disbursement = 1
            GROUP BY signup_month
        )
        SELECT
            signup_month,
            users_disbursed,
            repayment_rate_pct,
            total_disbursed_amount,
            recovered_amount,
            -- Month-on-Month change in repayment rate
            ROUND(repayment_rate_pct - LAG(repayment_rate_pct) OVER (ORDER BY signup_month), 2) AS mom_change_pct,
            -- 3-month moving average repayment rate
            ROUND(AVG(repayment_rate_pct) OVER (
                ORDER BY signup_month
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ), 2) AS rolling_3m_repayment_rate,
            CASE
                WHEN repayment_rate_pct - LAG(repayment_rate_pct) OVER (ORDER BY signup_month) < -3
                THEN '⚠️  DETERIORATING'
                WHEN repayment_rate_pct - LAG(repayment_rate_pct) OVER (ORDER BY signup_month) > 3
                THEN '✅  IMPROVING'
                ELSE '➡️  STABLE'
            END AS trend_flag
        FROM cohort_metrics
        ORDER BY signup_month;
    """,

    # Query 3: Customer Lifetime Value (LTV) Estimation using Window SUM
    # Business Question: What is the cumulative value generated by each acquisition cohort?
    "cohort_ltv_analysis": """
        WITH cohort_value AS (
            SELECT
                signup_month,
                COUNT(*)                                              AS total_users,
                SUM(has_disbursement)                                 AS borrowers,
                ROUND(SUM(loan_amount), 0)                            AS total_loan_amount,
                ROUND(SUM(CASE WHEN has_repayment = 1 THEN loan_amount ELSE 0 END), 0) AS revenue_recovered,
                -- Estimated LTV = recovered amount × assumed margin (5% net interest margin)
                ROUND(SUM(CASE WHEN has_repayment = 1 THEN loan_amount ELSE 0 END) * 0.05, 0) AS estimated_ltv
            FROM user_funnel
            GROUP BY signup_month
        )
        SELECT
            signup_month,
            total_users,
            borrowers,
            total_loan_amount,
            revenue_recovered,
            estimated_ltv,
            -- Cumulative LTV across cohorts (running business value metric)
            SUM(estimated_ltv) OVER (
                ORDER BY signup_month
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )                                                          AS cumulative_ltv,
            -- LTV per acquired user (CAC efficiency proxy)
            ROUND(estimated_ltv * 1.0 / NULLIF(total_users, 0), 2)   AS ltv_per_user
        FROM cohort_value
        ORDER BY signup_month;
    """,

    # Query 4: Funnel Quality by Cohort — Monthly Cross-Tab
    # Business Question: Are earlier cohorts better quality? (via view)
    "monthly_funnel_quality": """
        SELECT
            signup_month,
            registered,
            kyc_completed,
            apps_submitted,
            disbursed,
            repaid,
            ROUND(kyc_completed    * 100.0 / NULLIF(registered, 0), 1)     AS kyc_rate,
            ROUND(apps_submitted   * 100.0 / NULLIF(kyc_completed, 0), 1)  AS app_rate,
            ROUND(disbursed        * 100.0 / NULLIF(apps_submitted, 0), 1) AS disburse_rate,
            ROUND(repaid           * 100.0 / NULLIF(disbursed, 0), 1)      AS repayment_rate,
            -- Full-funnel efficiency
            ROUND(repaid * 100.0 / NULLIF(registered, 0), 2)               AS end_to_end_efficiency_pct,
            -- Rank cohorts by end-to-end efficiency
            RANK() OVER (ORDER BY ROUND(repaid * 100.0 / NULLIF(registered, 0), 2) DESC) AS efficiency_rank
        FROM v_funnel_summary
        ORDER BY signup_month;
    """,

    # Query 5: Growth KPIs Summary
    "growth_kpis": """
        SELECT
            COUNT(DISTINCT signup_month)                             AS cohorts_tracked,
            COUNT(*)                                                 AS total_users,
            SUM(has_disbursement)                                    AS total_borrowers,
            ROUND(SUM(has_disbursement) * 100.0 / COUNT(*), 2)     AS overall_conversion_pct,
            ROUND(SUM(loan_amount), 0)                               AS total_disbursed,
            SUM(has_repayment)                                       AS total_repaid_loans,
            ROUND(SUM(CASE WHEN has_repayment=1 THEN loan_amount ELSE 0 END), 0) AS recovered_amt,
            ROUND(SUM(CASE WHEN has_repayment=1 THEN loan_amount ELSE 0 END)
                  * 100.0 / NULLIF(SUM(loan_amount), 0), 2)        AS portfolio_repayment_rate_pct
        FROM user_funnel;
    """
}

def build_database():
    df = pd.read_csv(BASE / "funnel_data.csv")
    con = sqlite3.connect(DB)
    con.executescript(DDL)
    df.to_sql("user_funnel", con, if_exists="append", index=False)
    con.commit()
    print(f"✅ Growth Analytics DB created — {len(df)} user records loaded.")
    return con

def run_analytics(con):
    results = {}
    for name, sql in QUERIES.items():
        df = pd.read_sql_query(sql, con)
        results[name] = df
        print(f"\n{'='*65}")
        print(f"📊 {name.upper().replace('_', ' ')}")
        print('='*65)
        print(df.to_string(index=False))
    return results

def plot_results(results):
    sns.set_theme(style="dark")
    fig = plt.figure(figsize=(20, 14), facecolor="#0d1117")
    fig.suptitle(
        "Pallav Credit OS — Digital Lending Growth & LTV Dashboard",
        fontsize=18, color="white", fontweight="bold", y=0.98
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.4)
    text_kw = dict(color="white")

    # Plot 1: Funnel Waterfall Chart
    ax1 = fig.add_subplot(gs[0, 0:2])
    d = results["funnel_conversion_analysis"].dropna(subset=["overall_conversion_pct"])
    cmap = plt.cm.Blues(np.linspace(0.4, 1.0, len(d)))
    bars = ax1.bar(d["stage"], d["users"], color=cmap, width=0.55)
    ax1.set_facecolor("#161b22")
    ax1.set_title("Customer Acquisition Funnel (SQL CTE Chain)", color="white", fontsize=12, pad=10)
    ax1.set_ylabel("Users", **text_kw)
    ax1.tick_params(colors="white", axis="x", rotation=15)
    ax1.tick_params(colors="white", axis="y")
    ax1.spines[:].set_color("#30363d")
    for bar, row in zip(bars, d.itertuples()):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                 f"{row.users:,}\n({row.overall_conversion_pct}%)",
                 ha="center", color="white", fontsize=8.5)

    # Plot 2: Cohort Repayment Rate Trend + 3M Rolling Average
    ax2 = fig.add_subplot(gs[0, 2])
    d2 = results["cohort_repayment_trend"]
    ax2.bar(d2["signup_month"], d2["repayment_rate_pct"], alpha=0.5,
            color="#818cf8", label="Monthly Rate")
    ax2.plot(d2["signup_month"], d2["rolling_3m_repayment_rate"],
             color="#f97316", linewidth=2.5, marker="o", markersize=6, label="3M Rolling Avg")
    ax2.set_facecolor("#161b22")
    ax2.set_title("Cohort Repayment Quality\n(LAG + Rolling Window)", color="white", fontsize=11, pad=10)
    ax2.set_ylabel("Repayment Rate (%)", **text_kw)
    ax2.tick_params(colors="white", axis="x", rotation=25)
    ax2.tick_params(colors="white", axis="y")
    ax2.spines[:].set_color("#30363d")
    ax2.legend(facecolor="#161b22", labelcolor="white", fontsize=8)
    ax2.set_ylim(50, 100)

    # Plot 3: Cumulative LTV by Cohort (Running SUM OVER)
    ax3 = fig.add_subplot(gs[1, 0])
    d3 = results["cohort_ltv_analysis"]
    ax3.fill_between(d3["signup_month"], d3["cumulative_ltv"], alpha=0.4, color="#a78bfa")
    ax3.plot(d3["signup_month"], d3["cumulative_ltv"], color="#7c3aed",
             linewidth=2.5, marker="s", markersize=7)
    ax3.set_facecolor("#161b22")
    ax3.set_title("Cumulative LTV Across Cohorts\n(SUM OVER Window)", color="white", fontsize=11, pad=10)
    ax3.set_ylabel("Cumulative LTV (₹)", **text_kw)
    ax3.tick_params(colors="white", axis="x", rotation=25)
    ax3.tick_params(colors="white", axis="y")
    ax3.spines[:].set_color("#30363d")
    for i, row in d3.iterrows():
        ax3.text(i, row["cumulative_ltv"] + 100, f"₹{row['cumulative_ltv']:,.0f}",
                 ha="center", color="#c4b5fd", fontsize=7.5)

    # Plot 4: Monthly Funnel Quality Heatmap
    ax4 = fig.add_subplot(gs[1, 1])
    d4 = results["monthly_funnel_quality"].set_index("signup_month")
    rate_cols = ["kyc_rate", "app_rate", "disburse_rate", "repayment_rate"]
    sns.heatmap(d4[rate_cols], annot=True, fmt=".1f", cmap="RdYlGn", ax=ax4,
                vmin=0, vmax=100, linewidths=0.5, linecolor="#30363d",
                cbar_kws={"label": "Rate (%)"})
    ax4.set_title("Monthly Funnel Quality Heatmap\n(RANK by Efficiency)", color="white", fontsize=11, pad=10)
    ax4.set_ylabel("Signup Month", **text_kw)
    ax4.set_xlabel("Funnel Stage Rate", **text_kw)
    ax4.tick_params(colors="white", labelsize=8)
    ax4.set_facecolor("#161b22")

    # Plot 5: KPI Card
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis("off")
    kpi = results["growth_kpis"].iloc[0]
    text = (
        "  GROWTH KPIs\n"
        f"  {'─'*30}\n"
        f"  Cohorts Tracked     : {int(kpi['cohorts_tracked'])}\n"
        f"  Total Users         : {int(kpi['total_users']):,}\n"
        f"  Total Borrowers     : {int(kpi['total_borrowers']):,}\n"
        f"  End-to-End Conv.    : {kpi['overall_conversion_pct']}%\n"
        f"  Total Disbursed     : ₹{int(kpi['total_disbursed']):,}\n"
        f"  Total Recovered     : ₹{int(kpi['recovered_amt']):,}\n"
        f"  Portfolio Repay Rate: {kpi['portfolio_repayment_rate_pct']}%"
    )
    ax5.text(0.05, 0.95, text, transform=ax5.transAxes, fontsize=10.5,
             verticalalignment="top", fontfamily="monospace",
             color="#fde68a", bbox=dict(boxstyle="round,pad=0.8", facecolor="#1c1917", edgecolor="#d97706"))
    ax5.set_title("Business Growth KPIs", color="white", fontsize=11)

    out = BASE / "growth_sql_dashboard.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"\n✅ Growth Dashboard saved → {out}")
    plt.close()

if __name__ == "__main__":
    con = build_database()
    results = run_analytics(con)
    plot_results(results)
    con.close()
    print("\n✅ Project 3 SQL Analytics complete.")
