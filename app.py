import streamlit as st
import yfinance as yf
from portfolio import portfolio
from datetime import date, datetime

# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Investment Analyst",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# COLOUR / DISPLAY HELPERS
# =========================================================

def action_colour(action):
    if action == "BUY":
        return "🟢"
    elif action == "HOLD":
        return "🟠"
    return "🔴"


def sentiment_colour(sentiment):
    if sentiment == "POSITIVE":
        return "🟢"
    elif sentiment == "NEGATIVE":
        return "🔴"
    return "🟠"


def risk_colour(risk):
    if risk == "LOW":
        return "🟢"
    elif risk == "MODERATE":
        return "🟠"
    return "🔴"


def valuation_colour(valuation):
    if valuation == "ATTRACTIVE":
        return "🟢"
    elif valuation == "EXPENSIVE":
        return "🔴"
    return "🟠"


# =========================================================
# NEWS SENTIMENT
# =========================================================

def get_news_sentiment(title):

    if not title:
        return "NEUTRAL"

    text = title.lower()

    positive_words = [
        "growth", "profit", "profits", "beats", "beat",
        "upgrade", "surge", "record", "strong", "raises",
        "raised", "positive", "contract", "deal",
        "partnership", "launch", "expands", "expansion",
        "orders", "approval", "approved", "breakthrough",
        "bullish"
    ]

    negative_words = [
        "loss", "losses", "miss", "misses", "downgrade",
        "fall", "falls", "drop", "drops", "weak",
        "warning", "cuts", "cut", "decline", "declines",
        "lawsuit", "investigation", "delay", "delays",
        "debt", "concern", "concerns", "bearish", "risk"
    ]

    positive_score = sum(1 for word in positive_words if word in text)
    negative_score = sum(1 for word in negative_words if word in text)

    if positive_score > negative_score:
        return "POSITIVE"

    if negative_score > positive_score:
        return "NEGATIVE"

    return "NEUTRAL"


# =========================================================
# NEWS SUMMARY
# =========================================================

def create_news_summary(title):

    if not title:
        return "No summary available."

    title = title.strip()

    if len(title) > 180:
        title = title[:177] + "..."

    return title


# =========================================================
# ANALYST CONSENSUS
# =========================================================

def get_analyst_consensus(info):

    recommendation = info.get("recommendationKey")

    if not recommendation:
        return "N/A"

    recommendation = str(recommendation).lower()

    mapping = {
        "strong_buy": "STRONG BUY",
        "strong buy": "STRONG BUY",
        "buy": "BUY",
        "outperform": "BUY",
        "hold": "HOLD",
        "neutral": "HOLD",
        "market perform": "HOLD",
        "sell": "SELL",
        "underperform": "SELL",
        "strong_sell": "STRONG SELL",
        "strong sell": "STRONG SELL"
    }

    return mapping.get(
        recommendation,
        recommendation.upper()
    )


def get_analyst_text(info):

    consensus = get_analyst_consensus(info)

    if consensus in ["STRONG BUY", "BUY"]:
        return "positive analyst consensus"

    if consensus == "HOLD":
        return "neutral analyst consensus"

    if consensus in ["SELL", "STRONG SELL"]:
        return "negative analyst consensus"

    return None


# =========================================================
# VALUATION
# =========================================================

def get_valuation(info):

    forward_pe = info.get("forwardPE")
    trailing_pe = info.get("trailingPE")
    peg = info.get("pegRatio")

    if peg is not None:
        try:
            if peg < 1:
                return "ATTRACTIVE"
            elif peg > 2:
                return "EXPENSIVE"
        except Exception:
            pass

    pe = forward_pe or trailing_pe

    if pe is not None:
        try:
            if pe < 20:
                return "ATTRACTIVE"
            elif pe > 40:
                return "EXPENSIVE"
        except Exception:
            pass

    return "FAIR"


# =========================================================
# BUSINESS QUALITY
# =========================================================

