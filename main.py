import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
import matplotlib.pyplot as plt
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, NamedStyle

# 1. SETUP LOGGING
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_mock_datasets():
    """Generates two mock CSVs to simulate CRM data and Core Banking data."""
    crm_file = "mock_crm_clients.csv"
    core_file = "mock_core_loans.csv"
    
    if not os.path.exists(crm_file) or not os.path.exists(core_file):
        logging.info("Generating mock CRM and Core Banking datasets...")
        np.random.seed(42)
        
        client_ids = range(5001, 5101)
        crm_data = pd.DataFrame({
            'client_id': client_ids,
            'client_type': np.random.choice(['Retail', 'SME'], 100),
            'industry': np.random.choice(['Tech', 'Retail', 'Construction', 'Services'], 100)
        })
        crm_data.to_csv(crm_file, index=False)
        
        core_data = pd.DataFrame({
            'loan_id': range(1001, 1101),
            'client_id': client_ids,
            'loan_amount': np.random.randint(10000, 250000, 100),
            'status': np.random.choice(['Active', 'Approved', 'Rejected', 'Pending'], 100, p=[0.4, 0.2, 0.3, 0.1]),
            'date_submitted': pd.date_range(start='2026-02-01', end='2026-02-28', periods=100).astype(str)
        })
        core_data.to_csv(core_file, index=False)
        logging.info("Mock datasets created successfully.")
        
    return crm_file, core_file

def generate_financial_report(crm_csv, core_csv):
    """Merges datasets, generates charts, and exports a styled Excel report."""
    report_name = f"Monthly_Financial_Report_{datetime.now().strftime('%Y_%m')}.xlsx"
    chart_filename = "status_chart.png"
    
    try:
        logging.info("Loading and merging datasets...")
        crm_df = pd.read_csv(crm_csv)
        core_df = pd.read_csv(core_csv)
        merged_df = pd.merge(core_df, crm_df, on='client_id', how='left')
        
        # --- CALCULATE METRICS ---
        active_loans = merged_df[merged_df['status'] == 'Active']
        summary_data = {
            'Metric': [
                'Total Portfolio Value', 
                'Number of Active Loans', 
                'Loans Approved This Month', 
                'Average Loan Size'
            ],
            'Value': [
                active_loans['loan_amount'].sum(), 
                len(active_loans), 
                len(merged_df[merged_df['status'] == 'Approved']), 
                merged_df['loan_amount'].mean()
            ]
        }
        
        # Breakdowns
        industry_summary = merged_df.groupby('industry').agg(
            Total_Loans=('loan_id', 'count'),
            Active_Portfolio_Value=('loan_amount', lambda x: x[merged_df['status'] == 'Active'].sum())
        ).reset_index()
        
        client_type_summary = merged_df.groupby('client_type').agg(
            Total_Loans=('loan_id', 'count'),
            Active_Portfolio_Value=('loan_amount', lambda x: x[merged_df['status'] == 'Active'].sum())
        ).reset_index()

        # --- GENERATE CHART ---
        logging.info("Generating data visualization...")
        plt.figure(figsize=(7, 4))
        status_counts = merged_df['status'].value_counts()
        status_counts.plot(kind='bar', color=['#4CAF50', '#2196F3', '#F44336', '#FF9800'])
        plt.title('Loan Pipeline Status Overview', fontsize=12)
        plt.ylabel('Number of Applications')
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(chart_filename)
        plt.close()

        # --- GENERATE & STYLE EXCEL ---
        logging.info(f"Writing and styling report: {report_name}...")
        with pd.ExcelWriter(report_name, engine='openpyxl') as writer:
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Executive Summary', index=False)
            client_type_summary.to_excel(writer, sheet_name='Client Breakdown', index=False)
            industry_summary.to_excel(writer, sheet_name='Industry Breakdown', index=False)
            merged_df.to_excel(writer, sheet_name='Merged Raw Data', index=False)

            # Access the workbook to add styles and images
            workbook = writer.book
            
            # Format Executive Summary Tab
            ws_summary = workbook['Executive Summary']
            ws_summary.column_dimensions['A'].width = 30
            ws_summary.column_dimensions['B'].width = 20
            
            # Make headers bold
            for cell in ws_summary["1:1"]:
                cell.font = Font(bold=True)
            
            # Format currency cells in Summary
            currency_style = NamedStyle(name="currency", number_format='"$"#,##0.00')
            ws_summary['B2'].style = currency_style # Total Portfolio
            ws_summary['B5'].style = currency_style # Avg Loan Size
            
            # Embed the Chart into the Excel file
            img = OpenpyxlImage(chart_filename)
            ws_summary.add_image(img, 'D2') # Places chart next to the data table

        logging.info("Report generation completed successfully.")
        print(f"Success! Report generated: {report_name}")

    except Exception as e:
        logging.error(f"Report generation failed: {e}")
        print("An error occurred. Please check 'pipeline.log' for details.")

if __name__ == "__main__":
    print("Initializing Automated Data Pipeline...")
    crm_file, core_file = generate_mock_datasets()
    generate_financial_report(crm_file, core_file)