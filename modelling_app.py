import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go
from io import StringIO
import base64
import datetime

# --- Set up the Streamlit app layout ---
st.set_page_config(layout="wide", page_title="Comprehensive M&A Financial Model")
st.title("Comprehensive M&A Financial Modeling App 💰")
st.markdown("A one-stop platform for financial modeling, valuation, and M&A analysis.")

# Add a script to handle clipboard functionality in the browser
# This script is a cleaner way to handle copying without a visible text area
st.markdown("""
<script>
function copyTextToClipboard(text) {
  navigator.clipboard.writeText(text).then(function() {
    // Show a success message
    alert('Report copied to clipboard! You can now paste it into a document.');
  }, function(err) {
    // Show an error message
    alert('Could not copy text: ' + err);
  });
}
</script>
""", unsafe_allow_html=True)

# --- Mock Exchange Rates, Industry, Comps & Precedents Data ---
# In a real-world scenario, this data would come from a financial API.
EXCHANGE_RATES = {
    "USD": 1.0,
    "NGN": 1500.0,
    "EUR": 0.92,
    "GBP": 0.80,
    "JPY": 155.0,
    "CAD": 1.35,
}

INDUSTRY_DATA = {
    "Technology": {"P/E Ratio": 25.0, "EV/EBITDA": 18.0, "Net Profit Margin": 0.20},
    "Healthcare": {"P/E Ratio": 22.0, "EV/EBITDA": 15.0, "Net Profit Margin": 0.15},
    "FMCG (Consumer Goods)": {"P/E Ratio": 22.0, "EV/EBITDA": 17.0, "Net Profit Margin": 0.08},
    "Real Estate": {"P/E Ratio": 18.0, "EV/EBITDA": 12.0, "Net Profit Margin": 0.10},
    "Oil and Gas": {"P/E Ratio": 14.0, "EV/EBITDA": 8.0, "Net Profit Margin": 0.09},
    "Renewable Energy": {"P/E Ratio": 28.0, "EV/EBITDA": 20.0, "Net Profit Margin": 0.12},
    "Automobile": {"P/E Ratio": 15.0, "EV/EBITDA": 10.0, "Net Profit Margin": 0.07},
    "Agriculture": {"P/E Ratio": 16.0, "EV/EBITDA": 11.0, "Net Profit Margin": 0.06},
    "Insurance": {"P/E Ratio": 13.0, "EV/EBITDA": 9.0, "Net Profit Margin": 0.11},
    "Agro-allied": {"P/E Ratio": 17.0, "EV/EBITDA": 12.5, "Net Profit Margin": 0.07},
    "Banking": {"P/E Ratio": 12.0, "EV/EBITDA": 8.5, "Net Profit Margin": 0.25},
    "Education": {"P/E Ratio": 20.0, "EV/EBITDA": 14.0, "Net Profit Margin": 0.13},
    "Professional Services": {"P/E Ratio": 19.0, "EV/EBITDA": 13.0, "Net Profit Margin": 0.18},
    "Audit Firms": {"P/E Ratio": 15.0, "EV/EBITDA": 10.0, "Net Profit Margin": 0.22},
    "Retail": {"P/E Ratio": 21.0, "EV/EBITDA": 16.0, "Net Profit Margin": 0.04},
}

# Mock data for Comparable Company Analysis (Comps)
COMP_DATA = {
    "Company": ["Microsoft", "Google", "Amazon"],
    "Market Cap ($B)": [3000, 2200, 1900],
    "Revenue ($B)": [245, 307, 575],
    "EBITDA ($B)": [109, 84, 80],
    "Net Income ($B)": [72, 73, 30],
    "P/E Ratio": [41.6, 29.8, 115.5],
    "EV/EBITDA": [27.5, 26.2, 23.8]
}

# Mock data for Precedent Transaction Analysis
PRECEDENT_DATA = {
    "Transaction": ["Salesforce/Slack", "Microsoft/Activision", "IBM/Red Hat"],
    "Date": ["2021", "2022", "2019"],
    "EV ($B)": [27.7, 68.7, 34.0],
    "Target Revenue ($B)": [1.1, 8.5, 3.0],
    "EV/Revenue": [25.2, 8.1, 11.3]
}