def get_business_quality(info):

    roe = info.get("returnOnEquity")
    profit_margin = info.get("profitMargins")
    operating_margin = info.get("operatingMargins")

    score = 0

    if roe is not None:
        try:
            if roe >= 0.20:
                score += 2
            elif roe >= 0.10:
                score += 1
        except Exception:
            pass

    if profit_margin is not None:
        try:
            if profit_margin >= 0.15:
                score += 2
            elif profit_margin > 0:
                score += 1
        except Exception:
            pass

    if operating_margin is not None:
        try:
            if operating_margin >= 0.15:
                score += 2
            elif operating_margin > 0:
                score += 1
        except Exception:
            pass

    if score >= 5:
        quality = "EXCELLENT"
    elif score >= 3:
        quality = "STRONG"
    elif score >= 1:
        quality = "WEAK"
    else:
        quality = "POOR"

    return quality, score


# =========================================================
# GROWTH
# =========================================================

def get_growth(info):

    revenue_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")

    values = []

    for value in [revenue_growth, earnings_growth]:
        if value is not None:
            try:
                values.append(float(value))
            except Exception:
                pass

    if not values:
        return 0

    return sum(values) / len(values) * 100


# =========================================================
# RISK
# =========================================================

def get_risk(info, growth):

    beta = info.get("beta")
    profit_margin = info.get("profitMargins")
    debt_to_equity = info.get("debtToEquity")

    risk_score = 0

    if beta is not None:
        try:
            if beta >= 2:
                risk_score += 3
            elif beta >= 1.4:
                risk_score += 2
            elif beta >= 1:
                risk_score += 1
        except Exception:
            pass

    if debt_to_equity is not None:
        try:
            if debt_to_equity >= 150:
                risk_score += 2
            elif debt_to_equity >= 80:
                risk_score += 1
        except Exception:
            pass

    if profit_margin is not None:
        try:
            if profit_margin < 0:
                risk_score += 2
        except Exception:
            pass

    if growth < 0:
        risk_score += 1

    if risk_score >= 5:
        return "VERY HIGH"

    elif risk_score >= 3:
        return "HIGH"

    elif risk_score >= 1:
        return "MODERATE"

    return "LOW"


# =========================================================
# CATALYSTS
# =========================================================

def get_catalyst_strength(info):

    score = 0

    earnings_date = info.get("earningsTimestamp")

    if earnings_date:
        score += 1

    recommendation = info.get("recommendationKey")

    if recommendation in ["strong_buy", "buy"]:
        score += 1

    if score >= 2:
        return "STRONG"

    elif score == 1:
        return "MODERATE"

    return "WEAK"


# =========================================================
# EVENTS
# =========================================================

def get_events(stock, info):

    events = []

    earnings = info.get("earningsTimestamp")

    if earnings:
        try:
            event_date = datetime.fromtimestamp(
                earnings
            ).date()

            events.append({
                "date": event_date,
                "type": "EARNINGS",
                "priority": 1
            })

        except Exception:
            pass

    ex_dividend = info.get("exDividendDate")

    if ex_dividend:
        try:
            event_date = datetime.fromtimestamp(
                ex_dividend
            ).date()

            events.append({
                "date": event_date,
                "type": "DIVIDEND",
                "priority": 3
            })

        except Exception:
            pass

    try:

        calendar = stock.calendar

        if calendar is not None and hasattr(calendar, "to_dict"):

            calendar_data = calendar.to_dict()

            earnings_dates = calendar_data.get(
                "Earnings Date"
            )

            if earnings_dates:

                for event_date in earnings_dates:

                    if hasattr(event_date, "date"):
                        event_date = event_date.date()

                    if isinstance(event_date, date):

                        events.append({
                            "date": event_date,
                            "type": "EARNINGS",
                            "priority": 1
                        })

    except Exception:
        pass

    unique = []
    seen = set()

    for event in events:

        key = (
            event["date"],
            event["type"]
        )

        if key not in seen:

            seen.add(key)
            unique.append(event)

    return unique


# =========================================================
# SCORING
# =========================================================

