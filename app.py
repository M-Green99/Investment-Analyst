import streamlit as st
from main import generate_report

# =========================================================
# PAGE
# =========================================================
st.set_page_config(layout="wide")
st.title("📊 Investment Analyst Dashboard")

# =========================================================
# SESSION
# =========================================================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = ["NVDA"]

# =========================================================
# INPUT
# =========================================================
user_input = st.text_input(
    "Enter stocks (comma separated)",
    value=", ".join(st.session_state.portfolio)
)

if st.button("Update Portfolio"):
    st.session_state.portfolio = [
        t.strip().upper()
        for t in user_input.split(",")
        if t.strip()
    ]

portfolio = st.session_state.portfolio

# =========================================================
# RUN ANALYSIS
# =========================================================
results = generate_report(portfolio)

# =========================================================
# SUMMARY SECTION
# =========================================================
st.subheader("📊 Summary")

if results:
    col1, col2, col3 = st.columns(3)

    best = max(results, key=lambda x: x["score"])
    highest_risk = max(results, key=lambda x: x["risk"])
    cheapest = min(results, key=lambda x: x["valuation"])

    col1.metric("Best Opportunity", best["ticker"], best["score"])
    col2.metric("Highest Risk", highest_risk["ticker"], highest_risk["risk"])
    col3.metric("Most Attractive Valuation", cheapest["ticker"], cheapest["valuation"])

# =========================================================
# STOCK CARDS
# =========================================================
st.subheader("📈 Stock Analysis")

for stock in results:

    st.markdown("---")

    # Header
    st.markdown(f"## {stock['ticker']}")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Price", stock["price"])
    col2.metric("Score", stock["score"])
    col3.metric("Growth %", f"{stock['growth']:.1f}")
    col4.metric("52W Position", f"{stock['pos']:.1f}%" if stock["pos"] else "N/A")

    # Second row
    col1, col2, col3 = st.columns(3)

    col1.metric("Valuation", stock["valuation"])
    col2.metric("Risk", stock["risk"])
    col3.metric("Analyst", stock["analyst"])

    # Action
    if stock["action"] == "BUY":
        st.success(f"BUY — {stock['reason']}")
    elif stock["action"] == "HOLD":
        st.warning(f"HOLD — {stock['reason']}")
    else:
        st.error(f"SELL — {stock['reason']}")

    # News
    st.markdown("### 📰 Recent News")

    if stock["news"]:
        for n in stock["news"]:
            st.markdown(f"**{n[0]}**")
            st.write(n[1])
    else:
        st.write("No recent news")

    # Events
    st.markdown("### 📅 Key Dates")

    if stock["events"]:
        for e in stock["events"]:
            st.write(f"{e[0]}: {e[1]}")
    else:
        st.write("No upcoming events")
