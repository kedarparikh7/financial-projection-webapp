
import streamlit as st
import pandas as pd
import PyPDF2
import re
import io

def extract_text_from_pdf(uploaded_file):
    text = ""
    reader = PyPDF2.PdfReader(uploaded_file)
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_financials(text):
    lines = text.split('\n')
    data = {}
    for line in lines:
        match = re.match(r"(.+?)\s+([-]?[\d,]+\.?\d*)$", line.strip())
        if match:
            key = match.group(1).strip()
            value = float(match.group(2).replace(',', ''))
            data[key] = value
    return data

def project_values(base_value, growth_rate, years):
    return [round(base_value * ((1 + growth_rate) ** i), 2) for i in range(1, years + 1)]

def generate_projection(bs_data, pl_data, assumptions, current_year):
    years = [f"{current_year-1}-{str(current_year)[-2:]}", f"{current_year}-{str(current_year+1)[-2:]}"]
    proj_years = [f"{current_year+i}-{str(current_year+i+1)[-2:]}" for i in range(1, 4)]
    all_years = years + proj_years

    net_sales = pl_data.get("Sales Accounts", 1000000)
    cost_of_sales = pl_data.get("Purchase Accounts", net_sales * 0.85)

    index = ["Net Sales", "Cost of Sales", "Operating Profit/EBDITA", "Net Profit after Tax", "Cash Accruals"]
    df = pd.DataFrame(index=index, columns=all_years)

    df.loc["Net Sales", years[-1]] = net_sales
    df.loc["Cost of Sales", years[-1]] = cost_of_sales
    df.loc["Operating Profit/EBDITA", years[-1]] = net_sales * assumptions['ebitda_margin']
    df.loc["Net Profit after Tax", years[-1]] = net_sales * assumptions['net_margin']
    df.loc["Cash Accruals", years[-1]] = df.loc["Net Profit after Tax", years[-1]] + assumptions['depreciation_start']

    for i, y in enumerate(proj_years):
        ns = project_values(net_sales, assumptions['sales_growth'], 3)[i]
        cs = ns * assumptions['cost_percent']
        ebitda = ns * assumptions['ebitda_margin']
        net_profit = ns * assumptions['net_margin']
        dep = assumptions['depreciation_start'] if i == 0 else assumptions['depreciation_next']

        df.loc["Net Sales", y] = ns
        df.loc["Cost of Sales", y] = cs
        df.loc["Operating Profit/EBDITA", y] = ebitda
        df.loc["Net Profit after Tax", y] = net_profit
        df.loc["Cash Accruals", y] = net_profit + dep

    return df

# Streamlit UI
st.title("Financial Projection Generator")

bs_file = st.file_uploader("Upload Balance Sheet PDF", type="pdf")
pl_file = st.file_uploader("Upload Profit & Loss PDF", type="pdf")

with st.sidebar:
    st.header("Projection Assumptions")
    sales_growth = st.number_input("Net Sales Growth (%)", value=20) / 100
    cost_percent = st.number_input("Cost of Sales (% of Sales)", value=85) / 100
    ebitda_margin = st.number_input("EBITDA Margin (%)", value=10) / 100
    net_margin = st.number_input("Net Profit Margin (%)", value=6) / 100
    depreciation_start = st.number_input("Depreciation FY1", value=5000)
    depreciation_next = st.number_input("Depreciation FY2/FY3", value=10000)

if bs_file and pl_file:
    bs_text = extract_text_from_pdf(bs_file)
    pl_text = extract_text_from_pdf(pl_file)
    bs_data = extract_financials(bs_text)
    pl_data = extract_financials(pl_text)

    assumptions = {
        'sales_growth': sales_growth,
        'cost_percent': cost_percent,
        'ebitda_margin': ebitda_margin,
        'net_margin': net_margin,
        'depreciation_start': depreciation_start,
        'depreciation_next': depreciation_next
    }

    df_result = generate_projection(bs_data, pl_data, assumptions, current_year=2024)
    st.success("Projection generated successfully!")
    st.dataframe(df_result)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, sheet_name="Projections")
        writer.close()
    st.download_button("Download Excel", data=buffer.getvalue(), file_name="Financial_Projection.xlsx")