def calculate_score(
    info,
    valuation,
    quality,
    quality_score,
    growth,
    analyst_consensus,
    risk,
    catalyst_strength,
    news_sentiment
):

    score = 50

    if quality == "EXCELLENT":
        score += 15
    elif quality == "STRONG":
        score += 10
    elif quality == "WEAK":
        score -= 8
    elif quality == "POOR":
        score -= 15

    if growth >= 20:
        score += 15
    elif growth >= 10:
        score += 10
    elif growth >= 5:
        score += 5
    elif growth < 0:
        score -= 10

    if valuation == "ATTRACTIVE":
        score += 10
    elif valuation == "EXPENSIVE":
        score -= 10

    if analyst_consensus == "STRONG BUY":
        score += 8
    elif analyst_consensus == "BUY":
        score += 5
    elif analyst_consensus == "SELL":
        score -= 5
    elif analyst_consensus == "STRONG SELL":
        score -= 8

    if catalyst_strength == "STRONG":
        score += 5
    elif catalyst_strength == "WEAK":
        score -= 2

    if news_sentiment == "POSITIVE":
        score += 4
    elif news_sentiment == "NEGATIVE":
        score -= 4

    if risk == "VERY HIGH":
        score -= 15
    elif risk == "HIGH":
        score -= 8
    elif risk == "LOW":
        score += 3

    return max(0, min(100, score))


def get_verdict(score):

    if score >= 75:
        return "Very Strong"

    elif score >= 65:
        return "Strong"

    elif score >= 55:
        return "Moderate"

    elif score >= 40:
        return "Weak"

    return "Very Weak"


# =========================================================
# ACTION + JUSTIFICATION
# =========================================================

def get_action_and_reason(item):

    score = item["score"]
    quality = item["model"]["quality"]
    valuation = item["valuation"]
    risk = item["risk"]
    growth = item["model"]["growth"]
    catalyst = item["model"]["catalyst_strength"]

    analyst_text = get_analyst_text(item["info"])

    reasons = []

    if quality == "EXCELLENT":
        reasons.append("exceptional business quality")
    elif quality == "STRONG":
        reasons.append("strong business quality")
    elif quality == "WEAK":
        reasons.append("weak business quality")
    elif quality == "POOR":
        reasons.append("poor business quality")

    if growth >= 17:
        reasons.append("strong growth")
    elif growth >= 10:
        reasons.append("healthy growth")
    elif growth < 0:
        reasons.append("declining growth")
    elif growth <= 5:
        reasons.append("limited growth")

    if valuation == "ATTRACTIVE":
        reasons.append("attractive valuation")
    elif valuation == "EXPENSIVE":
        reasons.append("expensive valuation")
    else:
        reasons.append("fair valuation")

    if analyst_text:
        reasons.append(analyst_text)

    if catalyst == "STRONG":
        reasons.append("strong upcoming catalysts")
    elif catalyst == "MODERATE":
        reasons.append("some upcoming catalysts")

    if risk == "VERY HIGH":
        reasons.append("very high risk")
    elif risk == "HIGH":
        reasons.append("high risk")
    elif risk == "LOW":
        reasons.append("relatively low risk")

    sentiment = item.get(
        "overall_news_sentiment",
        "NEUTRAL"
    )

    if sentiment == "POSITIVE":
        reasons.append("positive recent news")
    elif sentiment == "NEGATIVE":
        reasons.append("negative recent news")

    if score >= 70 and risk not in ["HIGH", "VERY HIGH"]:
        action = "BUY"

    elif score >= 50:
        action = "HOLD"

    else:
        action = "SELL"

    if action == "BUY":

        priority = [
            "attractive valuation",
            "strong growth",
            "healthy growth",
            "exceptional business quality",
            "strong business quality",
            "positive analyst consensus",
            "strong upcoming catalysts",
            "positive recent news",
            "relatively low risk"
        ]

    elif action == "HOLD":

        priority = [
            "expensive valuation",
            "fair valuation",
            "exceptional business quality",
            "strong business quality",
            "strong growth",
            "healthy growth",
            "positive analyst consensus",
            "neutral analyst consensus",
            "high risk",
            "strong upcoming catalysts",
            "negative recent news"
        ]

    else:

        priority = [
            "very high risk",
            "high risk",
            "poor business quality",
            "weak business quality",
            "negative analyst consensus",
            "declining growth",
            "limited growth",
            "expensive valuation",
            "negative recent news"
        ]

    selected = []

    for reason in priority:

        if reason in reasons:

            selected.append(reason)

        if len(selected) >= 3:
            break

    if not selected:
        selected = reasons[:3]

    if len(selected) == 1:

        explanation = (
            selected[0].capitalize() + "."
        )

    elif len(selected) == 2:

        explanation = (
            selected[0].capitalize()
            + " and "
            + selected[1]
            + "."
        )

    else:

        explanation = (
            selected[0].capitalize()
            + ", "
            + selected[1]
            + ", with "
            + selected[2]
            + "."
        )

    return action, explanation


