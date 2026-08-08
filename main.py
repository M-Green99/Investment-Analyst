```python
# main.py

import yfinance as yf
from datetime import date, datetime
from colorama import init, Fore, Style

# =========================================================
# COLOUR SETUP
# =========================================================

init(autoreset=True)

GREEN = Fore.GREEN
RED = Fore.RED
AMBER = Fore.YELLOW
CYAN = Fore.CYAN
WHITE = Fore.WHITE
GREY = Fore.LIGHTBLACK_EX
BOLD = Style.BRIGHT


# =========================================================
# GENERAL HELPERS
# =========================================================

def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def format_number(value, decimals=2):
    value = safe_float(value)

    if value is None:
        return "N/A"

    return f"{value:,.{decimals}f}"


def format_percentage(value, decimals=1):
    value = safe_float(value)

    if value is None:
        return "N/A"

    return f"{value:.{decimals}f}%"


def format_large_number(value):
    value = safe_float(value)

    if value is None:
        return "N/A"

    absolute = abs(value)

    if absolute >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"

    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if absolute >= 1_000:
        return f"{value / 1_000:.2f}K"

    return f"{value:,.2f}"


def colour_text(text, colour):
    return f"{colour}{text}{Fore.RESET}"


def colour_score(score):
    if score >= 70:
        colour = GREEN
    elif score >= 55:
        colour = AMBER
    else:
        colour = RED

    return f"{colour}{score}/100{Fore.RESET}"


def colour_sentiment(sentiment):
    if sentiment == "POSITIVE":
        return f"{GREEN}{sentiment}{Fore.RESET}"

    if sentiment == "NEGATIVE":
        return f"{RED}{sentiment}{Fore.RESET}"

    return f"{AMBER}{sentiment}{Fore.RESET}"


def colour_risk(risk):
    if risk in ["VERY HIGH", "HIGH"]:
        return f"{RED}{risk}{Fore.RESET}"

    if risk == "MODERATE":
        return f"{AMBER}{risk}{Fore.RESET}"

    return f"{GREEN}{risk}{Fore.RESET}"


def colour_valuation(valuation):
    if valuation == "ATTRACTIVE":
        return f"{GREEN}{valuation}{Fore.RESET}"

    if valuation == "EXPENSIVE":
        return f"{RED}{valuation}{Fore.RESET}"

    return f"{AMBER}{valuation}{Fore.RESET}"


def colour_quality(quality):
    if quality in ["EXCELLENT", "STRONG"]:
        return f"{GREEN}{quality}{Fore.RESET}"

    if quality in ["WEAK", "POOR"]:
        return f"{RED}{quality}{Fore.RESET}"

    return f"{AMBER}{quality}{Fore.RESET}"


def colour_catalyst(catalyst):
    if catalyst == "STRONG":
        return f"{GREEN}{catalyst}{Fore.RESET}"

    if catalyst == "WEAK":
        return f"{RED}{catalyst}{Fore.RESET}"

    return f"{AMBER}{catalyst}{Fore.RESET}"


def colour_upside(upside):
    if upside is None:
        return "N/A"

    if upside >= 10:
        return f"{GREEN}{upside:.1f}%{Fore.RESET}"

    if upside >= 0:
        return f"{AMBER}{upside:.1f}%{Fore.RESET}"

    return f"{RED}{upside:.1f}%{Fore.RESET}"


# =========================================================
# NEWS SENTIMENT
# =========================================================

def get_news_sentiment(title):

    if not title:
        return "NEUTRAL"

    text = title.lower()

    positive_words = [
        "growth",
        "profit",
        "profits",
        "beats",
        "beat",
        "upgrade",
        "surge",
        "record",
        "strong",
        "raises",
        "raised",
        "positive",
        "contract",
        "deal",
        "partnership",
        "launch",
        "expands",
        "expansion",
        "orders",
        "approval",
        "approved",
        "breakthrough",
        "bullish",
        "guidance",
        "outlook",
        "demand",
        "revenue",
        "earnings"
    ]

    negative_words = [
        "loss",
        "losses",
        "miss",
        "misses",
        "downgrade",
        "fall",
        "falls",
        "drop",
        "drops",
        "weak",
        "warning",
        "cuts",
        "cut",
        "decline",
        "declines",
        "lawsuit",
        "investigation",
        "delay",
        "delays",
        "debt",
        "concern",
        "concerns",
        "bearish",
        "risk",
        "slump",
        "recall",
        "fraud",
        "layoffs"
    ]

    positive_score = sum(
        1 for word in positive_words if word in text
    )

    negative_score = sum(
        1 for word in negative_words if word in text
    )

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

    if consensus == "STRONG BUY":
        return "strong analyst consensus"

    if consensus == "BUY":
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

    forward_pe = safe_float(info.get("forwardPE"))
    trailing_pe = safe_float(info.get("trailingPE"))
    peg = safe_float(info.get("pegRatio"))

    if peg is not None:

        if peg < 1:
            return "ATTRACTIVE"

        if peg > 2:
            return "EXPENSIVE"

    pe = forward_pe or trailing_pe

    if pe is not None:

        if pe < 20:
            return "ATTRACTIVE"

        if pe > 40:
            return "EXPENSIVE"

    return "FAIR"


# =========================================================
# BUSINESS QUALITY
# =========================================================

def get_business_quality(info):

    roe = safe_float(info.get("returnOnEquity"))
    profit_margin = safe_float(info.get("profitMargins"))
    operating_margin = safe_float(info.get("operatingMargins"))

    score = 0

    if roe is not None:

        if roe >= 0.20:
            score += 2

        elif roe >= 0.10:
            score += 1

    if profit_margin is not None:

        if profit_margin >= 0.15:
            score += 2

        elif profit_margin > 0:
            score += 1

    if operating_margin is not None:

        if operating_margin >= 0.15:
            score += 2

        elif operating_margin > 0:
            score += 1

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

    revenue_growth = safe_float(
        info.get("revenueGrowth")
    )

    earnings_growth = safe_float(
        info.get("earningsGrowth")
    )

    values = []

    for value in [
        revenue_growth,
        earnings_growth
    ]:

        if value is not None:
            values.append(value)

    if not values:
        return 0

    return sum(values) / len(values) * 100


# =========================================================
# RISK
# =========================================================

def get_risk(info, growth):

    beta = safe_float(info.get("beta"))
    profit_margin = safe_float(info.get("profitMargins"))
    debt_to_equity = safe_float(info.get("debtToEquity"))

    risk_score = 0

    if beta is not None:

        if beta >= 2:
            risk_score += 3

        elif beta >= 1.4:
            risk_score += 2

        elif beta >= 1:
            risk_score += 1

    if debt_to_equity is not None:

        if debt_to_equity >= 150:
            risk_score += 2

        elif debt_to_equity >= 80:
            risk_score += 1

    if profit_margin is not None:

        if profit_margin < 0:
            risk_score += 2

    if growth < 0:
        risk_score += 1

    if risk_score >= 5:
        return "VERY HIGH"

    if risk_score >= 3:
        return "HIGH"

    if risk_score >= 1:
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

    recommendation = info.get(
        "recommendationKey"
    )

    if recommendation in [
        "strong_buy",
        "buy"
    ]:
        score += 1

    if score >= 2:
        return "STRONG"

    if score == 1:
        return "MODERATE"

    return "WEAK"


# =========================================================
# KEY EVENTS
# =========================================================

def get_events(stock, info):

    events = []

    # -----------------------------------------------------
    # Earnings
    # -----------------------------------------------------

    earnings = info.get("earningsTimestamp")

    if earnings:

        try:

            event_date = datetime.fromtimestamp(
                earnings
            ).date()

            events.append(
                {
                    "date": event_date,
                    "type": "EARNINGS",
                    "priority": 1
                }
            )

        except Exception:
            pass

    # -----------------------------------------------------
    # Dividend
    # -----------------------------------------------------

    ex_dividend = info.get(
        "exDividendDate"
    )

    if ex_dividend:

        try:

            event_date = datetime.fromtimestamp(
                ex_dividend
            ).date()

            events.append(
                {
                    "date": event_date,
                    "type": "DIVIDEND",
                    "priority": 3
                }
            )

        except Exception:
            pass

    # -----------------------------------------------------
    # Calendar
    # -----------------------------------------------------

    try:

        calendar = stock.calendar

        if calendar is not None:

            if hasattr(calendar, "to_dict"):

                calendar_data = calendar.to_dict()

                earnings_dates = calendar_data.get(
                    "Earnings Date"
                )

                if earnings_dates:

                    for event_date in earnings_dates:

                        if hasattr(
                            event_date,
                            "date"
                        ):
                            event_date = event_date.date()

                        if isinstance(
                            event_date,
                            date
                        ):

                            events.append(
                                {
                                    "date": event_date,
                                    "type": "EARNINGS",
                                    "priority": 1
                                }
                            )

    except Exception:
        pass

    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

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


def get_event_icon(event_type):

    icons = {
        "EARNINGS": "EARNINGS",
        "DIVIDEND": "DIVIDEND",
        "CONFERENCE": "CONFERENCE",
        "PRODUCT": "PRODUCT"
    }

    return icons.get(
        event_type,
        "EVENT"
    )


def get_event_colour(event_type):

    if event_type == "EARNINGS":
        return AMBER

    if event_type in [
        "CONFERENCE",
        "PRODUCT"
    ]:
        return GREEN

    return CYAN


# =========================================================
# SCORE
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

    # -----------------------------------------------------
    # Business Quality
    # -----------------------------------------------------

    if quality == "EXCELLENT":
        score += 15

    elif quality == "STRONG":
        score += 10

    elif quality == "WEAK":
        score -= 8

    elif quality == "POOR":
        score -= 15

    # -----------------------------------------------------
    # Growth
    # -----------------------------------------------------

    if growth >= 20:
        score += 15

    elif growth >= 10:
        score += 10

    elif growth >= 5:
        score += 5

    elif growth < 0:
        score -= 10

    # -----------------------------------------------------
    # Valuation
    # -----------------------------------------------------

    if valuation == "ATTRACTIVE":
        score += 10

    elif valuation == "EXPENSIVE":
        score -= 10

    # -----------------------------------------------------
    # Analysts
    # -----------------------------------------------------

    if analyst_consensus == "STRONG BUY":
        score += 8

    elif analyst_consensus == "BUY":
        score += 5

    elif analyst_consensus == "SELL":
        score -= 5

    elif analyst_consensus == "STRONG SELL":
        score -= 8

    # -----------------------------------------------------
    # Catalysts
    # -----------------------------------------------------

    if catalyst_strength == "STRONG":
        score += 5

    elif catalyst_strength == "WEAK":
        score -= 2

    # -----------------------------------------------------
    # News
    # -----------------------------------------------------

    if news_sentiment == "POSITIVE":
        score += 4

    elif news_sentiment == "NEGATIVE":
        score -= 4

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    if risk == "VERY HIGH":
        score -= 15

    elif risk == "HIGH":
        score -= 8

    elif risk == "LOW":
        score += 3

    score = max(
        0,
        min(100, score)
    )

    return score


def get_verdict(score):

    if score >= 75:
        return "Very Strong"

    if score >= 65:
        return "Strong"

    if score >= 55:
        return "Moderate"

    if score >= 40:
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

    analyst_text = get_analyst_text(
        item["info"]
    )

    reasons = []

    # -----------------------------------------------------
    # Quality
    # -----------------------------------------------------

    if quality == "EXCELLENT":
        reasons.append(
            "exceptional business quality"
        )

    elif quality == "STRONG":
        reasons.append(
            "strong business quality"
        )

    elif quality == "WEAK":
        reasons.append(
            "weak business quality"
        )

    elif quality == "POOR":
        reasons.append(
            "poor business quality"
        )

    # -----------------------------------------------------
    # Growth
    # -----------------------------------------------------

    if growth >= 17:
        reasons.append(
            "strong growth"
        )

    elif growth >= 10:
        reasons.append(
            "healthy growth"
        )

    elif growth < 0:
        reasons.append(
            "declining growth"
        )

    elif growth <= 5:
        reasons.append(
            "limited growth"
        )

    # -----------------------------------------------------
    # Valuation
    # -----------------------------------------------------

    if valuation == "ATTRACTIVE":
        reasons.append(
            "attractive valuation"
        )

    elif valuation == "EXPENSIVE":
        reasons.append(
            "expensive valuation"
        )

    else:
        reasons.append(
            "fair valuation"
        )

    # -----------------------------------------------------
    # Analysts
    # -----------------------------------------------------

    if analyst_text:
        reasons.append(
            analyst_text
        )

    # -----------------------------------------------------
    # Catalysts
    # -----------------------------------------------------

    if catalyst == "STRONG":
        reasons.append(
            "strong upcoming catalysts"
        )

    elif catalyst == "MODERATE":
        reasons.append(
            "some upcoming catalysts"
        )

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    if risk == "VERY HIGH":
        reasons.append(
            "very high risk"
        )

    elif risk == "HIGH":
        reasons.append(
            "high risk"
        )

    elif risk == "LOW":
        reasons.append(
            "relatively low risk"
        )

    # -----------------------------------------------------
    # News
    # -----------------------------------------------------

    sentiment = item.get(
        "overall_news_sentiment",
        "NEUTRAL"
    )

    if sentiment == "POSITIVE":
        reasons.append(
            "positive recent news"
        )

    elif sentiment == "NEGATIVE":
        reasons.append(
            "negative recent news"
        )

    # -----------------------------------------------------
    # Action
    # -----------------------------------------------------

    if (
        score >= 70
        and risk not in [
            "HIGH",
            "VERY HIGH"
        ]
    ):
        action = "BUY"

    elif score >= 50:
        action = "HOLD"

    else:
        action = "SELL"

    # -----------------------------------------------------
    # Priorities
    # -----------------------------------------------------

    if action == "BUY":

        priority = [
            "attractive valuation",
            "strong growth",
            "healthy growth",
            "exceptional business quality",
            "strong business quality",
            "strong analyst consensus",
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
            selected[0].capitalize()
            + "."
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

def analyse_stock(ticker):

    print(
        f"{GREY}Analysing {ticker}...{Fore.RESET}"
    )

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

        # =================================================
        # MARKET DATA
        # =================================================

        current_price = safe_float(
            info.get("currentPrice")
            or info.get("regularMarketPrice")
        )

        previous_close = safe_float(
            info.get("previousClose")
        )

        day_low = safe_float(
            info.get("dayLow")
        )

        day_high = safe_float(
            info.get("dayHigh")
        )

        fifty_two_week_low = safe_float(
            info.get("fiftyTwoWeekLow")
        )

        fifty_two_week_high = safe_float(
            info.get("fiftyTwoWeekHigh")
        )

        fifty_two_week_position = None

        if (
            current_price is not None
            and fifty_two_week_low is not None
            and fifty_two_week_high is not None
            and fifty_two_week_high > fifty_two_week_low
        ):

            fifty_two_week_position = (
                (
                    current_price
                    - fifty_two_week_low
                )
                /
                (
                    fifty_two_week_high
                    - fifty_two_week_low
                )
            ) * 100

        market_cap = safe_float(
            info.get("marketCap")
        )

        enterprise_value = safe_float(
            info.get("enterpriseValue")
        )

        # =================================================
        # NEWS
        # =================================================

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

                    news_items.append(
                        {
                            "title": title,
                            "summary": summary,
                            "sentiment": sentiment
                        }
                    )

        except Exception:
            pass

        sentiments = [
            item["sentiment"]
            for item in news_items
        ]

        positive = sentiments.count(
            "POSITIVE"
        )

        negative = sentiments.count(
            "NEGATIVE"
        )

        neutral = sentiments.count(
            "NEUTRAL"
        )

        if positive > negative:
            overall_news_sentiment = "POSITIVE"

        elif negative > positive:
            overall_news_sentiment = "NEGATIVE"

        else:
            overall_news_sentiment = "NEUTRAL"

        # =================================================
        # FUNDAMENTALS
        # =================================================

        revenue = safe_float(
            info.get("totalRevenue")
        )

        gross_profit = safe_float(
            info.get("grossProfits")
        )

        operating_income = safe_float(
            info.get("operatingIncome")
        )

        net_income = safe_float(
            info.get("netIncomeToCommon")
            or info.get("netIncome")
        )

        operating_cash_flow = safe_float(
            info.get("operatingCashflow")
        )

        free_cash_flow = safe_float(
            info.get("freeCashflow")
        )

        debt_to_equity = safe_float(
            info.get("debtToEquity")
        )

        current_ratio = safe_float(
            info.get("currentRatio")
        )

        return_on_equity = safe_float(
            info.get("returnOnEquity")
        )

        return_on_assets = safe_float(
            info.get("returnOnAssets")
        )

        profit_margin = safe_float(
            info.get("profitMargins")
        )

        operating_margin = safe_float(
            info.get("operatingMargins")
        )

        revenue_growth = safe_float(
            info.get("revenueGrowth")
        )

        earnings_growth = safe_float(
            info.get("earningsGrowth")
        )

        # =================================================
        # VALUATION
        # =================================================

        trailing_pe = safe_float(
            info.get("trailingPE")
        )

        forward_pe = safe_float(
            info.get("forwardPE")
        )

        peg_ratio = safe_float(
            info.get("pegRatio")
        )

        price_to_book = safe_float(
            info.get("priceToBook")
        )

        price_to_sales = safe_float(
            info.get("priceToSalesTrailing12Months")
        )

        enterprise_to_revenue = safe_float(
            info.get("enterpriseToRevenue")
        )

        enterprise_to_ebitda = safe_float(
            info.get("enterpriseToEbitda")
        )

        dividend_yield = safe_float(
            info.get("dividendYield")
        )

        payout_ratio = safe_float(
            info.get("payoutRatio")
        )

        valuation = get_valuation(
            info
        )

        # =================================================
        # BUSINESS QUALITY
        # =================================================

        quality, quality_score = (
            get_business_quality(info)
        )

        # =================================================
        # GROWTH
        # =================================================

        growth = get_growth(
            info
        )

        # =================================================
        # RISK
        # =================================================

        risk = get_risk(
            info,
            growth
        )

        # =================================================
        # ANALYST CONSENSUS
        # =================================================

        analyst_consensus = (
            get_analyst_consensus(info)
        )

        analyst_count = info.get(
            "numberOfAnalystOpinions"
        )

        target_mean_price = safe_float(
            info.get("targetMeanPrice")
        )

        target_high_price = safe_float(
            info.get("targetHighPrice")
        )

        target_low_price = safe_float(
            info.get("targetLowPrice")
        )

        target_upside = None

        if (
            target_mean_price is not None
            and current_price is not None
            and current_price != 0
        ):

            target_upside = (
                target_mean_price
                /
                current_price
                - 1
            ) * 100

        # =================================================
        # EARNINGS
        # =================================================

        earnings_timestamp = info.get(
            "earningsTimestamp"
        )

        earnings_date = None

        if earnings_timestamp:

            try:

                earnings_date = (
                    datetime.fromtimestamp(
                        earnings_timestamp
                    ).date()
                )

            except Exception:
                earnings_date = None

        forward_eps = safe_float(
            info.get("forwardEps")
        )

        trailing_eps = safe_float(
            info.get("trailingEps")
        )

        earnings_data = {
            "date": earnings_date,
            "forward_eps": forward_eps,
            "trailing_eps": trailing_eps
        }

        # =================================================
        # CATALYSTS
        # =================================================

        catalyst_strength = (
            get_catalyst_strength(info)
        )

        # =================================================
        # SCORE
        # =================================================

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

        verdict = get_verdict(
            score
        )

        # =================================================
        # EVENTS
        # =================================================

        events = get_events(
            stock,
            info
        )

        # =================================================
        # MODEL DATA
        # =================================================

        model = {
            "score": score,
            "quality": quality,
            "quality_score": quality_score,
            "growth": growth,
            "valuation_label": valuation,
            "catalyst": (
                2
                if catalyst_strength == "STRONG"
                else 1
                if catalyst_strength == "MODERATE"
                else 0
            ),
            "catalyst_strength": catalyst_strength,
            "verdict": verdict
        }

        # =================================================
        # RETURN COMPLETE RESULT
        # =================================================

        return {

            "ticker": ticker,

            "name": name,

            "sector": sector,

            "info": info,

            "news": news_items,

            "sentiments": sentiments,

            "overall_news_sentiment":
                overall_news_sentiment,

            "valuation": valuation,

            "valuation_data": {
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "peg_ratio": peg_ratio,
                "price_to_book": price_to_book,
                "price_to_sales": price_to_sales,
                "enterprise_to_revenue":
                    enterprise_to_revenue,
                "enterprise_to_ebitda":
                    enterprise_to_ebitda,
                "dividend_yield":
                    dividend_yield,
                "payout_ratio":
                    payout_ratio
            },

            "market": {
                "current_price":
                    current_price,
                "previous_close":
                    previous_close,
                "day_low":
                    day_low,
                "day_high":
                    day_high,
                "fifty_two_week_low":
                    fifty_two_week_low,
                "fifty_two_week_high":
                    fifty_two_week_high,
                "fifty_two_week_position":
                    fifty_two_week_position,
                "market_cap":
                    market_cap,
                "enterprise_value":
                    enterprise_value
            },

            "fundamentals": {
                "revenue":
                    revenue,
                "gross_profit":
                    gross_profit,
                "operating_income":
                    operating_income,
                "net_income":
                    net_income,
                "operating_cash_flow":
                    operating_cash_flow,
                "free_cash_flow":
                    free_cash_flow,
                "debt_to_equity":
                    debt_to_equity,
                "current_ratio":
                    current_ratio,
                "return_on_equity":
                    return_on_equity,
                "return_on_assets":
                    return_on_assets,
                "profit_margin":
                    profit_margin,
                "operating_margin":
                    operating_margin,
                "revenue_growth":
                    revenue_growth,
                "earnings_growth":
                    earnings_growth
            },

            "earnings":
                earnings_data,

            "risk": risk,

            "analyst_consensus":
                analyst_consensus,

            "analyst_count":
                analyst_count,

            "target_mean_price":
                target_mean_price,

            "target_high_price":
                target_high_price,

            "target_low_price":
                target_low_price,

            "target_upside":
                target_upside,

            "events":
                events,

            "model":
                model,

            "score":
                score
        }

    except Exception as e:

        print(
            f"{RED}Error analysing "
            f"{ticker}: {e}{Fore.RESET}"
        )

        return None


# =========================================================
# PRINT SUMMARY
# =========================================================

def print_summary(results):

    print()

    print("=" * 75)

    print(
        f"{CYAN}{BOLD}"
        f" SUMMARY"
        f"{Fore.RESET}"
    )

    print("=" * 75)

    if not results:

        print(
            f"{RED}No stocks could be analysed."
            f"{Fore.RESET}"
        )

        return

    print()

    print(
        f"{CYAN}{BOLD}"
        f"STOCK ACTION"
        f"{'REASON':>25}"
        f"{Fore.RESET}"
    )

    print("-" * 75)

    for item in results:

        action, explanation = (
            get_action_and_reason(item)
        )

        if action == "BUY":

            action_display = (
                f"{GREEN}{BOLD}"
                f"BUY"
                f"{Fore.RESET}"
            )

        elif action == "HOLD":

            action_display = (
                f"{AMBER}{BOLD}"
                f"HOLD"
                f"{Fore.RESET}"
            )

        else:

            action_display = (
                f"{RED}{BOLD}"
                f"SELL"
                f"{Fore.RESET}"
            )

        print()

        print(
            f"{item['ticker']:<11}"
            f"{action_display}"
        )

        print(
            f" {explanation}"
        )

        print()

        print("-" * 75)

    # =====================================================
    # BEST OPPORTUNITY
    # =====================================================

    best = max(
        results,
        key=lambda x: x["score"]
    )

    print()

    print(
        "Best Opportunity: "
        f"{GREEN}{best['ticker']}"
        f"{Fore.RESET}"
        f" — "
        f"{colour_score(best['score'])}"
    )

    print(
        " Verdict: "
        f"{best['model']['verdict']}"
    )

    # =====================================================
    # HIGHEST RISK
    # =====================================================

    risk_order = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "VERY HIGH": 4
    }

    highest_risk = max(
        results,
        key=lambda x:
        risk_order.get(
            x["risk"],
            0
        )
    )

    print()

    print(
        "Highest Risk: "
        f"{RED}{highest_risk['ticker']}"
        f"{Fore.RESET}"
        f" — "
        f"{colour_risk(highest_risk['risk'])}"
    )

    # =====================================================
    # MOST ATTRACTIVE VALUATION
    # =====================================================

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

    print()

    print(
        "Most Attractive Valuation: "
        f"{GREEN}{most_attractive['ticker']}"
        f"{Fore.RESET}"
        f" — "
        f"{colour_valuation(most_attractive['valuation'])}"
    )

    # =====================================================
    # OVERALL NEWS SENTIMENT
    # =====================================================

    positive = sum(
        item["sentiments"].count(
            "POSITIVE"
        )
        for item in results
    )

    negative = sum(
        item["sentiments"].count(
            "NEGATIVE"
        )
        for item in results
    )

    neutral = sum(
        item["sentiments"].count(
            "NEUTRAL"
        )
        for item in results
    )

    if positive > negative:

        overall_sentiment = "POSITIVE"

    elif negative > positive:

        overall_sentiment = "NEGATIVE"

    else:

        overall_sentiment = "NEUTRAL"

    print()

    print(
        "Overall News Sentiment: "
        f"{colour_sentiment(overall_sentiment)}"
    )

    # =====================================================
    # STRONGEST BUSINESS
    # =====================================================

    strongest_business = max(
        results,
        key=lambda x:
        x["model"]["quality_score"]
    )

    print()

    print(
        "Strongest Business: "
        f"{GREEN}{strongest_business['ticker']}"
        f"{Fore.RESET}"
        f" — "
        f"{colour_quality("
            f"strongest_business['model']['quality']"
        f")}"
    )

    # =====================================================
    # STRONGEST CATALYST
    # =====================================================

    catalyst_results = [
        item
        for item in results
        if item["model"]["catalyst_strength"]
        == "STRONG"
    ]

    if catalyst_results:

        strongest_catalyst = max(
            catalyst_results,
            key=lambda x:
            x["model"]["catalyst"]
        )

        print()

        print(
            "Strongest Catalyst: "
            f"{GREEN}{strongest_catalyst['ticker']}"
            f"{Fore.RESET}"
            f" — "
            f"{colour_catalyst("
                f"strongest_catalyst"
                f"['model']['catalyst_strength']"
            f")}"
        )

    # =====================================================
    # IMMEDIATE KEY DATES
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"IMMEDIATE KEY DATES"
        f"{Fore.RESET}"
    )

    print()

    all_events = []

    for item in results:

        for event in item["events"]:

            if event["date"] >= date.today():

                all_events.append(
                    {
                        "ticker":
                            item["ticker"],
                        **event
                    }
                )

    all_events.sort(
        key=lambda x:
        (
            x["date"],
            x["priority"]
        )
    )

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
            timing = f"{days} days"

        event_colour = (
            get_event_colour(
                event["type"]
            )
        )

        event_type = (
            get_event_icon(
                event["type"]
            )
        )

        print(
            f"{event['date'].strftime('%d %b %Y')} "
            f"{event['ticker']:<7}"
            f"{event_colour}"
            f"{event_type:<13}"
            f"{Fore.RESET}"
            f" ({timing})"
        )

    if not all_events:

        print(
            "No upcoming key dates found."
        )

    print()

    print(
        f"Companies Analysed: "
        f"{len(results)}"
    )

    print(
        f"Positive News Articles: "
        f"{GREEN}{positive}{Fore.RESET}"
    )

    print(
        f"Neutral News Articles: "
        f"{AMBER}{neutral}{Fore.RESET}"
    )

    print(
        f"Negative News Articles: "
        f"{RED}{negative}{Fore.RESET}"
    )

    print()

    print("-" * 75)


# =========================================================
# DETAILED STOCK REPORT
# =========================================================

def print_stock_report(item):

    ticker = item["ticker"]

    print()

    print("=" * 75)

    print(
        f"{BOLD}{CYAN}"
        f"{ticker} — {item['name']}"
        f"{Fore.RESET}"
    )

    print("=" * 75)

    print(
        f"Sector: "
        f"{item['sector']}"
    )

    # =====================================================
    # OVERALL SCORE
    # =====================================================

    print()

    print(
        f"{BOLD}Overall Score:{Fore.RESET} "
        f"{colour_score(item['score'])}"
    )

    print(
        f"Verdict: "
        f"{item['model']['verdict']}"
    )

    # =====================================================
    # ACTION
    # =====================================================

    action, explanation = (
        get_action_and_reason(item)
    )

    if action == "BUY":

        action_display = (
            f"{GREEN}{BOLD}"
            f"BUY"
            f"{Fore.RESET}"
        )

    elif action == "HOLD":

        action_display = (
            f"{AMBER}{BOLD}"
            f"HOLD"
            f"{Fore.RESET}"
        )

    else:

        action_display = (
            f"{RED}{BOLD}"
            f"SELL"
            f"{Fore.RESET}"
        )

    print()

    print(
        f"Analyst Model Action: "
        f"{action_display}"
    )

    print(
        f"Reason: "
        f"{explanation}"
    )

    # =====================================================
    # MARKET DATA
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"MARKET DATA"
        f"{Fore.RESET}"
    )

    market = item["market"]

    print(
        f"Current Price: "
        f"{format_number(market['current_price'])}"
    )

    print(
        f"Previous Close: "
        f"{format_number(market['previous_close'])}"
    )

    print(
        f"Day Range: "
        f"{format_number(market['day_low'])}"
        f" - "
        f"{format_number(market['day_high'])}"
    )

    print(
        f"52 Week Range: "
        f"{format_number(market['fifty_two_week_low'])}"
        f" - "
        f"{format_number(market['fifty_two_week_high'])}"
    )

    position = market[
        "fifty_two_week_position"
    ]

    if position is not None:

        if position >= 75:
            position_display = (
                f"{GREEN}{position:.1f}%"
                f"{Fore.RESET}"
            )

        elif position >= 50:
            position_display = (
                f"{AMBER}{position:.1f}%"
                f"{Fore.RESET}"
            )

        else:
            position_display = (
                f"{RED}{position:.1f}%"
                f"{Fore.RESET}"
            )

        print(
            f"52 Week Position: "
            f"{position_display}"
        )

    else:

        print(
            "52 Week Position: N/A"
        )

    print(
        f"Market Cap: "
        f"{format_large_number("
            f"market['market_cap']"
        f")}"
    )

    print(
        f"Enterprise Value: "
        f"{format_large_number("
            f"market['enterprise_value']"
        f")}"
    )

    # =====================================================
    # BUSINESS QUALITY
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"BUSINESS QUALITY"
        f"{Fore.RESET}"
    )

    print(
        f"Quality: "
        f"{colour_quality("
            f"item['model']['quality']"
        f")}"
    )

    print(
        f"Quality Score: "
        f"{item['model']['quality_score']}/6"
    )

    print(
        f"Growth: "
        f"{item['model']['growth']:.1f}%"
    )

    fundamentals = item[
        "fundamentals"
    ]

    print(
        f"Revenue Growth: "
        f"{format_percentage("
            f"fundamentals['revenue_growth']"
        f")}"
    )

    print(
        f"Earnings Growth: "
        f"{format_percentage("
            f"fundamentals['earnings_growth']"
        f")}"
    )

    print(
        f"Profit Margin: "
        f"{format_percentage("
            f"fundamentals['profit_margin'] * 100 "
            f"if fundamentals['profit_margin'] "
            f"is not None else None"
        )}"
    )

    print(
        f"Operating Margin: "
        f"{format_percentage("
            f"fundamentals['operating_margin'] * 100 "
            f"if fundamentals['operating_margin'] "
            f"is not None else None"
        )}"
    )

    print(
        f"ROE: "
        f"{format_percentage("
            f"fundamentals['return_on_equity'] * 100 "
            f"if fundamentals['return_on_equity'] "
            f"is not None else None"
        )}"
    )

    print(
        f"ROA: "
        f"{format_percentage("
            f"fundamentals['return_on_assets'] * 100 "
            f"if fundamentals['return_on_assets'] "
            f"is not None else None"
        )}"
    )

    print(
        f"Debt to Equity: "
        f"{format_number("
            f"fundamentals['debt_to_equity']"
        f")}"
    )

    print(
        f"Current Ratio: "
        f"{format_number("
            f"fundamentals['current_ratio']"
        f")}"
    )

    print(
        f"Free Cash Flow: "
        f"{format_large_number("
            f"fundamentals['free_cash_flow']"
        f")}"
    )

    # =====================================================
    # VALUATION
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"VALUATION"
        f"{Fore.RESET}"
    )

    print(
        f"Assessment: "
        f"{colour_valuation("
            f"item['valuation']"
        f")}"
    )

    valuation_data = item[
        "valuation_data"
    ]

    print(
        f"Trailing P/E: "
        f"{format_number("
            f"valuation_data['trailing_pe']"
        f")}"
    )

    print(
        f"Forward P/E: "
        f"{format_number("
            f"valuation_data['forward_pe']"
        f")}"
    )

    print(
        f"PEG Ratio: "
        f"{format_number("
            f"valuation_data['peg_ratio']"
        f")}"
    )

    print(
        f"Price to Book: "
        f"{format_number("
            f"valuation_data['price_to_book']"
        f")}"
    )

    print(
        f"Price to Sales: "
        f"{format_number("
            f"valuation_data['price_to_sales']"
        f")}"
    )

    print(
        f"EV/Revenue: "
        f"{format_number("
            f"valuation_data['enterprise_to_revenue']"
        f")}"
    )

    print(
        f"EV/EBITDA: "
        f"{format_number("
            f"valuation_data['enterprise_to_ebitda']"
        f")}"
    )

    # =====================================================
    # EARNINGS
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"EARNINGS"
        f"{Fore.RESET}"
    )

    earnings = item["earnings"]

    earnings_date = earnings[
        "date"
    ]

    if earnings_date:

        print(
            f"Next Earnings Date: "
            f"{earnings_date.strftime('%d %b %Y')}"
        )

    else:

        print(
            "Next Earnings Date: N/A"
        )

    print(
        f"Forward EPS: "
        f"{format_number("
            f"earnings['forward_eps']"
        f")}"
    )

    print(
        f"Trailing EPS: "
        f"{format_number("
            f"earnings['trailing_eps']"
        f")}"
    )

    # =====================================================
    # ANALYST CONSENSUS
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"ANALYST CONSENSUS"
        f"{Fore.RESET}"
    )

    consensus = item[
        "analyst_consensus"
    ]

    if consensus in [
        "STRONG BUY",
        "BUY"
    ]:

        consensus_display = (
            f"{GREEN}{consensus}"
            f"{Fore.RESET}"
        )

    elif consensus in [
        "SELL",
        "STRONG SELL"
    ]:

        consensus_display = (
            f"{RED}{consensus}"
            f"{Fore.RESET}"
        )

    elif consensus == "HOLD":

        consensus_display = (
            f"{AMBER}{consensus}"
            f"{Fore.RESET}"
        )

    else:

        consensus_display = consensus

    print(
        f"Consensus: "
        f"{consensus_display}"
    )

    if item["analyst_count"] is not None:

        print(
            f"Analyst Count: "
            f"{item['analyst_count']}"
        )

    if item["target_mean_price"] is not None:

        print(
            f"Average Target: "
            f"{format_number("
                f"item['target_mean_price']"
            f")}"
        )

    if market["current_price"] is not None:

        print(
            f"Current Price: "
            f"{format_number("
                f"market['current_price']"
            f")}"
        )

    print(
        f"Target Upside: "
        f"{colour_upside("
            f"item['target_upside']"
        f")}"
    )

    if item["target_high_price"] is not None:

        print(
            f"High Target: "
            f"{format_number("
                f"item['target_high_price']"
            f")}"
        )

    if item["target_low_price"] is not None:

        print(
            f"Low Target: "
            f"{format_number("
                f"item['target_low_price']"
            f")}"
        )

    # =====================================================
    # RISK
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"RISK"
        f"{Fore.RESET}"
    )

    print(
        f"Risk Assessment: "
        f"{colour_risk(item['risk'])}"
    )

    beta = safe_float(
        item["info"].get("beta")
    )

    if beta is not None:

        print(
            f"Beta: "
            f"{beta:.2f}"
        )

    # =====================================================
    # CATALYSTS
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"CATALYSTS"
        f"{Fore.RESET}"
    )

    print(
        f"Catalyst Strength: "
        f"{colour_catalyst("
            f"item['model']['catalyst_strength']"
        f")}"
    )

    # =====================================================
    # RECENT NEWS
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"RECENT NEWS"
        f"{Fore.RESET}"
    )

    if not item["news"]:

        print(
            "- No recent news found"
        )

    else:

        for index, news in enumerate(
            item["news"],
            start=1
        ):

            sentiment = (
                colour_sentiment(
                    news["sentiment"]
                )
            )

            print()

            print(
                f"{index}. "
                f"{news['title']}"
            )

            print(
                f" Sentiment: "
                f"{sentiment}"
            )

            print(
                f" Summary: "
                f"{news['summary']}"
            )

    # =====================================================
    # NEWS OVERALL
    # =====================================================

    print()

    print(
        f"Overall News Sentiment: "
        f"{colour_sentiment("
            f"item['overall_news_sentiment']"
        f")}"
    )

    # =====================================================
    # KEY NEXT DATES
    # =====================================================

    print()

    print(
        f"{CYAN}{BOLD}"
        f"KEY NEXT DATES"
        f"{Fore.RESET}"
    )

    future_events = [
        event
        for event in item["events"]
        if event["date"] >= date.today()
    ]

    future_events.sort(
        key=lambda x:
        (
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
                timing = (
                    f"in {days} days"
                )

            event_colour = (
                get_event_colour(
                    event["type"]
                )
            )

            print(
                f"{event['date'].strftime('%d %b %Y')}"
                f" — "
                f"{event_colour}"
                f"{event['type']}"
                f"{Fore.RESET}"
                f" ({timing})"
            )

    else:

        print(
            "No upcoming dates found."
        )


# =========================================================
# MAIN REPORT
# =========================================================

def generate_report(portfolio):

    print()

    print(
        f"{CYAN}{BOLD}"
        "========================================================"
        f"{Fore.RESET}"
    )

    print(
        f"{CYAN}{BOLD}"
        " INVESTMENT ANALYST REPORT"
        f"{Fore.RESET}"
    )

    print(
        f"{CYAN}{BOLD}"
        "========================================================"
        f"{Fore.RESET}"
    )

    print()

    # -----------------------------------------------------
    # CLEAN USER PORTFOLIO
    # -----------------------------------------------------

    if isinstance(
        portfolio,
        str
    ):

        portfolio = [
            ticker.strip().upper()
            for ticker in portfolio.split(",")
            if ticker.strip()
        ]

    else:

        portfolio = [
            str(ticker).strip().upper()
            for ticker in portfolio
            if str(ticker).strip()
        ]

    # Remove duplicates while
    # preserving order

    portfolio = list(
        dict.fromkeys(
            portfolio
        )
    )

    if not portfolio:

        print(
            f"{RED}"
            "No stocks selected."
            f"{Fore.RESET}"
        )

        return []

    # -----------------------------------------------------
    # ANALYSE
    # -----------------------------------------------------

    results = []

    for ticker in portfolio:

        result = analyse_stock(
            ticker
        )

        if result:

            results.append(
                result
            )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    print_summary(
        results
    )

    # -----------------------------------------------------
    # DETAILED REPORTS
    # -----------------------------------------------------

    for item in results:

        print_stock_report(
            item
        )

    # -----------------------------------------------------
    # END
    # -----------------------------------------------------

    print()

    print(
        f"{CYAN}{BOLD}"
        "========================================================"
        f"{Fore.RESET}"
    )

    print(
        f"{CYAN}{BOLD}"
        " END OF REPORT"
        f"{Fore.RESET}"
    )

    print(
        f"{CYAN}{BOLD}"
        "========================================================"
        f"{Fore.RESET}"
    )

    print()

    # Returning results is important
    # for the Streamlit app.

    return results


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    # This fallback is only for running
    # main.py directly from the command line.
    #
    # The Streamlit app will pass its
    # own portfolio into generate_report().

    default_portfolio = [
        "NVDA",
        "AAPL",
        "MSFT"
    ]

    generate_report(
        default_portfolio
    )
```
