import streamlit as st
from main import generate_report

# =========================================================

# PAGE CONFIGURATION

# =========================================================

st.set_page_config(
page_title="Investment Analyst",
page_icon="📊",
layout="wide",
initial_sidebar_state="expanded"
)

# =========================================================

# CUSTOM CSS

# =========================================================

st.markdown(
""" <style>

```
.main-title {
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.subtitle {
    color: #888888;
    margin-bottom: 1.5rem;
}

.stock-header {
    font-size: 1.7rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.small-label {
    color: #888888;
    font-size: 0.85rem;
}

.buy-box {
    padding: 14px;
    border-radius: 10px;
    background-color: rgba(0, 200, 83, 0.12);
    border: 1px solid rgba(0, 200, 83, 0.35);
    margin: 10px 0;
}

.hold-box {
    padding: 14px;
    border-radius: 10px;
    background-color: rgba(255, 165, 0, 0.12);
    border: 1px solid rgba(255, 165, 0, 0.40);
    margin: 10px 0;
}

.sell-box {
    padding: 14px;
    border-radius: 10px;
    background-color: rgba(244, 67, 54, 0.12);
    border: 1px solid rgba(244, 67, 54, 0.35);
    margin: 10px 0;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

</style>
""",
unsafe_allow_html=True
```

)

# =========================================================

# TITLE

# =========================================================

st.markdown(
'<div class="main-title">📊 Investment Analyst Dashboard</div>',
unsafe_allow_html=True
)

st.markdown(
'<div class="subtitle">Fundamental analysis, valuation, analysts, risk, catalysts and market data</div>',
unsafe_allow_html=True
)

# =========================================================

# SESSION STATE

# =========================================================

if "portfolio" not in st.session_state:
st.session_state.portfolio = ["NVDA"]

if "portfolio_input" not in st.session_state:
st.session_state.portfolio_input = ", ".join(
st.session_state.portfolio
)

# =========================================================

# SIDEBAR

# =========================================================

with st.sidebar:

```
st.header("📋 My Stocks")

st.caption(
    "Enter the stocks you want the analyst to monitor."
)

portfolio_input = st.text_input(
    "Stock tickers",
    value=st.session_state.portfolio_input,
    key="portfolio_input",
    placeholder="NVDA, MSFT, CCJ, GOOGL"
)

update_clicked = st.button(
    "🔄 Update Stock List",
    use_container_width=True
)

if update_clicked:

    new_portfolio = [
        ticker.strip().upper()
        for ticker in portfolio_input.split(",")
        if ticker.strip()
    ]

    # Remove duplicates while keeping order
    new_portfolio = list(dict.fromkeys(new_portfolio))

    if new_portfolio:
        st.session_state.portfolio = new_portfolio
        st.session_state.portfolio_input = ", ".join(
            new_portfolio
        )
        st.success("Stock list updated.")
    else:
        st.warning("Please enter at least one ticker.")

st.divider()

st.write("**Current list:**")

for ticker in st.session_state.portfolio:
    st.write(f"• {ticker}")

st.divider()

refresh_clicked = st.button(
    "🔄 Refresh Analysis",
    use_container_width=True
)
```

# =========================================================

# CURRENT PORTFOLIO

# =========================================================

portfolio = st.session_state.portfolio

if not portfolio:
st.warning("No stocks selected.")
st.stop()

# =========================================================

# RUN ANALYSIS

# =========================================================

with st.spinner(
f"Analysing {len(portfolio)} stock"
+ ("..." if len(portfolio) == 1 else "s...")
):

```
try:
    results = generate_report(portfolio)

except Exception as e:
    st.error(
        f"Error running analysis: {e}"
    )
    st.stop()
```

# =========================================================

# NO RESULTS

# =========================================================

if not results:

```
st.error(
    "No stocks could be analysed. "
    "Check the ticker symbols and try again."
)

st.stop()
```

# =========================================================

# HELPER FUNCTIONS

# =========================================================

def get_value(dictionary, *keys, default=None):

```
current = dictionary

for key in keys:

    if not isinstance(current, dict):
        return default

    current = current.get(key)

    if current is None:
        return default

return current
```

def format_number(value, decimals=2):

```
if value is None:
    return "N/A"

try:
    return f"{float(value):,.{decimals}f}"
except Exception:
    return str(value)
```

def format_percent(value, decimals=1):

```
if value is None:
    return "N/A"

try:
    return f"{float(value):.{decimals}f}%"
except Exception:
    return str(value)
```

def format_large_number(value):

```
if value is None:
    return "N/A"

try:

    value = float(value)

    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"

    return f"{value:,.0f}"

except Exception:
    return str(value)
```

def action_colour(action):

```
if action == "BUY":
    return "green"

if action == "HOLD":
    return "orange"

if action == "SELL":
    return "red"

return "gray"
```

def display_action(action, reason):

```
if action == "BUY":

    st.success(
        f"🟢 BUY\n\n{reason}"
    )

elif action == "HOLD":

    st.warning(
        f"🟠 HOLD\n\n{reason}"
    )

elif action == "SELL":

    st.error(
        f"🔴 SELL\n\n{reason}"
    )

else:

    st.info(
        f"{action}\n\n{reason}"
    )
```

# =========================================================

# SUMMARY

# =========================================================

st.header("📊 Portfolio Summary")

# ---------------------------------------------------------

# Summary calculations

# ---------------------------------------------------------

best = max(
results,
key=lambda x: get_value(
x,
"score",
default=0
) or 0
)

# Risk ranking

risk_order = {
"LOW": 1,
"MODERATE": 2,
"HIGH": 3,
"VERY HIGH": 4
}

highest_risk = max(
results,
key=lambda x: risk_order.get(
x.get("risk", "LOW"),
0
)
)

# Attractive valuation first

attractive = [
item
for item in results
if item.get("valuation") == "ATTRACTIVE"
]

if attractive:

```
most_attractive = max(
    attractive,
    key=lambda x: x.get("score", 0)
)
```

else:

```
most_attractive = min(
    results,
    key=lambda x: x.get("score", 0)
)
```

# ---------------------------------------------------------

# Summary metrics

# ---------------------------------------------------------

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:

```
st.metric(
    "🏆 Best Opportunity",
    best.get("ticker", "N/A"),
    f"Score {best.get('score', 'N/A')}"
)
```

with summary_col2:

```
st.metric(
    "⚠️ Highest Risk",
    highest_risk.get("ticker", "N/A"),
    highest_risk.get("risk", "N/A")
)
```

with summary_col3:

```
st.metric(
    "💰 Best Valuation",
    most_attractive.get("ticker", "N/A"),
    most_attractive.get("valuation", "N/A")
)
```

# =========================================================

# ACTION SUMMARY

# =========================================================

st.subheader("🎯 Investment Actions")

for item in results:

```
ticker = item.get("ticker", "N/A")
action = item.get("action", "N/A")
reason = item.get("reason", "No explanation available.")
score = item.get("score", "N/A")

if action == "BUY":

    st.success(
        f"🟢 **{ticker} — BUY** | Score: {score}\n\n"
        f"{reason}"
    )

elif action == "HOLD":

    st.warning(
        f"🟠 **{ticker} — HOLD** | Score: {score}\n\n"
        f"{reason}"
    )

elif action == "SELL":

    st.error(
        f"🔴 **{ticker} — SELL** | Score: {score}\n\n"
        f"{reason}"
    )

else:

    st.info(
        f"**{ticker} — {action}** | Score: {score}\n\n"
        f"{reason}"
    )
```

# =========================================================

# STOCK ANALYSIS

# =========================================================

st.header("📈 Stock Analysis")

for item in results:

```
ticker = item.get("ticker", "N/A")
name = item.get("name", ticker)
sector = item.get("sector", "N/A")

score = item.get("score", 0)
action = item.get("action", "N/A")
reason = item.get(
    "reason",
    "No explanation available."
)

model = item.get("model", {})
market_data = item.get("market_data", {})
valuation_data = item.get("valuation_data", {})
fundamentals = item.get("fundamentals", {})
analyst_data = item.get("analyst_data", {})
earnings = item.get("earnings", {})
news = item.get("news", [])
events = item.get("events", [])

growth = model.get("growth")
quality = model.get("quality")
quality_score = model.get("quality_score")
verdict = model.get("verdict")
catalyst_strength = model.get(
    "catalyst_strength"
)

risk = item.get("risk")

# -----------------------------------------------------
# STOCK HEADER
# -----------------------------------------------------

st.markdown("---")

st.markdown(
    f"## {ticker} — {name}"
)

if sector and sector != "N/A":

    st.caption(
        f"Sector: {sector}"
    )

# -----------------------------------------------------
# ACTION
# -----------------------------------------------------

display_action(
    action,
    reason
)

# -----------------------------------------------------
# TOP METRICS
# -----------------------------------------------------

metric1, metric2, metric3, metric4 = st.columns(4)

current_price = (
    market_data.get("current_price")
    or market_data.get("price")
    or item.get("price")
)

market_cap = (
    market_data.get("market_cap")
    or item.get("market_cap")
)

fifty_two_week_position = (
    market_data.get(
        "fifty_two_week_position"
    )
    or market_data.get(
        "52_week_position"
    )
    or item.get("pos")
)

with metric1:

    st.metric(
        "Current Price",
        format_number(current_price)
    )

with metric2:

    st.metric(
        "Model Score",
        f"{score}/100"
    )

with metric3:

    st.metric(
        "Growth",
        format_percent(growth)
    )

with metric4:

    if fifty_two_week_position is not None:

        st.metric(
            "52-Week Position",
            format_percent(
                fifty_two_week_position
            )
            if float(
                fifty_two_week_position
            ) <= 1
            else format_percent(
                fifty_two_week_position
            )
        )

    else:

        st.metric(
            "52-Week Position",
            "N/A"
        )

# -----------------------------------------------------
# DETAILED SECTIONS
# -----------------------------------------------------

with st.expander(
    "📊 Market Data",
    expanded=False
):

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Current Price",
            format_number(current_price)
        )

    with col2:

        st.metric(
            "Market Cap",
            format_large_number(market_cap)
        )

    with col3:

        st.metric(
            "52-Week Position",
            format_percent(
                fifty_two_week_position
            )
        )

    high_52 = (
        market_data.get(
            "fifty_two_week_high"
        )
        or market_data.get(
            "52_week_high"
        )
    )

    low_52 = (
        market_data.get(
            "fifty_two_week_low"
        )
        or market_data.get(
            "52_week_low"
        )
    )

    if high_52 is not None or low_52 is not None:

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**52-Week High:** "
                f"{format_number(high_52)}"
            )

        with col2:

            st.write(
                f"**52-Week Low:** "
                f"{format_number(low_52)}"
            )

    beta = (
        market_data.get("beta")
        or item.get("beta")
    )

    if beta is not None:

        st.write(
            f"**Beta:** {format_number(beta)}"
        )

