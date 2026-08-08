import streamlit as st
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
# PORTFOLIO INPUT (SESSION MEMORY)
# =========================================================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = "NVDA, AAPL, MSFT"

st.subheader("Your Stocks")

user_input = st.text_input(
    "Enter stock tickers (comma separated)",
    st.session_state.portfolio
)

# Save to session
st.session_state.portfolio = user_input

# Convert to list
portfolio = [
    t.strip().upper()
    for t in user_input.split(",")
    if t.strip()
]

# =========================================================
# REFRESH BUTTON
# =========================================================
if st.button("🔄 Refresh Analysis"):
    st.session_state.run_analysis = True

# Run once automatically on first load
if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = True

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
            # Pass portfolio into your existing engine
            generate_report(portfolio)
        except Exception as e:
            st.error(f"Error running analysis: {e}")
