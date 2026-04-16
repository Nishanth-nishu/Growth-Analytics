import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", palette="Spectral")

def run_growth_analysis():
    # 1. Load Data
    df = pd.read_csv('/scratch/nishanth.r/pallavi/project_3_growth_analytics/funnel_data.csv')
    
    # 2. Funnel Conversion Analysis
    stages = ['Registered', 'KYC', 'Application', 'Approval', 'Disbursement']
    counts = [
        len(df),
        df['has_kyc'].sum(),
        df['has_application'].sum(),
        df['has_approval'].sum(),
        df['has_disbursement'].sum()
    ]
    
    funnel_df = pd.DataFrame({'Stage': stages, 'Count': counts})
    funnel_df['Conversion_Rate (%)'] = (funnel_df['Count'] / len(df) * 100).round(2)
    
    print("\nFunnel Conversion Summary:")
    print(funnel_df)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Stage', y='Count', data=funnel_df)
    for i, v in enumerate(counts):
        plt.text(i, v + 20, f"{v}\n({(v/len(df)*100):.1f}%)", ha='center', fontweight='bold')
    plt.title('Fintech Customer Acquisition Funnel')
    plt.savefig('/scratch/nishanth.r/pallavi/project_3_growth_analytics/acquisition_funnel.png')
    
    # 3. Cohort Repayment Analysis
    # We look at repayment rates by signup month
    cohort_data = df[df['has_disbursement'] == 1].groupby('signup_month').agg({
        'user_id': 'count',
        'has_repayment': 'mean'
    }).rename(columns={'user_id': 'Loan_Count', 'has_repayment': 'Repayment_Rate'})
    
    print("\nCohort Repayment Analysis:")
    print(cohort_data)
    
    plt.figure(figsize=(10, 6))
    plt.plot(cohort_data.index, cohort_data['Repayment_Rate'], marker='o', linewidth=3, color='darkred')
    plt.title('Loan Repayment Rate by Signup Cohort')
    plt.ylim(0, 1)
    plt.ylabel('Repayment Rate (Probability)')
    plt.grid(True, linestyle='--')
    plt.savefig('/scratch/nishanth.r/pallavi/project_3_growth_analytics/cohort_repayment.png')
    
    # 4. Identification of Risk Trend
    cohort_data_reset = cohort_data.reset_index()
    cohort_data_reset['month_num'] = range(len(cohort_data_reset))
    correlation = cohort_data_reset['month_num'].corr(cohort_data_reset['Repayment_Rate'])
    print(f"\nTime-based Repayment Trend (Correlation): {correlation:.2f}")
    if correlation < -0.5:
        print("WARNING: Repayment rates are declining in newer cohorts. Investigation required.")

    print("\nSaved Growth and Funnel plots.")

if __name__ == "__main__":
    run_growth_analysis()