# =========================================================
# STOCK ANALYSIS
# =========================================================

@st.cache_data(ttl=900)
def analyse_stock(ticker):

    try:

        stock = yf.Ticker(ticker)

        info = stock.info

        name = info.get(
            "longName",
            ticker
        )

        sector = info.get(
            "sector",
            "N/A"
        )

        # -------------------------------------------------
        # NEWS
        # -------------------------------------------------

        news_items = []

        try:

            raw_news = stock.news

            if raw_news:

                for item in raw_news[:3]:

                    content = item.get(
                        "content",
                        {}
                    )

                    title = (
                        content.get("title")
                        or item.get("title")
                        or "No title available"
                    )

                    summary = (
                        content.get("summary")
                        or item.get("summary")
                        or create_news_summary(title)
                    )

                    sentiment = get_news_sentiment(
                        title
                    )

                    news_items.append({
                        "title": title,
                        "summary": summary,
                        "sentiment": sentiment
                    })

        except Exception:
            pass

        sentiments = [
            item["sentiment"]
            for item in news_items
        ]

        positive = sentiments.count("POSITIVE")
        negative = sentiments.count("NEGATIVE")

        if positive > negative:
            overall_news_sentiment = "POSITIVE"

        elif negative > positive:
            overall_news_sentiment = "NEGATIVE"

        else:
            overall_news_sentiment = "NEUTRAL"

        # -------------------------------------------------
        # FUNDAMENTALS
        # -------------------------------------------------

        valuation = get_valuation(info)

        quality, quality_score = (
            get_business_quality(info)
        )

        growth = get_growth(info)

        risk = get_risk(
            info,
            growth
        )

        analyst_consensus = (
            get_analyst_consensus(info)
        )

        catalyst_strength = (
            get_catalyst_strength(info)
        )

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        score = calculate_score(
            info,
            valuation,
            quality,
            quality_score,
            growth,
            analyst_consensus,
            risk,
            catalyst_strength,
            overall_news_sentiment
        )

        verdict = get_verdict(score)

        # -------------------------------------------------
        # EVENTS
        # -------------------------------------------------

        events = get_events(
            stock,
            info
        )

        # -------------------------------------------------
        # MODEL
        # -------------------------------------------------

        model = {
            "score": score,
            "quality": quality,
            "quality_score": quality_score,
            "growth": growth,
            "valuation_label": valuation,
            "catalyst_strength": catalyst_strength,
            "verdict": verdict
        }

        return {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "info": info,
            "news": news_items,
            "sentiments": sentiments,
            "overall_news_sentiment": overall_news_sentiment,
            "valuation": valuation,
            "risk": risk,
            "analyst_consensus": analyst_consensus,
            "events": events,
            "model": model,
            "score": score
        }

    except Exception as e:

        return {
            "ticker": ticker,
            "error": str(e)
        }


# =========================================================
# MAIN APP
# =========================================================

st.title("📊 Investment Analyst")

st.caption(
    "Fundamentals • Valuation • Growth • Analysts • News • Catalysts • Key Dates"
)

