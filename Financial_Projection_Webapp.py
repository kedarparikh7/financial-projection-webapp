# Import necessary libraries
import pandas as pd
from fpdf import FPDF

# Placeholder data input structure for GUI (to be built using Streamlit, Tkinter, etc.)
# Four upload buttons - 2 for Balance Sheet, 2 for P&L Statements

# Sample input from balance sheet and P&L of last 2 years (to be replaced by uploaded files)
data = {
    'Particulars': [
        'Paid up Capital', 'Reserves & Surplus', 'Intangible assets', 'Tangible Net Worth',
        'Long Term Liabilities', 'Unsecured loans or Quasi Equity', 'Capital Employed',
        'Net Block', 'Investments', 'Non Current Assets', 'Net Working Capital',
        'Current Assets', 'Current Liabilities', 'Current Ratio', 'DER (TL/TNW)',
        'TOL/TNW Ratio', 'Net Sales', 'Cost of Sales', 'Operating Profit/EBDITA',
        'Other Income', 'Interest/Finance Charges', 'Depreciation', 'Tax',
        'Net Profit after Tax', 'Cash Accruals'
    ],
    'FY2023': [
        1000000, 300000, 50000, 1300000,
        400000, 100000, 1800000,
        800000, 200000, 1100000, 700000,
        1200000, 500000, 2.4, 0.31,
        0.42, 2000000, 1700000, 200000,
        30000, 40000, 80000, 15000,
        95000, 175000
    ],
    'FY2024': [
        1000000, 500000, 50000, 1550000,
        350000, 120000, 2020000,
        880000, 220000, 1250000, 770000,
        1300000, 530000, 2.45, 0.23,
        0.39, 2400000, 2040000, 240000,
        32000, 42000, 85000, 18000,
        115000, 200000
    ]
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Projections based on assumptions
for year in ['FY2025', 'FY2026', 'FY2027']:
    previous_year = df.columns[-1]
    sales = df.loc[df['Particulars'] == 'Net Sales', previous_year].values[0] * 1.2
    cost = 0.85 * sales
    ebitda = 0.10 * sales
    other_income = 30000
    interest = 45000
    dep = df.loc[df['Particulars'] == 'Depreciation', previous_year].values[0] * 1.10
    tax = 0.25 * (ebitda + other_income - interest - dep)
    net_profit = 0.06 * sales
    cash_accruals = net_profit + dep

    new_col = [
        df.loc[df['Particulars'] == 'Paid up Capital', previous_year].values[0] + 0.5 * df.loc[df['Particulars'] == 'Cash Accruals', previous_year].values[0],
        df.loc[df['Particulars'] == 'Reserves & Surplus', previous_year].values[0] + net_profit,
        df.loc[df['Particulars'] == 'Intangible assets', previous_year].values[0],
        0,  # To be calculated
        df.loc[df['Particulars'] == 'Long Term Liabilities', previous_year].values[0],
        df.loc[df['Particulars'] == 'Unsecured loans or Quasi Equity', previous_year].values[0],
        0,  # Capital Employed = TNW + Long Term Liab + Quasi Eq
        df.loc[df['Particulars'] == 'Net Block', previous_year].values[0] + (30000 if year=='FY2025' else 50000) - dep,
        df.loc[df['Particulars'] == 'Investments', previous_year].values[0] * 1.10,
        0,  # Non Current Assets = Net Block + Investments
        0,  # NWC
        0,  # Current Assets
        0,  # Current Liabilities
        0,  # Current Ratio
        0,  # DER
        0,  # TOL/TNW
        sales,
        cost,
        ebitda,
        other_income,
        interest,
        dep,
        tax,
        net_profit,
        cash_accruals
    ]

    # Derived calculations
    tnw = new_col[0] + new_col[1] - new_col[2]
    new_col[3] = tnw
    cap_emp = tnw + new_col[4] + new_col[5]
    new_col[6] = cap_emp
    non_curr = new_col[7] + new_col[8]
    new_col[9] = non_curr

    debtors = (sales / 365) * 45
    stock = (cost / 365) * 60
    cash = 0.05 * sales
    curr_assets = debtors + stock + cash
    creditors = (cost / 365) * 30
    nwc = curr_assets - creditors
    new_col[10] = nwc
    new_col[11] = curr_assets
    new_col[12] = creditors
    new_col[13] = round(curr_assets / creditors, 2)
    new_col[14] = round(new_col[4] / tnw, 2)
    new_col[15] = round((new_col[4] + new_col[12]) / tnw, 2)

    # Append column
    df[year] = new_col

# Export to TXT
df.to_csv("financial_projection.txt", sep='\t', index=False)

# Export to PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=10)
pdf.cell(200, 10, txt="Financial Projections Report", ln=True, align='C')

# Add table rows
for i, row in df.iterrows():
    pdf.cell(200, 10, txt=row['Particulars'], ln=True)
    for col in df.columns[1:]:
        pdf.cell(200, 10, txt=f"{col}: {row[col]}", ln=True)
    pdf.cell(200, 5, txt="", ln=True)

pdf.output("financial_projection.pdf")