# -----------------------------------------------------
# BUSINESS QUALITY / FUNDAMENTALS
# -----------------------------------------------------

with st.expander(
    "🏢 Business & Fundamentals",
    expanded=False
):

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            f"**Business Quality:** "
            f"{quality or 'N/A'}"
        )

        if quality_score is not None:

            st.write(
                f"**Quality Score:** "
                f"{quality_score}"
            )

    with col2:

        st.write(
            f"**Growth:** "
            f"{format_percent(growth)}"
        )

    with col3:

        if fundamentals:

            for key, value in fundamentals.items():

                label = (
                    str(key)
                    .replace("_", " ")
                    .title()
                )

                if isinstance(
                    value,
                    (int, float)
                ):

                    st.write(
                        f"**{label}:** "
                        f"{format_number(value)}"
                    )

                else:

                    st.write(
                        f"**{label}:** "
                        f"{value}"
                    )

        else:

            st.write(
                "No additional fundamental "
                "data available."
            )

# -----------------------------------------------------
# VALUATION
# -----------------------------------------------------

with st.expander(
    "💰 Valuation",
    expanded=False
):

    valuation_label = item.get(
        "valuation",
        valuation_data.get(
            "assessment",
            "N/A"
        )
    )

    if valuation_label == "ATTRACTIVE":

        st.success(
            f"Valuation: **{valuation_label}**"
        )

    elif valuation_label == "EXPENSIVE":

        st.error(
            f"Valuation: **{valuation_label}**"
        )

    else:

        st.warning(
            f"Valuation: **{valuation_label}**"
        )

    if valuation_data:

        for key, value in valuation_data.items():

            label = (
                str(key)
                .replace("_", " ")
                .title()
            )

            if isinstance(
                value,
                (int, float)
            ):

                st.write(
                    f"**{label}:** "
                    f"{format_number(value)}"
                )

            else:

                st.write(
                    f"**{label}:** "
                    f"{value}"
                )

