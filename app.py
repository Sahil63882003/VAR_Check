import streamlit as st
import pandas as pd
import numpy as np
import base64
import time

# Function to process the data and calculate VaR
def calculate_var(df, nfo_strike, bfo_strike, allocation):
    splits = df["Symbol"].str.split()
    df["Strike"] = splits.str[-1]
    df["Transaction"] = splits.str[-2]

    df_nfo = df[df["Exchange"] == "NFO"].copy()
    df_bfo = df[df["Exchange"] == "BFO"].copy()

    nfo_results = {}
    if not df_nfo.empty:
        strike_nfo = df_nfo["Strike"].astype(float)
        qty_nfo = df_nfo["Net Qty"]
        is_ce_nfo = df_nfo["Transaction"] == "CE"
        netpos_pos_nfo = qty_nfo > 0
        netpos_neg_nfo = qty_nfo < 0

        for perc in [10, -10, 15, -15]:
            calc_nfo = nfo_strike + (nfo_strike * perc / 100)
            colname = f"calc_{perc}%_VAR"
            if perc > 0:
                df_nfo[colname] = np.where(
                    netpos_pos_nfo & is_ce_nfo, (calc_nfo - strike_nfo) * abs(qty_nfo),
                    np.where(netpos_neg_nfo & is_ce_nfo, (calc_nfo - strike_nfo) * qty_nfo,
                    np.where(netpos_neg_nfo & ~is_ce_nfo, abs(df_nfo["Sell Avg Price"] * qty_nfo), 0))
                )
            else:
                df_nfo[colname] = np.where(
                    netpos_pos_nfo & ~is_ce_nfo, (strike_nfo - calc_nfo) * qty_nfo,
                    np.where(netpos_neg_nfo & is_ce_nfo, abs(df_nfo["Sell Avg Price"] * qty_nfo),
                    np.where(netpos_neg_nfo & ~is_ce_nfo, (calc_nfo - strike_nfo) * abs(qty_nfo), 0))
                )
            sum_var = df_nfo[colname].sum()
            perc_var = sum_var / allocation if allocation != 0 else 0
            nfo_results[perc] = (sum_var, perc_var)
    else:
        nfo_results = {perc: (0, 0) for perc in [10, -10, 15, -15]}

    bfo_results = {}
    if not df_bfo.empty:
        strike_bfo = df_bfo["Strike"].astype(float)
        qty_bfo = df_bfo["Net Qty"]
        is_ce_bfo = df_bfo["Transaction"] == "CE"
        netpos_pos_bfo = qty_bfo > 0
        netpos_neg_bfo = qty_bfo < 0

        for perc in [10, -10, 15, -15]:
            calc_bfo = bfo_strike + (bfo_strike * perc / 100)
            colname = f"calc_{perc}%_VAR"
            if perc > 0:
                df_bfo[colname] = np.where(
                    netpos_pos_bfo & is_ce_bfo, (calc_bfo - strike_bfo) * abs(qty_bfo),
                    np.where(netpos_neg_bfo & is_ce_bfo, (calc_bfo - strike_bfo) * qty_bfo,
                    np.where(netpos_neg_bfo & ~is_ce_bfo, abs(df_bfo["Sell Avg Price"] * qty_bfo), 0))
                )
            else:
                df_bfo[colname] = np.where(
                    netpos_pos_bfo & ~is_ce_bfo, (strike_bfo - calc_bfo) * qty_bfo,
                    np.where(netpos_neg_bfo & is_ce_bfo, abs(df_bfo["Sell Avg Price"] * qty_bfo),
                    np.where(netpos_neg_bfo & ~is_ce_bfo, (calc_bfo - strike_bfo) * abs(qty_bfo), 0))
                )
            sum_var = df_bfo[colname].sum()
            perc_var = sum_var / allocation if allocation != 0 else 0
            bfo_results[perc] = (sum_var, perc_var)
    else:
        bfo_results = {perc: (0, 0) for perc in [10, -10, 15, -15]}

    return nfo_results, bfo_results, df_nfo, df_bfo