if st.button("🔄 Refresh Analysis"):

    st.cache_data.clear()
    st.rerun()


# =========================================================
# ANALYSE PORTFOLIO
# =========================================================

results = []

progress = st.progress(0)

for index, ticker in enumerate(portfolio):

    result = analyse_stock(ticker)

    if "error" not in result:
        results.append(result)

    progress.progress(
        (index + 1) / len(portfolio)
    )

progress.empty()


if not results:

    st.error("No stocks could be analysed.")

    st.stop()


# =========================================================
# SUMMARY
# =========================================================

st.header("Summary")

# Best opportunity

best = max(
    results,
    key=lambda x: x["score"]
)

# Highest risk

risk_order = {
    "LOW": 1,
    "MODERATE": 2,
    "HIGH": 3,
    "VERY HIGH": 4
}

highest_risk = max(
    results,
    key=lambda x: risk_order.get(
        x["risk"],
        0
    )
)

# Attractive valuation

attractive = [
    item
    for item in results
    if item["valuation"] == "ATTRACTIVE"
]

if attractive:

    most_attractive = max(
        attractive,
        key=lambda x: x["score"]
    )

else:

    most_attractive = min(
        results,
        key=lambda x: x["score"]
    )


col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Best Opportunity",
        best["ticker"],
        f"{best['score']}/100"
    )

with col2:

    st.metric(
        "Highest Risk",
        highest_risk["ticker"],
        highest_risk["risk"]
    )

with col3:

    st.metric(
        "Most Attractive Valuation",
        most_attractive["ticker"],
        most_attractive["valuation"]
    )


# =========================================================
# ACTION SUMMARY
# =========================================================

st.subheader("Stock Actions")

