# Streamlit Web App for Dynamic Financial Projections
import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

st.set_page_config(page_title="Financial Projection Generator")
st.title("📊 Financial Projection Report Generator")
st.markdown("Upload your Balance Sheet and Profit & Loss statements for the last 2 years to generate a 3-year financial projection report.")

# Upload sections
st.header("📂 Upload Financial Statements")
col1, col2 = st.columns(2)

with col1:
    bs1 = st.file_uploader("Upload Balance Sheet - FY1", type=["csv", "xlsx"], key="bs1")
    bs2 = st.file_uploader("Upload Balance Sheet - FY2", type=["csv", "xlsx"], key="bs2")

with col2:
    pl1 = st.file_uploader("Upload P&L Statement - FY1", type=["csv", "xlsx"], key="pl1")
    pl2 = st.file_uploader("Upload P&L Statement - FY2", type=["csv", "xlsx"], key="pl2")

if all([bs1, bs2, pl1, pl2]):
    def read_file(file):
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)

    # Read uploaded files
    df_bs1 = read_file(bs1).set_index('Particulars')
    df_bs2 = read_file(bs2).set_index('Particulars')
    df_pl1 = read_file(pl1).set_index('Particulars')
    df_pl2 = read_file(pl2).set_index('Particulars')

    # Merge into one dataframe
    df = pd.DataFrame(index=df_bs1.index.union(df_pl1.index))
    df['FY2023'] = df_bs1['Value'].combine_first(df_pl1['Value'])
    df['FY2024'] = df_bs2['Value'].combine_first(df_pl2['Value'])

    # Start projections
    for year in ['FY2025', 'FY2026', 'FY2027']:
        prev_year = df.columns[-1]
        sales = df.at['Net Sales', prev_year] * 1.2
        cost = 0.85 * sales
        ebitda = 0.10 * sales
        other_income = 30000
        interest = 45000
        dep = df.at['Depreciation', prev_year] * 1.10
        tax = 0.25 * (ebitda + other_income - interest - dep)
        net_profit = 0.06 * sales
        cash_accruals = net_profit + dep

        paid_up = df.at['Paid up Capital', prev_year] + 0.5 * df.at['Cash Accruals', prev_year]
        reserves = df.at['Reserves & Surplus', prev_year] + net_profit
        intangibles = df.at['Intangible assets', prev_year]
        tnw = paid_up + reserves - intangibles
        lt_liab = df.at['Long Term Liabilities', prev_year]
        unsecured = df.at['Unsecured loans or Quasi Equity', prev_year]
        cap_emp = tnw + lt_liab + unsecured
        net_block = df.at['Net Block', prev_year] + (30000 if year == 'FY2025' else 50000) - dep
        investments = df.at['Investments', prev_year] * 1.10
        non_current = net_block + investments

        debtors = (sales / 365) * 45
        stock = (cost / 365) * 60
        cash = 0.05 * sales
        curr_assets = debtors + stock + cash
        creditors = (cost / 365) * 30
        nwc = curr_assets - creditors
        curr_ratio = round(curr_assets / creditors, 2)
        der = round(lt_liab / tnw, 2)
        tol_tnw = round((lt_liab + creditors) / tnw, 2)

        df[year] = [
            paid_up, reserves, intangibles, tnw,
            lt_liab, unsecured, cap_emp,
            net_block, investments, non_current, nwc,
            curr_assets, creditors, curr_ratio, der,
            tol_tnw, sales, cost, ebitda,
            other_income, interest, dep, tax,
            net_profit, cash_accruals
        ]

    st.subheader("📈 Financial Summary Table")
    st.dataframe(df)

    # Export TXT
    txt = df.to_csv(sep='\t')
    st.download_button("Download TXT File", data=txt, file_name="financial_projection.txt")

    # Export PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Financial Projections Report", ln=True, align='C')

    for i, row in df.iterrows():
        pdf.cell(200, 10, txt=row.name, ln=True)
        for col in df.columns:
            pdf.cell(200, 10, txt=f"{col}: {row[col]}", ln=True)
        pdf.cell(200, 5, txt="", ln=True)

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    st.download_button("Download PDF Report", data=pdf_buffer.getvalue(), file_name="financial_projection.pdf", mime="application/pdf")

else:
    st.warning("Please upload all 4 files to proceed.")