# Streamlit App Configuration
st.set_page_config(page_title="VaR Calculator Pro", page_icon="📈", layout="wide")

# Custom CSS with Tailwind, Light/Dark Mode, and Improved Responsiveness
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-light: #F9FAFB;
            --bg-dark: #111827;
            --text-light: #1F2937;
            --text-dark: #F9FAFB;
            --card-bg-light: #FFFFFF;
            --card-bg-dark: #1F2937;
            --accent: #3B82F6;
            --accent-hover: #2563EB;
            --border-light: #E5E7EB;
            --border-dark: #374151;
            --shadow-light: rgba(0, 0, 0, 0.05);
            --shadow-dark: rgba(0, 0, 0, 0.3);
        }
        body {
            font-family: 'Inter', sans-serif;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        .light-mode {
            background: var(--bg-light);
            color: var(--text-light);
        }
        .dark-mode {
            background: var(--bg-dark);
            color: var(--text-dark);
        }
        .stApp {
            background: inherit;
            color: inherit;
        }
        .sidebar .sidebar-content {
            background: var(--card-bg-light);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 4px 8px var(--shadow-light);
        }
        .dark-mode .sidebar .sidebar-content {
            background: var(--card-bg-dark);
            box-shadow: 0 4px 8px var(--shadow-dark);
        }
        .stButton > button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 6px var(--shadow-light);
        }
        .dark-mode .stButton > button:hover {
            box-shadow: 0 4px 6px var(--shadow-dark);
        }
        .metric-card {
            border-radius: 0.75rem;
            padding: 1rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .header {
            font-size: 2.25rem;
            font-weight: 800;
            background: linear-gradient(to right, var(--accent), #6366F1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subheader {
            font-size: 1.125rem;
            color: #4B5563;
        }
        .dark-mode .subheader {
            color: #9CA3AF;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        .download-button {
            background: var(--accent);
            color: white !important;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            text-decoration: none;
            transition: background 0.3s ease;
        }
        .download-button:hover {
            background: var(--accent-hover);
        }
        @media (max-width: 640px) {
            .header {
                font-size: 1.875rem;
            }
            .st-columns > div {
                margin-bottom: 1rem;
            }
        }
    </style>
    <script>
        function applyTheme(theme) {
            const body = document.body;
            body.classList.remove('light-mode', 'dark-mode');
            body.classList.add(theme + '-mode');
            localStorage.setItem('theme', theme);
        }
        function toggleTheme() {
            const currentTheme = localStorage.getItem('theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            applyTheme(newTheme);
        }
        document.addEventListener('DOMContentLoaded', () => {
            const savedTheme = localStorage.getItem('theme');
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            applyTheme(savedTheme || systemTheme);
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                if (!localStorage.getItem('theme')) {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        });
    </script>
""", unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/calculator.png", use_column_width=True)
    st.markdown('<h1 class="text-xl font-bold mb-2">VaR Calculator Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="text-sm text-gray-600 dark:text-gray-400">Upload positions CSV and set parameters to compute Value at Risk (VaR).</p>', unsafe_allow_html=True)

    # Theme toggle with label
    theme_toggle = st.checkbox("Dark Mode", value=False, on_change=None)
    if theme_toggle:
        st.markdown('<script>applyTheme("dark");</script>', unsafe_allow_html=True)
    else:
        st.markdown('<script>applyTheme("light");</script>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload POS (2).csv", type=["csv"], help="Upload your positions file in CSV format. Ensure it has columns like Symbol, Exchange, Net Qty, Sell Avg Price.")

    nfo_strike = st.number_input("Nifty Strike Price", min_value=0, value=24600, step=100, help="Current strike price for Nifty (NFO). Must be positive.")
    bfo_strike = st.number_input("Sensex Strike Price", min_value=0, value=80200, step=100, help="Current strike price for Sensex (BFO). Must be positive.")
    allocation = st.number_input("Allocation Amount", min_value=0, value=50000000, step=1000000, help="Total allocation amount. Used for percentage calculations.")

    if st.button("Calculate VaR", help="Click to process the uploaded file and calculate VaR."):
        if uploaded_file is None:
            st.error("Please upload a CSV file to proceed.")
        elif allocation <= 0:
            st.error("Allocation amount must be greater than zero.")
        elif nfo_strike <= 0 or bfo_strike <= 0:
            st.error("Strike prices must be positive.")
        else:
            with st.spinner("Analyzing positions and calculating VaR..."):
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.005)
                    progress_bar.progress((i + 1) / 100)
                df = pd.read_csv(uploaded_file)
                if "Symbol" not in df.columns or "Exchange" not in df.columns or "Net Qty" not in df.columns or "Sell Avg Price" not in df.columns:
                    st.error("Uploaded CSV is missing required columns: Symbol, Exchange, Net Qty, Sell Avg Price.")
                else:
                    nfo_results, bfo_results, df_nfo, df_bfo = calculate_var(df, nfo_strike, bfo_strike, allocation)
                    st.session_state['nfo_results'] = nfo_results
                    st.session_state['bfo_results'] = bfo_results
                    st.session_state['df_nfo'] = df_nfo
                    st.session_state['df_bfo'] = df_bfo
                    st.success("VaR calculation completed successfully! Results are ready below.")

# Main content
st.markdown('<h1 class="header fade-in">Value at Risk (VaR) Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader fade-in">Interactive dashboard for Nifty and Sensex VaR analysis. View metrics and download detailed data.</p>', unsafe_allow_html=True)

if 'nfo_results' in st.session_state:
    # NFO Section
    st.markdown('<h2 class="text-lg font-semibold mt-6 mb-3 fade-in">Nifty (NFO) VaR Results</h2>', unsafe_allow_html=True)
    cols = st.columns(4)
    percs = [10, -10, 15, -15]
    for idx, perc in enumerate(percs):
        sum_var, perc_var = st.session_state['nfo_results'][perc]
        with cols[idx]:
            st.metric(
                label=f"VaR at {perc}%",
                value=f"₹{sum_var:,.2f}",
                delta=f"{perc_var:.4%}",
                delta_color="inverse" if perc < 0 else "normal"
            )

    # BFO Section
    st.markdown('<h2 class="text-lg font-semibold mt-6 mb-3 fade-in">Sensex (BFO) VaR Results</h2>', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, perc in enumerate(percs):
        sum_var, perc_var = st.session_state['bfo_results'][perc]
        with cols[idx]:
            st.metric(
                label=f"VaR at {perc}%",
                value=f"₹{sum_var:,.2f}",
                delta=f"{perc_var:.4%}",
                delta_color="inverse" if perc < 0 else "normal"
            )

    # Detailed Data Download
    st.markdown('<h3 class="text-md font-medium mt-6 mb-3 fade-in">Download Detailed Processed Data</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download NFO Processed CSV",
            data=st.session_state['df_nfo'].to_csv(index=False),
            file_name="nfo_processed.csv",
            mime="text/csv",
            help="Download the processed NFO data with VaR calculations."
        )
    with col2:
        st.download_button(
            label="Download BFO Processed CSV",
            data=st.session_state['df_bfo'].to_csv(index=False),
            file_name="bfo_processed.csv",
            mime="text/csv",
            help="Download the processed BFO data with VaR calculations."
        )

    # Expander for Raw Data Preview
    with st.expander("Preview Processed Data", expanded=False):
        st.subheader("NFO Data Preview")
        st.dataframe(st.session_state['df_nfo'].head(10), use_container_width=True)
        st.subheader("BFO Data Preview")
        st.dataframe(st.session_state['df_bfo'].head(10), use_container_width=True)

else:
    st.info("Upload a CSV file in the sidebar and click 'Calculate VaR' to generate results. Ensure the file is correctly formatted for accurate calculations.")

# Footer
st.markdown("""
    <div class="mt-8 py-3 text-center text-sm text-gray-500 dark:text-gray-400 fade-in">
        Powered by Streamlit | Optimized for Financial Risk Analysis | © 2025
    </div>
""", unsafe_allow_html=True)