for item in results:

    action, explanation = (
        get_action_and_reason(item)
    )

    icon = action_colour(action)

    with st.container(border=True):

        st.markdown(
            f"### {icon} {item['ticker']} — {action}"
        )

        st.write(
            explanation
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.write(
                f"**Score:** {item['score']}/100"
            )

        with c2:
            st.write(
                f"**Quality:** {item['model']['quality']}"
            )

        with c3:
            st.write(
                f"**Growth:** {item['model']['growth']:.1f}%"
            )

        with c4:
            st.write(
                f"**Analysts:** {item['analyst_consensus']}"
            )


# =========================================================
# IMMEDIATE KEY DATES
# =========================================================

st.subheader("Immediate Key Dates")

all_events = []

for item in results:

    for event in item["events"]:

        if event["date"] >= date.today():

            all_events.append({
                "ticker": item["ticker"],
                **event
            })

all_events.sort(
    key=lambda x: (
        x["date"],
        x["priority"]
    )
)

if all_events:

    for event in all_events[:7]:

        days = (
            event["date"]
            - date.today()
        ).days

        if days == 0:
            timing = "TODAY"

        elif days == 1:
            timing = "TOMORROW"

        else:
            timing = f"in {days} days"

        st.write(
            f"**{event['date'].strftime('%d %b %Y')}** "
            f"— {event['ticker']} — "
            f"{event['type']} "
            f"({timing})"
        )

else:

    st.write(
        "No upcoming key dates found."
    )


# =========================================================
# OVERALL NEWS
# =========================================================

positive = sum(
    item["sentiments"].count("POSITIVE")
    for item in results
)

negative = sum(
    item["sentiments"].count("NEGATIVE")
    for item in results
)

neutral = sum(
    item["sentiments"].count("NEUTRAL")
    for item in results
)

if positive > negative:
    overall_sentiment = "POSITIVE"

elif negative > positive:
    overall_sentiment = "NEGATIVE"

else:
    overall_sentiment = "NEUTRAL"

st.subheader("Overall News Sentiment")

st.write(
    f"{sentiment_colour(overall_sentiment)} "
    f"**{overall_sentiment}**"
)


# =========================================================
# DETAILED STOCK REPORTS
# =========================================================

st.header("Detailed Stock Reports")

for item in results:

    with st.expander(
        f"{item['ticker']} — {item['name']}"
    ):

        info = item["info"]

        action, explanation = (
            get_action_and_reason(item)
        )

        # -------------------------------------------------
        # OVERALL
        # -------------------------------------------------

        st.subheader("Overall")

        st.write(
            f"**Action:** "
            f"{action_colour(action)} {action}"
        )

        st.write(
            f"**Score:** {item['score']}/100"
        )

        st.write(
            f"**Verdict:** "
            f"{item['model']['verdict']}"
        )

        st.write(
            f"**Reason:** {explanation}"
        )

        # -------------------------------------------------
        # MARKET DATA
        # -------------------------------------------------

        st.subheader("Market Data")

        current_price = info.get(
            "currentPrice"
        )

        previous_close = info.get(
            "previousClose"
        )

        market_cap = info.get(
            "marketCap"
        )

        fifty_two_high = info.get(
            "fiftyTwoWeekHigh"
        )

        fifty_two_low = info.get(
            "fiftyTwoWeekLow"
        )

        if current_price is not None:

            st.write(
                f"**Current Price:** {current_price:.2f}"
            )

        if previous_close is not None:

            st.write(
                f"**Previous Close:** {previous_close:.2f}"
            )

        if market_cap is not None:

            st.write(
                f"**Market Cap:** {market_cap:,.0f}"
            )

        if (
            current_price is not None
            and fifty_two_high is not None
            and fifty_two_low is not None
            and fifty_two_high != fifty_two_low
        ):

            position = (
                (
                    current_price
                    - fifty_two_low
                )
                /
                (
                    fifty_two_high
                    - fifty_two_low
                )
                * 100
            )

            st.write(
                f"**52-Week Position:** "
                f"{position:.1f}%"
            )

            st.progress(
                max(
                    0,
                    min(
                        100,
                        position
                    )
                ) / 100
            )

        if fifty_two_low is not None:

            st.write(
                f"**52-Week Low:** "
                f"{fifty_two_low:.2f}"
            )

        if fifty_two_high is not None:

            st.write(
                f"**52-Week High:** "
                f"{fifty_two_high:.2f}"
            )

        # -------------------------------------------------
        # FUNDAMENTALS
        # -------------------------------------------------

        st.subheader("Fundamentals")

        st.write(
            f"**Business Quality:** "
            f"{item['model']['quality']}"
        )

        st.write(
            f"**Revenue/Earnings Growth:** "
            f"{item['model']['growth']:.1f}%"
        )

        roe = info.get(
            "returnOnEquity"
        )

        profit_margin = info.get(
            "profitMargins"
        )

        operating_margin = info.get(
            "operatingMargins"
        )

        debt_to_equity = info.get(
            "debtToEquity"
        )

        if roe is not None:

            st.write(
                f"**ROE:** {roe * 100:.1f}%"
            )

        if profit_margin is not None:

            st.write(
                f"**Profit Margin:** "
                f"{profit_margin * 100:.1f}%"
            )

        if operating_margin is not None:

            st.write(
                f"**Operating Margin:** "
                f"{operating_margin * 100:.1f}%"
            )

        if debt_to_equity is not None:

            st.write(
                f"**Debt / Equity:** "
                f"{debt_to_equity:.1f}"
            )

        # -------------------------------------------------
        # VALUATION
        # -------------------------------------------------

        st.subheader("Valuation")

        st.write(
            f"**Assessment:** "
            f"{valuation_colour(item['valuation'])} "
            f"{item['valuation']}"
        )

        forward_pe = info.get(
            "forwardPE"
        )

        trailing_pe = info.get(
            "trailingPE"
        )

        peg = info.get(
            "pegRatio"
        )

        if forward_pe is not None:

            st.write(
                f"**Forward P/E:** "
                f"{forward_pe:.2f}"
            )

        if trailing_pe is not None:

            st.write(
                f"**Trailing P/E:** "
                f"{trailing_pe:.2f}"
            )

        if peg is not None:

            st.write(
                f"**PEG Ratio:** "
                f"{peg:.2f}"
            )

        # -------------------------------------------------
        # ANALYSTS
        # -------------------------------------------------

        st.subheader(
            "Analyst Consensus"
        )

        consensus = item[
            "analyst_consensus"
        ]

        st.write(
            f"**Consensus:** {consensus}"
        )

        analyst_count = info.get(
            "numberOfAnalystOpinions"
        )

        target = info.get(
            "targetMeanPrice"
        )

        high_target = info.get(
            "targetHighPrice"
        )

        low_target = info.get(
            "targetLowPrice"
        )

        if analyst_count is not None:

            st.write(
                f"**Analyst Count:** "
                f"{analyst_count}"
            )

        if target is not None:

            st.write(
                f"**Average Target:** "
                f"{target:.2f}"
            )

        if (
            target is not None
            and current_price
        ):

            upside = (
                (
                    target
                    / current_price
                    - 1
                )
                * 100
            )

            st.write(
                f"**Target Upside:** "
                f"{upside:.1f}%"
            )

        if high_target is not None:

            st.write(
                f"**High Target:** "
                f"{high_target:.2f}"
            )

        if low_target is not None:

            st.write(
                f"**Low Target:** "
                f"{low_target:.2f}"
            )

        # -------------------------------------------------
        # EARNINGS
        # -------------------------------------------------

        st.subheader("Earnings")

        earnings = info.get(
            "earningsTimestamp"
        )

        if earnings:

            try:

                earnings_date = (
                    datetime.fromtimestamp(
                        earnings
                    ).date()
                )

                st.write(
                    f"**Next Earnings:** "
                    f"{earnings_date.strftime('%d %b %Y')}"
                )

            except Exception:

                st.write(
                    "Earnings date unavailable."
                )

        else:

            st.write(
                "Earnings date unavailable."
            )

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        st.subheader("Risk")

        st.write(
            f"**Risk Assessment:** "
            f"{risk_colour(item['risk'])} "
            f"{item['risk']}"
        )

        beta = info.get(
            "beta"
        )

        if beta is not None:

            st.write(
                f"**Beta:** {beta:.2f}"
            )

        # -------------------------------------------------
        # CATALYSTS
        # -------------------------------------------------

        st.subheader("Catalysts")

        st.write(
            f"**Catalyst Strength:** "
            f"{item['model']['catalyst_strength']}"
        )

        # -------------------------------------------------
        # NEWS
        # -------------------------------------------------

        st.subheader(
            "Recent News"
        )

        if not item["news"]:

            st.write(
                "No recent news found."
            )

        else:

            for index, news in enumerate(
                item["news"],
                start=1
            ):

                st.markdown(
                    f"**{index}. "
                    f"{news['title']}**"
                )

                st.write(
                    f"{sentiment_colour(news['sentiment'])} "
                    f"{news['sentiment']}"
                )

                st.write(
                    f"**Summary:** "
                    f"{news['summary']}"
                )

        st.write(
            f"**Overall News Sentiment:** "
            f"{sentiment_colour(item['overall_news_sentiment'])} "
            f"{item['overall_news_sentiment']}"
        )

        # -------------------------------------------------
        # KEY DATES
        # -------------------------------------------------

        st.subheader(
            "Key Next Dates"
        )

        future_events = [
            event
            for event in item["events"]
            if event["date"] >= date.today()
        ]

        future_events.sort(
            key=lambda x: (
                x["date"],
                x["priority"]
            )
        )

        if future_events:

            for event in future_events:

                days = (
                    event["date"]
                    - date.today()
                ).days

                if days == 0:
                    timing = "TODAY"

                elif days == 1:
                    timing = "TOMORROW"

                else:
                    timing = f"in {days} days"

                st.write(
                    f"**{event['date'].strftime('%d %b %Y')}** "
                    f"— {event['type']} "
                    f"({timing})"
                )

        else:

            st.write(
                "No upcoming dates found."
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    f"Companies analysed: {len(results)}"
)

st.caption(
    "Data and analysis are for research purposes only."
)
