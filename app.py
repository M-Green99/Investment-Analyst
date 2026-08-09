import streamlit as st
import io
import sys
from main import generate_report

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Investment Analyst",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================
st.title("📊 Investment Analyst Dashboard")

# =========================================================
# SESSION STATE INIT
# =========================================================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = ["NVDA", "AAPL", "MSFT"]

if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = True

# =========================================================
# USER INPUT
# =========================================================
st.subheader("Your Stock List")

user_input = st.text_input(
    "Enter stock tickers (comma separated)",
    value=", ".join(st.session_state.portfolio)
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Update Portfolio"):
        st.session_state.portfolio = [
            t.strip().upper()
            for t in user_input.split(",")
            if t.strip()
        ]
        st.success("Portfolio updated")

with col2:
    if st.button("🔄 Refresh Analysis"):
        st.session_state.run_analysis = True

portfolio = st.session_state.portfolio

# =========================================================
# RUN ANALYSIS
# =========================================================
if st.session_state.run_analysis:

    st.write("---")
    st.subheader("Analysis Results")

    if not portfolio:
        st.warning("Please enter at least one stock.")
    else:
        try:
            # Capture print output from main.py
            buffer = io.StringIO()
            sys.stdout = buffer

            generate_report(portfolio)

            sys.stdout = sys.__stdout__

            st.text(buffer.getvalue())

        except Exception as e:
            sys.stdout = sys.__stdout__
            st.error(f"Error running analysis: {e}")