# -----------------------------------------------------
# ANALYST CONSENSUS
# -----------------------------------------------------

with st.expander(
    "🏦 Analyst Consensus",
    expanded=False
):

    consensus = (
        item.get("analyst_consensus")
        or analyst_data.get("consensus")
        or analyst_data.get("recommendation")
    )

    if consensus is None:

        consensus = "N/A"

    if consensus in (
        "BUY",
        "STRONG BUY"
    ):

        st.success(
            f"Analyst Consensus: **{consensus}**"
        )

    elif consensus == "HOLD":

        st.warning(
            f"Analyst Consensus: **{consensus}**"
        )

    elif consensus in (
        "SELL",
        "STRONG SELL"
    ):

        st.error(
            f"Analyst Consensus: **{consensus}**"
        )

    else:

        st.info(
            f"Analyst Consensus: **{consensus}**"
        )

    if analyst_data:

        for key, value in analyst_data.items():

            label = (
                str(key)
                .replace("_", " ")
                .title()
            )

            if isinstance(
                value,
                (int, float)
            ):

                st.write(
                    f"**{label}:** "
                    f"{format_number(value)}"
                )

            else:

                st.write(
                    f"**{label}:** "
                    f"{value}"
                )

# -----------------------------------------------------
# EARNINGS
# -----------------------------------------------------

