# Growth & LTV Funnel Analytics

A comprehensive analysis of the digital lending acquisition funnel and customer lifetime value (LTV) for a fintech "Credit Operating System." This project focuses on optimizing marketing spend and identifying repayment trends across cohorts.

## Key Features
- **Funnel Conversion Tracking**: Analyzes drop-offs at each stage: Registration -> KYC -> Application -> Approval -> Disbursement.
- **Cohort Analysis**: Tracks repayment rates by signup month to monitor portfolio health over time.
- **Trend Detection**: Identifies potential risk shifts in newer customer segments through time-based correlation analysis.

## Results
- **Funnel Insight**: Found a critical conversion bottleneck at the **Loan Application** stage (46% drop-off).
- **Cohort Insight**: Detected a downward trend in repayment quality for newer cohorts, dropping from **91% (January)** to **69% (June)**.

## Project Structure
- `growth_analysis.py`: Main funnel and cohort analysis script.
- `growth_data_generator.py`: Synthetic funnel event generator.
- `funnel_data.csv`: Sample event dataset.
- `*.png`: Visualizations of the acquisition funnel and cohort repayment trends.

---
*Created for Pallav Technologies Data Analyst Portfolio.*