# --- Sidebar for User Inputs ---
st.sidebar.header("User Inputs & API Settings")
currency_options = list(EXCHANGE_RATES.keys())
selected_currency = st.sidebar.selectbox("Select Display Currency", options=currency_options)
industry_options = list(INDUSTRY_DATA.keys())
selected_industry = st.sidebar.selectbox("Select Industry for Comparison", options=industry_options)
industry_benchmarks = INDUSTRY_DATA[selected_industry]

st.sidebar.markdown("---")
st.sidebar.subheader("Financial Data Input")
input_method = st.sidebar.radio("Select Input Method", ["Simulated API", "Upload CSV/Excel"])

# --- Data Handling ---
acquirer_data_df = pd.DataFrame()
target_data_df = pd.DataFrame()

if input_method == "Simulated API":
    acquirer_name = st.sidebar.text_input("Acquirer Company Ticker", "AAPL")
    target_name = st.sidebar.text_input("Target Company Ticker", "NVDA")
    st.sidebar.info("Using mock data to simulate a financial API based on tickers.")
    
    # Mock data fetching function
    def fetch_mock_data(company_name):
        if company_name == "AAPL":
            return pd.DataFrame({
                'Metric': ['Revenue', 'EBITDA', 'Net_Income', 'Total_Assets', 'Total_Debt', 'Shares_Outstanding'],
                'Value': [383.3, 131.9, 97.0, 352.6, 290.4, 15.7]
            }).set_index('Metric')
        elif company_name == "NVDA":
            return pd.DataFrame({
                'Metric': ['Revenue', 'EBITDA', 'Net_Income', 'Total_Assets', 'Total_Debt', 'Shares_Outstanding'],
                'Value': [79.9, 53.6, 30.1, 74.3, 11.2, 2.5]
            }).set_index('Metric')
        else:
            return pd.DataFrame()

    acquirer_data_df = fetch_mock_data(acquirer_name)
    target_data_df = fetch_mock_data(target_name)

elif input_method == "Upload CSV/Excel":
    uploaded_file_acquirer = st.sidebar.file_uploader("Upload Acquirer's Financials (CSV or XLSX)", type=['csv', 'xlsx'])
    uploaded_file_target = st.sidebar.file_uploader("Upload Target's Financials (CSV or XLSX)", type=['csv', 'xlsx'])
    
    if uploaded_file_acquirer is not None and uploaded_file_target is not None:
        try:
            # Check file type and read accordingly
            if uploaded_file_acquirer.name.endswith('.xlsx'):
                acquirer_data_df = pd.read_excel(uploaded_file_acquirer, index_col=0)
            else:
                acquirer_data_df = pd.read_csv(uploaded_file_acquirer, index_col=0)
            
            if uploaded_file_target.name.endswith('.xlsx'):
                target_data_df = pd.read_excel(uploaded_file_target, index_col=0)
            else:
                target_data_df = pd.read_csv(uploaded_file_target, index_col=0)
                
            acquirer_name = "Uploaded Acquirer"
            target_name = "Uploaded Target"
        except Exception as e:
            st.sidebar.error(f"Error reading file: {e}. Please ensure the file is a valid CSV or XLSX format.")
    else:
        st.info("Please upload both CSV or Excel files to proceed with this method.")