with st.expander(
    "📅 Earnings",
    expanded=False
):

    if earnings:

        for key, value in earnings.items():

            label = (
                str(key)
                .replace("_", " ")
                .title()
            )

            st.write(
                f"**{label}:** {value}"
            )

    else:

        st.write(
            "No earnings information available."
        )

# -----------------------------------------------------
# RISK
# -----------------------------------------------------

with st.expander(
    "⚠️ Risk",
    expanded=False
):

    if risk == "VERY HIGH":

        st.error(
            f"Risk Assessment: **{risk}**"
        )

    elif risk == "HIGH":

        st.error(
            f"Risk Assessment: **{risk}**"
        )

    elif risk == "MODERATE":

        st.warning(
            f"Risk Assessment: **{risk}**"
        )

    else:

        st.success(
            f"Risk Assessment: **{risk or 'N/A'}**"
        )

# -----------------------------------------------------
# CATALYSTS
# -----------------------------------------------------

with st.expander(
    "🚀 Catalysts",
    expanded=False
):

    if catalyst_strength == "STRONG":

        st.success(
            f"Catalyst Strength: "
            f"**{catalyst_strength}**"
        )

    elif catalyst_strength == "MODERATE":

        st.warning(
            f"Catalyst Strength: "
            f"**{catalyst_strength}**"
        )

    else:

        st.info(
            f"Catalyst Strength: "
            f"**{catalyst_strength or 'N/A'}**"
        )

# -----------------------------------------------------
# NEWS
# -----------------------------------------------------

with st.expander(
    "📰 Recent News",
    expanded=False
):

    if news:

        for index, article in enumerate(
            news,
            start=1
        ):

            if isinstance(
                article,
                dict
            ):

                title = article.get(
                    "title",
                    "No title"
                )

                summary = article.get(
                    "summary",
                    ""
                )

                sentiment = article.get(
                    "sentiment",
                    "NEUTRAL"
                )

                st.markdown(
                    f"**{index}. {title}**"
                )

                if summary:

                    st.write(
                        summary
                    )

                st.caption(
                    f"Sentiment: {sentiment}"
                )

            elif isinstance(
                article,
                (list, tuple)
            ):

                if len(article) >= 1:

                    st.markdown(
                        f"**{index}. "
                        f"{article[0]}**"
                    )

                if len(article) >= 2:

                    st.write(
                        article[1]
                    )

                if len(article) >= 3:

                    st.caption(
                        f"Sentiment: "
                        f"{article[2]}"
                    )

            else:

                st.write(
                    str(article)
                )

    else:

        st.write(
            "No recent news available."
        )

# -----------------------------------------------------
# KEY DATES
# -----------------------------------------------------

with st.expander(
    "📆 Key Dates",
    expanded=False
):

    if events:

        for event in events:

            if isinstance(
                event,
                dict
            ):

                event_type = event.get(
                    "type",
                    "EVENT"
                )

                event_date = event.get(
                    "date",
                    "N/A"
                )

                st.write(
                    f"**{event_type}:** "
                    f"{event_date}"
                )

            elif isinstance(
                event,
                (list, tuple)
            ):

                if len(event) >= 2:

                    st.write(
                        f"**{event[0]}:** "
                        f"{event[1]}"
                    )

                else:

                    st.write(
                        str(event)
                    )

            else:

                st.write(
                    str(event)
                )

    else:

        st.write(
            "No upcoming key dates found."
        )
```

# =========================================================

# FOOTER

# =========================================================

st.divider()

st.caption(
"Investment Analyst Dashboard • "
"Data supplied by market-data sources • "
"For research purposes only"
)
