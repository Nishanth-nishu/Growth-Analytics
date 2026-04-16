"""
=============================================================================
PROJECT 3: Digital Lending Growth & Portfolio Quality
Python Analytics Engine for Cohort Health
=============================================================================
Dataset: LendingClub Real Performance Data
Goal: Analyze repayment trends and volume growth by cohort
=============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Paths are now relative for portability
BASE = Path(".")
DATA_PATH = Path("lending_club_openintro.csv")

sns.set_theme(style="whitegrid", palette="Set2")

def run_growth_analysis():
    print("🚀 Loading LendingClub data for cohort analysis...")
    if not DATA_PATH.exists():
        print(f"❌ Data file not found: {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)

    # 1. Monthly Cohort Repayment Analysis
    # Track the percentage of "Fully Paid" loans by issuance month
    df['is_fully_paid'] = (df['loan_status'] == 'Fully Paid').astype(int)
    
    cohort_data = df.groupby('issue_month').agg({
        'loan_amount': 'sum',
        'is_fully_paid': 'mean',
        'interest_rate': 'mean'
    }).rename(columns={
        'loan_amount': 'Total_Volume',
        'is_fully_paid': 'Repayment_Rate',
        'interest_rate': 'Avg_Int_Rate'
    })
    
    print("\n📈 Cohort Repayment Summary:")
    print(cohort_data)

    # 2. Visualizing Volume vs Quality (The Dual-Axis Growth View)
    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.set_xlabel('Issue Month')
    ax1.set_ylabel('Disbursement Volume (₹)', color='tab:blue')
    sns.barplot(x=cohort_data.index, y=cohort_data['Total_Volume'], ax=ax1, color='lightblue', label='Loan Volume')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Repayment Rate (%)', color='tab:red')
    sns.lineplot(x=cohort_data.index, y=cohort_data['Repayment_Rate'], ax=ax2, marker='o', color='tab:red', linewidth=3, label='Repayment Rate')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    plt.title('Disbursement Growth vs. Repayment Quality by Cohort', fontsize=16)
    plt.savefig(BASE / "cohort_repayment.png")
    
    # 3. Interest Yield vs Risk Analysis
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='Avg_Int_Rate', y='Repayment_Rate', size='Total_Volume', data=cohort_data, hue=cohort_data.index)
    plt.title('Interest Rate Yield vs. Recovery Rate (Cohort Size Analysis)', fontsize=14)
    plt.savefig(BASE / "acquisition_funnel.png") # Re-using filename for compatibility with README links

    print(f"✨ Growth and cohort visuals generated at {BASE}")

if __name__ == "__main__":
    run_growth_analysis()