if not acquirer_data_df.empty and not target_data_df.empty:
    # Check if the 'Value' column exists in both dataframes from the user upload
    if 'Value' not in acquirer_data_df.columns or 'Value' not in target_data_df.columns:
        st.error("Error: The uploaded files must contain a column named 'Value'. Please check your file format.")
        acquirer_data_df = pd.DataFrame() # Reset the dataframes to prevent further errors
        target_data_df = pd.DataFrame()
    else:
        acquirer_data = acquirer_data_df['Value'].to_dict()
        target_data = target_data_df['Value'].to_dict()
    
        conversion_rate = EXCHANGE_RATES[selected_currency]
        def convert_currency(value):
            return value * conversion_rate
        
        for metric in ['Revenue', 'EBITDA', 'Net_Income', 'Total_Assets', 'Total_Debt', 'Shares_Outstanding']:
            acquirer_data[metric] = convert_currency(acquirer_data[metric])
            target_data[metric] = convert_currency(target_data[metric])

        # --- Transaction Terms ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("Transaction Terms")
        offer_price_per_share_base = st.sidebar.number_input(f"Offer Price per Share (in USD)", value=15.0, step=0.5)
        synergy_value = st.sidebar.number_input(f"Synergy Value (EBITDA, in {selected_currency} millions)", value=15.0, step=1.0)
        stock_percent = st.sidebar.slider("Percent Stock Consideration", min_value=0, max_value=100, value=50)

        # --- Financial Ratios Section ---
        st.header("1. Financial Ratios & Industry Comparison 📊")
        def calculate_ratios(data):
            ratios = {}
            eps = data['Net_Income'] / data['Shares_Outstanding'] if data['Shares_Outstanding'] != 0 else np.nan
            pe_ratio = (data['Shares_Outstanding'] * eps) / data['Net_Income'] if data['Net_Income'] != 0 else np.nan
            ratios['P/E Ratio'] = pe_ratio
            
            market_cap = data['Shares_Outstanding'] * (data['Net_Income'] / data['Shares_Outstanding'] * (pe_ratio if not np.isnan(pe_ratio) else 15))
            enterprise_value = market_cap + data['Total_Debt']
            ratios['EV/EBITDA'] = enterprise_value / data['EBITDA'] if data['EBITDA'] != 0 else np.nan
            ratios['Net Profit Margin'] = data['Net_Income'] / data['Revenue'] if data['Revenue'] != 0 else np.nan
            return ratios

        ratios_acquirer = calculate_ratios(acquirer_data)
        ratios_target = calculate_ratios(target_data)

        ratio_comp_df = pd.DataFrame(index=INDUSTRY_DATA['Technology'].keys())
        ratio_comp_df[f'Acquirer ({selected_currency})'] = [ratios_acquirer.get(key, np.nan) for key in ratio_comp_df.index]
        ratio_comp_df[f'Target ({selected_currency})'] = [ratios_target.get(key, np.nan) for key in ratio_comp_df.index]
        ratio_comp_df[f'Industry Average ({selected_industry})'] = [industry_benchmarks.get(key, "N/A") for key in ratio_comp_df.index]
        st.table(ratio_comp_df.style.format(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else str(x)))

        # --- Valuation Methodologies ---
        st.header("2. Valuation Methodologies 💵")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("DCF Valuation")
            dcf_years = 5
            growth_rate = 0.02
            wacc = 0.10
            projected_ebitda = [target_data['EBITDA'] * (1 + 0.05)**i for i in range(1, dcf_years + 1)]
            pv_ebitda = sum([ebitda / (1 + wacc)**i for i, ebitda in enumerate(projected_ebitda, 1)])
            terminal_value = (projected_ebitda[-1] * (1 + growth_rate)) / (wacc - growth_rate)
            pv_terminal_value = terminal_value / (1 + wacc)**dcf_years
            dcf_value = pv_ebitda + pv_terminal_value
            st.write(f"**Target's DCF Valuation:** `{selected_currency} {dcf_value:,.2f} billion`")

        with col2:
            st.subheader("Comparable Company Analysis (Comps)")
            comps_df = pd.DataFrame(COMP_DATA)
            comps_df['EV/EBITDA'] = comps_df['EV/EBITDA'] / 1000 # Convert to same scale
            average_ev_ebitda = comps_df['EV/EBITDA'].mean()
            comps_value = average_ev_ebitda * target_data['EBITDA']
            st.write(f"**Average EV/EBITDA:** `{average_ev_ebitda:.2f}`")
            st.write(f"**Target's Comps Valuation:** `{selected_currency} {comps_value:,.2f} billion`")

        with col3:
            st.subheader("Precedent Transaction Analysis")
            precedents_df = pd.DataFrame(PRECEDENT_DATA)
            precedents_df['EV/Revenue'] = precedents_df['EV/Revenue'] / 1000 # Convert to same scale
            average_ev_revenue = precedents_df['EV/Revenue'].mean()
            precedents_value = average_ev_revenue * target_data['Revenue']
            st.write(f"**Average EV/Revenue:** `{average_ev_revenue:.2f}`")
            st.write(f"**Target's Precedents Valuation:** `{selected_currency} {precedents_value:,.2f} billion`")
        
        # --- Deal Structure & Accretion/Dilution Analysis ---
        st.header("3. Deal Structure & Accretion/Dilution 🤝")
        
        # Pro Forma Income Statement
        eps_acquirer = acquirer_data['Net_Income'] / acquirer_data['Shares_Outstanding']
        acquirer_share_price = eps_acquirer * ratios_acquirer.get('P/E Ratio', 15)
        offer_price_per_share_converted = offer_price_per_share_base * conversion_rate
        
        purchase_price = offer_price_per_share_converted * target_data['Shares_Outstanding']
        cash_consideration = purchase_price * (100 - stock_percent) / 100
        stock_consideration = purchase_price * stock_percent / 100
        
        shares_issued = stock_consideration / acquirer_share_price
        total_pro_forma_shares = acquirer_data['Shares_Outstanding'] + shares_issued
        
        pro_forma_net_income = acquirer_data['Net_Income'] + target_data['Net_Income'] + (synergy_value * 1000000 * (1 - 0.25))
        pro_forma_eps = pro_forma_net_income / total_pro_forma_shares
        accretion_dilution = ((pro_forma_eps - eps_acquirer) / eps_acquirer) * 100
        
        summary_data = {"Metric": ["Acquirer EPS", "Pro Forma EPS", "Accretion / Dilution"],
                        "Value": [eps_acquirer, pro_forma_eps, accretion_dilution]}
        st.table(pd.DataFrame(summary_data).set_index("Metric").style.format(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else str(x)))
        
        if accretion_dilution > 0:
            st.success(f"**🎉 The transaction is ACCRETIVE to the acquirer's EPS by {accretion_dilution:.2f}%.**")
        else:
            st.error(f"**📉 The transaction is DILUTIVE to the acquirer's EPS by {accretion_dilution:.2f}%.**")

        # --- Pro Forma Balance Sheet & Goodwill Calculation ---
        st.header("4. Pro Forma Balance Sheet & Goodwill ⚖️")
        
        # Calculate Goodwill
        target_assets_fair_value = target_data['Total_Assets'] # Assume book value = fair value for simplicity
        target_liabilities = target_data['Total_Debt'] # For simplicity, Total_Debt = Total Liabilities
        target_equity = target_assets_fair_value - target_liabilities
        
        goodwill = purchase_price - target_equity
        
        st.write(f"**Goodwill Created:** `{selected_currency} {goodwill:,.2f} billion`")
        
        # Pro Forma Balance Sheet
        pro_forma_assets = acquirer_data['Total_Assets'] + target_assets_fair_value + goodwill
        pro_forma_liabilities = acquirer_data['Total_Debt'] + target_liabilities + cash_consideration
        pro_forma_equity = pro_forma_assets - pro_forma_liabilities
        
        bs_data = {
            "Acquirer": [acquirer_data['Total_Assets'], acquirer_data['Total_Debt'], acquirer_data['Total_Assets'] - acquirer_data['Total_Debt']],
            "Target": [target_assets_fair_value, target_liabilities, target_equity],
            "Pro Forma": [pro_forma_assets, pro_forma_liabilities, pro_forma_equity]
        }
        bs_df = pd.DataFrame(bs_data, index=["Total Assets", "Total Liabilities", "Total Equity"])
        st.table(bs_df.style.format(lambda x: f"{x:,.2f} billion"))

        # --- Sensitivity Analysis (Corrected) ---
        st.header("5. Sensitivity Analysis (EPS Accretion) 📈")
        
        # Define ranges for sensitivity analysis
        price_range = np.linspace(offer_price_per_share_base * 0.8, offer_price_per_share_base * 1.2, 5)
        synergy_range_million = np.linspace(synergy_value * 0.5, synergy_value * 2, 5)
        
        sensitivity_matrix = np.zeros((5, 5))
        
        for i, syn_m in enumerate(synergy_range_million):
            for j, price_base in enumerate(price_range):
                price_converted = price_base * conversion_rate
                pp = price_converted * target_data['Shares_Outstanding']
                sc = pp * stock_percent / 100
                si = sc / acquirer_share_price
                pf_shares = acquirer_data['Shares_Outstanding'] + si
                pf_ni = acquirer_data['Net_Income'] + target_data['Net_Income'] + (syn_m * 1000000 * (1-0.25))
                pf_eps = pf_ni / pf_shares
                accret_dilut = ((pf_eps - eps_acquirer) / eps_acquirer) * 100
                sensitivity_matrix[i, j] = accret_dilut
        
        sensitivity_df = pd.DataFrame(
            sensitivity_matrix,
            index=[f"{int(s)} M" for s in synergy_range_million],
            columns=[f"{p:.2f}" for p in price_range]
        )
        
        sensitivity_df.index.name = "Synergy Value"
        sensitivity_df.columns.name = "Offer Price per Share"
        
        st.table(sensitivity_df.style.format("{:.2f}%"))


        # --- LBO/MBO Analysis ---
        st.header("6. LBO & MBO Analysis 📈")
        st.sidebar.markdown("---")
        st.sidebar.subheader("LBO Assumptions")
        
        # LBO Inputs
        exit_multiple = st.sidebar.number_input("Exit Multiple (EV/EBITDA)", value=10.0, step=0.5)
        exit_year = st.sidebar.number_input("Exit Year (from now)", value=5, min_value=1, max_value=10)
        
        # Debt assumptions
        term_loan_percent = st.sidebar.slider("Term Loan % of Purchase Price", 0, 100, 50)
        revolver_percent = st.sidebar.slider("Revolver % of Purchase Price", 0, 100, 5)
        
        # Calculations for LBO
        purchase_price_lbo = target_data['Shares_Outstanding'] * offer_price_per_share_converted
        
        # Sources & Uses of Funds
        term_loan = purchase_price_lbo * term_loan_percent / 100
        revolver = purchase_price_lbo * revolver_percent / 100
        total_debt = term_loan + revolver
        sponsor_equity = purchase_price_lbo - total_debt
        
        st.subheader("Sources & Uses of Funds")
        sources = pd.DataFrame({
            'Category': ['Total Debt', 'Sponsor Equity'],
            'Value': [total_debt, sponsor_equity]
        }).set_index('Category')
        
        uses = pd.DataFrame({
            'Category': ['Purchase Price', 'Transaction Fees'],
            'Value': [purchase_price_lbo, purchase_price_lbo * 0.03] # Assume 3% transaction fees
        }).set_index('Category')
        
        st.markdown(f"**Total Sources:** `{selected_currency} {sources.sum().values[0]:,.2f}`")
        st.markdown(f"**Total Uses:** `{selected_currency} {uses.sum().values[0]:,.2f}`")

        # Create a Sources & Uses bar chart
        fig_lbo = go.Figure()
        fig_lbo.add_trace(go.Bar(
            name='Sources',
            x=['Total Debt', 'Sponsor Equity'],
            y=[total_debt, sponsor_equity],
            marker_color='skyblue'
        ))
        fig_lbo.add_trace(go.Bar(
            name='Uses',
            x=['Purchase Price', 'Transaction Fees'],
            y=[purchase_price_lbo, purchase_price_lbo * 0.03],
            marker_color='salmon'
        ))
        fig_lbo.update_layout(title_text="Sources & Uses of Funds", barmode='group')
        st.plotly_chart(fig_lbo)

        # LBO IRR & MOIC calculation
        ebitda_growth = 1.05 # 5% annual growth
        proj_ebitda = target_data['EBITDA'] * (ebitda_growth)**exit_year
        proj_exit_ev = proj_ebitda * exit_multiple
        
        # Simplified debt paydown
        # Assume a straight line paydown of term loan over exit_year
        debt_paydown = term_loan / exit_year
        proj_exit_debt = total_debt - debt_paydown * exit_year
        if proj_exit_debt < 0:
            proj_exit_debt = 0 # Cannot have negative debt

        proj_exit_equity = proj_exit_ev - proj_exit_debt
        
        # Calculate MOIC and IRR
        moic = proj_exit_equity / sponsor_equity if sponsor_equity > 0 else 0
        irr = npf.irr([-sponsor_equity] + [0]*(exit_year-1) + [proj_exit_equity])
        
        st.markdown("---")
        st.subheader("LBO Analysis Results")
        st.write(f"**Projected Exit Enterprise Value:** `{selected_currency} {proj_exit_ev:,.2f} billion`")
        st.write(f"**Projected Exit Equity Value:** `{selected_currency} {proj_exit_equity:,.2f} billion`")
        st.write(f"**Multiple on Invested Capital (MOIC):** `{moic:.2f}x`")
        st.write(f"**Internal Rate of Return (IRR):** `{irr:.2%}`")


        # --- Reporting Module ---
        st.markdown("---")
        st.header("7. Generate Professional Report 📄")
        report_text = f"""
# M&A Financial Analysis Report: {acquirer_name} & {target_name}

**Date:** {datetime.date.today().strftime('%B %d, %Y')}
**Display Currency:** {selected_currency}

---

## 1. Executive Summary

This report provides a comprehensive financial analysis of a potential merger between **{acquirer_name}** (Acquirer) and **{target_name}** (Target). The analysis includes valuation, deal structure, and the financial impact on the combined entity.

**Key Findings:**
- The transaction is **{ "ACCRETIVE" if accretion_dilution > 0 else "DILUTIVE" }** to the acquirer's EPS by **{accretion_dilution:.2f}%**. This indicates that the deal is expected to increase (or decrease) the earnings per share for the combined company.
- The estimated **goodwill created** on the pro forma balance sheet is **{selected_currency} {goodwill:,.2f} billion**. Goodwill represents the intangible assets arising from the acquisition, such as brand reputation or customer relationships.
- The valuation of the target company varies across methodologies:
    - **Discounted Cash Flow (DCF):** **{selected_currency} {dcf_value:,.2f} billion**
    - **Comparable Company Analysis (Comps):** **{selected_currency} {comps_value:,.2f} billion**
    - **Precedent Transaction Analysis:** **{selected_currency} {precedents_value:,.2f} billion**

---

## 2. Business Valuation (Target)

The valuation section provides a range of potential values for the target company using standard financial modeling techniques.

| Valuation Method | Value ({selected_currency} Billion) |
| :--- | :--- |
| Discounted Cash Flow (DCF) | {dcf_value:,.2f} |
| Comparable Company Analysis | {comps_value:,.2f} |
| Precedent Transaction Analysis | {precedents_value:,.2f} |

---

## 3. Financial Impact Analysis

This section analyzes the pro forma financial metrics of the combined entity.

| Metric | Acquirer ({selected_currency}) | Pro Forma ({selected_currency}) |
| :--- | :--- | :--- |
| EPS | {eps_acquirer:.2f} | {pro_forma_eps:.2f} |
| Total Assets (B) | {acquirer_data['Total_Assets']:,.2f} | {pro_forma_assets:,.2f} |
| Total Liabilities (B) | {acquirer_data['Total_Debt']:,.2f} | {pro_forma_liabilities:,.2f} |

---

## 4. Sensitivity Analysis (EPS Accretion)

This table shows how the transaction's impact on EPS changes based on different assumptions for synergy values and the offer price.

| Synergy Value ({selected_currency}M) | {price_range[0]:.2f} | {price_range[1]:.2f} | {price_range[2]:.2f} | {price_range[3]:.2f} | {price_range[4]:.2f} |
| :--- | :---: | :---: | :---: | :---: | :---: |
| {synergy_range_million[4]:.2f} | {sensitivity_matrix[4, 0]:.2f}% | {sensitivity_matrix[4, 1]:.2f}% | {sensitivity_matrix[4, 2]:.2f}% | {sensitivity_matrix[4, 3]:.2f}% | {sensitivity_matrix[4, 4]:.2f}% |
| {synergy_range_million[3]:.2f} | {sensitivity_matrix[3, 0]:.2f}% | {sensitivity_matrix[3, 1]:.2f}% | {sensitivity_matrix[3, 2]:.2f}% | {sensitivity_matrix[3, 3]:.2f}% | {sensitivity_matrix[3, 4]:.2f}% |
| {synergy_range_million[2]:.2f} | {sensitivity_matrix[2, 0]:.2f}% | {sensitivity_matrix[2, 1]:.2f}% | {sensitivity_matrix[2, 2]:.2f}% | {sensitivity_matrix[2, 3]:.2f}% | {sensitivity_matrix[2, 4]:.2f}% |
| {synergy_range_million[1]:.2f} | {sensitivity_matrix[1, 0]:.2f}% | {sensitivity_matrix[1, 1]:.2f}% | {sensitivity_matrix[1, 2]:.2f}% | {sensitivity_matrix[1, 3]:.2f}% | {sensitivity_matrix[1, 4]:.2f}% |
| {synergy_range_million[0]:.2f} | {sensitivity_matrix[0, 0]:.2f}% | {sensitivity_matrix[0, 1]:.2f}% | {sensitivity_matrix[0, 2]:.2f}% | {sensitivity_matrix[0, 3]:.2f}% | {sensitivity_matrix[0, 4]:.2f}% |

---

## 5. LBO Analysis

This analysis assesses the deal's viability from the perspective of a financial sponsor using a leveraged buyout (LBO) model.

| Metric | Value |
| :--- | :--- |
| Projected Exit EV | {selected_currency} {proj_exit_ev:,.2f} billion |
| Projected Exit Equity | {selected_currency} {proj_exit_equity:,.2f} billion |
| MOIC | {moic:.2f}x |
| IRR | {irr:.2%} |

---
This report is a powerful tool for analyzing a potential deal. Would you like to adjust any of the input values or explore the impact of different deal terms?
"""
    
        col_report1, col_report2, col_report3 = st.columns(3)
        with col_report1:
            st.download_button(
                label="Download Report as Text",
                data=report_text,
                file_name=f"M&A_Report_{acquirer_name}_vs_{target_name}.txt",
                mime="text/plain",
            )
        with col_report2:
            # Generate the PowerPoint report content
            ppt_content = f"""
Slide 1: Title Slide
    Title: M&A Financial Analysis Report
    Subtitle: {acquirer_name} & {target_name}

Slide 2: Executive Summary
    - The transaction is {"ACCRETIVE" if accretion_dilution > 0 else "DILUTIVE"} to the acquirer's EPS by {accretion_dilution:.2f}%.
    - The estimated goodwill created is {selected_currency} {goodwill:,.2f} billion.
    - Valuation:
        - DCF: {selected_currency} {dcf_value:,.2f}B
        - Comps: {selected_currency} {comps_value:,.2f}B
        - Precedents: {selected_currency} {precedents_value:,.2f}B

Slide 3: Deal Structure & Impact
    - Pro Forma EPS: {pro_forma_eps:.2f}
    - Total Assets: {selected_currency} {pro_forma_assets:,.2f}B
    - Total Liabilities: {selected_currency} {pro_forma_liabilities:,.2f}B
    - Goodwill: {selected_currency} {goodwill:,.2f}B

Slide 4: Sensitivity Analysis (EPS Accretion)
    - [Insert data table here]

Slide 5: LBO Analysis
    - MOIC: {moic:.2f}x
    - IRR: {irr:.2%}
            """
            
            # Use a button with an `on_click` handler that calls a function
            # and then uses JavaScript to perform the copy action.
            if st.button("Copy to Clipboard for PowerPoint"):
                # Use a small bit of HTML and JavaScript to copy the text.
                st.markdown(
                    f"""
                    <script>
                    copyTextToClipboard(`{ppt_content}`);
                    </script>
                    """,
                    unsafe_allow_html=True
                )
            
            st.button("Generate as PDF", help="This feature is not yet available but would generate a professional PDF document.")
            
else:
    st.info("Please provide company information via the simulated API or by uploading CSV or Excel files in the sidebar to run the analysis.")
