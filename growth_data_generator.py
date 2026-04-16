import pandas as pd
import numpy as np
import os

def generate_growth_funnel_data(n_users=2000):
    np.random.seed(123)
    
    # Months for Cohorts
    months = ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06']
    
    users = range(10000, 10000 + n_users)
    signup_month = np.random.choice(months, size=n_users)
    
    # Funnel Drop-offs (Probabilities)
    # Registration -> KYC: 80%
    has_kyc = np.random.binomial(1, 0.8, size=n_users)
    
    # KYC -> Application: 70% of those with KYC
    has_app = np.where(has_kyc == 1, np.random.binomial(1, 0.7, size=n_users), 0)
    
    # Application -> Approval: 60% of those with App
    has_approval = np.where(has_app == 1, np.random.binomial(1, 0.6, size=n_users), 0)
    
    # Approval -> Disbursement: 95% of those with Approval
    has_disbursement = np.where(has_approval == 1, np.random.binomial(1, 0.95, size=n_users), 0)
    
    loan_amount = np.where(has_disbursement == 1, np.random.uniform(100, 1000), 0)
    
    # Repayment behavior (Cohort dependent - later cohorts might be riskier)
    # 0 = No, 1 = Yes
    repayment_prob = np.where(has_disbursement == 1, 0.85, 0)
    # Subtract 0.05 for later months to show trend
    for i, m in enumerate(months):
        repayment_prob = np.where((signup_month == m) & (has_disbursement == 1), 0.9 - (i * 0.03), repayment_prob)
        
    has_repayment = np.random.binomial(1, repayment_prob)
    
    df = pd.DataFrame({
        'user_id': users,
        'signup_month': signup_month,
        'has_kyc': has_kyc,
        'has_application': has_app,
        'has_approval': has_approval,
        'has_disbursement': has_disbursement,
        'loan_amount': loan_amount,
        'has_repayment': has_repayment
    })
    
    output_path = '/scratch/nishanth.r/pallavi/project_3_growth_analytics/funnel_data.csv'
    df.to_csv(output_path, index=False)
    print(f"Growth Funnel dataset generated at {output_path}")

if __name__ == "__main__":
    generate_growth_funnel_data()
