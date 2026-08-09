import yfinance as yf
from datetime import datetime, date
import math


# =========================================================
# GENERAL HELPERS
# =========================================================

def safe_get(info, key, default=None):
    """Safely retrieve a value from a yfinance info dictionary."""
    if not info:
        return default

    try:
        value = info.get(key, default)

        if value is None:
            return default

        return value

    except Exception:
        return default


def clean_number(value):
    """Return None for invalid numeric values."""
    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except Exception:
        return None


def percentage(value):
    """Convert decimal percentage to percentage points."""
    value = clean_number(value)

    if value is None:
        return None

    return value * 100


def format_number(value, decimals=2):
    value = clean_number(value)

    if value is None:
        return "N/A"

    return f"{value:,.{decimals}f}"


def format_large_number(value):
    value = clean_number(value)

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

    return f"{value:,.0f}"


def clean_ticker(ticker):
    """Clean and standardise ticker input."""
    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    return ticker if ticker else None


# =========================================================
# NEWS SENTIMENT
# =========================================================

POSITIVE_NEWS_WORDS = [
    "growth",
    "profit",
    "profits",
    "beat",
    "beats",
    "upgrade",
    "upgraded",
    "surge",
    "surges",
    "record",
    "strong",
    "raises",
    "raised",
    "positive",
    "contract",
    "deal",
    "partnership",
    "launch",
    "launches",
    "expands",
    "expansion",
    "orders",
    "approval",
    "approved",
    "breakthrough",
    "bullish",
    "outperform",
    "recovery",
    "rebound",
    "demand",
    "guidance",
]

NEGATIVE_NEWS_WORDS = [
    "loss",
    "losses",
    "miss",
    "misses",
    "downgrade",
    "downgraded",
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
    "risks",
    "underperform",
    "recall",
    "disappointing",
    "disappoints",
]


def get_news_sentiment(title):
    if not title:
        return "NEUTRAL"

    text = str(title).lower()

    positive_score = sum(
        1 for word in POSITIVE_NEWS_WORDS
        if word in text
    )

    negative_score = sum(
        1 for word in NEGATIVE_NEWS_WORDS
        if word in text
    )

    if positive_score > negative_score:
        return "POSITIVE"

    if negative_score > positive_score:
        return "NEGATIVE"

    return "NEUTRAL"


def create_news_summary(title, summary=None):
    """
    Use Yahoo's supplied summary where available.
    Otherwise provide a shortened headline.
    """

    if summary:
        summary = str(summary).strip()

        if summary:
            if len(summary) > 300:
                return summary[:297] + "..."

            return summary

    if not title:
        return "No summary available."

    title = str(title).strip()

    if len(title) > 220:
        return title[:217] + "..."

    return title


def extract_news_item(item):
    """
    yfinance/Yahoo news formats have changed over time.
    Support both older and newer structures.
    """

    content = item.get("content", {}) if isinstance(item, dict) else {}

    if not isinstance(content, dict):
        content = {}

    title = (
        content.get("title")
        or item.get("title")
        or "No title available"
    )

    summary = (
        content.get("summary")
        or item.get("summary")
        or content.get("description")
        or item.get("description")
        or ""
    )

    publisher = (
        content.get("provider", {}).get("displayName")
        if isinstance(content.get("provider"), dict)
        else None
    )

    if not publisher:
        publisher = item.get("publisher")

    link = (
        content.get("canonicalUrl", {}).get("url")
        if isinstance(content.get("canonicalUrl"), dict)
        else None
    )

    if not link:
        link = item.get("link")

    sentiment = get_news_sentiment(title)

    return {
        "title": title,
        "summary": create_news_summary(title, summary),
        "sentiment": sentiment,
        "publisher": publisher or "Unknown",
        "link": link,
    }


# =========================================================
# ANALYST CONSENSUS
# =========================================================

def get_analyst_consensus(info):
    recommendation = safe_get(info, "recommendationKey")

    if not recommendation:
        return "N/A"

    recommendation = str(recommendation).lower().strip()

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
        "strong sell": "STRONG SELL",
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
    """
    Valuation uses PEG where available, then forward P/E,
    then trailing P/E.

    This is deliberately not based on P/E alone because
    high-growth companies can look expensive on P/E while
    still having attractive growth-adjusted valuations.
    """

    forward_pe = clean_number(
        safe_get(info, "forwardPE")
    )

    trailing_pe = clean_number(
        safe_get(info, "trailingPE")
    )

    peg = clean_number(
        safe_get(info, "pegRatio")
    )

    # PEG has priority when available.
    if peg is not None:

        if peg < 1:
            return "ATTRACTIVE"

        if peg > 2:
            return "EXPENSIVE"

        return "FAIR"

    pe = forward_pe or trailing_pe

    if pe is not None:

        if pe < 20:
            return "ATTRACTIVE"

        if pe > 40:
            return "EXPENSIVE"

        return "FAIR"

    return "N/A"


# =========================================================
# BUSINESS QUALITY
# =========================================================

def get_business_quality(info):
    """
    Business quality considers:
    - ROE
    - Profit margin
    - Operating margin
    """

    roe = clean_number(
        safe_get(info, "returnOnEquity")
    )

    profit_margin = clean_number(
        safe_get(info, "profitMargins")
    )

    operating_margin = clean_number(
        safe_get(info, "operatingMargins")
    )

    score = 0

    # ROE
    if roe is not None:

        if roe >= 0.20:
            score += 2

        elif roe >= 0.10:
            score += 1

    # Profit margin
    if profit_margin is not None:

        if profit_margin >= 0.15:
            score += 2

        elif profit_margin > 0:
            score += 1

    # Operating margin
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
    """
    Average available revenue and earnings growth.
    """

    revenue_growth = clean_number(
        safe_get(info, "revenueGrowth")
    )

    earnings_growth = clean_number(
        safe_get(info, "earningsGrowth")
    )

    values = []

    if revenue_growth is not None:
        values.append(revenue_growth)

    if earnings_growth is not None:
        values.append(earnings_growth)

    if not values:
        return 0.0

    return sum(values) / len(values) * 100


# =========================================================
# RISK
# =========================================================

def get_risk(info, growth):
    beta = clean_number(
        safe_get(info, "beta")
    )

    profit_margin = clean_number(
        safe_get(info, "profitMargins")
    )

    debt_to_equity = clean_number(
        safe_get(info, "debtToEquity")
    )

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

    earnings_date = safe_get(
        info,
        "earningsTimestamp"
    )

    if earnings_date:
        score += 1

    recommendation = str(
        safe_get(info, "recommendationKey", "")
    ).lower()

    if recommendation in [
        "strong_buy",
        "buy",
        "outperform",
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
    # Earnings timestamp
    # -----------------------------------------------------

    earnings_timestamp = safe_get(
        info,
        "earningsTimestamp"
    )

    if earnings_timestamp:

        try:
            event_date = datetime.fromtimestamp(
                earnings_timestamp
            ).date()

            events.append({
                "date": event_date,
                "type": "EARNINGS",
                "priority": 1,
            })

        except Exception:
            pass

    # -----------------------------------------------------
    # Dividend
    # -----------------------------------------------------

    ex_dividend = safe_get(
        info,
        "exDividendDate"
    )

    if ex_dividend:

        try:
            event_date = datetime.fromtimestamp(
                ex_dividend
            ).date()

            events.append({
                "date": event_date,
                "type": "DIVIDEND",
                "priority": 3,
            })

        except Exception:
            pass

    # -----------------------------------------------------
    # Yahoo calendar
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

                    if not isinstance(
                        earnings_dates,
                        list
                    ):
                        earnings_dates = [
                            earnings_dates
                        ]

                    for event_date in earnings_dates:

                        try:

                            if hasattr(
                                event_date,
                                "date"
                            ):
                                event_date = event_date.date()

                            if isinstance(
                                event_date,
                                date
                            ):
                                events.append({
                                    "date": event_date,
                                    "type": "EARNINGS",
                                    "priority": 1,
                                })

                        except Exception:
                            pass

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

    unique.sort(
        key=lambda x: (
            x["date"],
            x["priority"]
        )
    )

    return unique


# =========================================================
# EARNINGS DATA
# =========================================================

def get_earnings_data(stock, info):
    """
    Collect available earnings information.
    """

    data = {
        "next_earnings_date": None,
        "eps_estimate": None,
        "eps_actual": None,
        "eps_surprise_pct": None,
        "revenue_estimate": None,
        "revenue_actual": None,
        "earnings_growth": percentage(
            safe_get(info, "earningsGrowth")
        ),
        "quarterly_earnings_growth": percentage(
            safe_get(
                info,
                "earningsQuarterlyGrowth"
            )
        ),
    }

    # -----------------------------------------------------
    # Next earnings date
    # -----------------------------------------------------

    earnings_timestamp = safe_get(
        info,
        "earningsTimestamp"
    )

    if earnings_timestamp:

        try:
            data["next_earnings_date"] = (
                datetime.fromtimestamp(
                    earnings_timestamp
                ).date()
            )

        except Exception:
            pass

    # -----------------------------------------------------
    # Earnings estimate dictionaries
    # -----------------------------------------------------

    try:

        earnings_estimate = getattr(
            stock,
            "earnings_estimate",
            None
        )

        if earnings_estimate is not None:

            if hasattr(
                earnings_estimate,
                "to_dict"
            ):

                estimate_dict = (
                    earnings_estimate.to_dict()
                )

                # Try common structures.
                for period, values in estimate_dict.items():

                    if not isinstance(values, dict):
                        continue

                    if data["eps_estimate"] is None:

                        eps_value = (
                            values.get("avg")
                            or values.get("epsAvg")
                            or values.get("eps")
                        )

                        eps_value = clean_number(
                            eps_value
                        )

                        if eps_value is not None:
                            data["eps_estimate"] = eps_value

                    if data["revenue_estimate"] is None:

                        revenue_value = (
                            values.get("revenueAvg")
                            or values.get("revenue")
                        )

                        revenue_value = clean_number(
                            revenue_value
                        )

                        if revenue_value is not None:
                            data[
                                "revenue_estimate"
                            ] = revenue_value

    except Exception:
        pass

    # -----------------------------------------------------
    # Earnings dates
    # -----------------------------------------------------

    try:

        earnings_dates = (
            stock.get_earnings_dates(
                limit=8
            )
        )

        if earnings_dates is not None:

            # Try to identify the most recent
            # reported EPS information.
            for index, row in earnings_dates.iterrows():

                try:

                    eps_estimate = (
                        row.get(
                            "EPS Estimate"
                        )
                    )

                    eps_actual = (
                        row.get(
                            "Reported EPS"
                        )
                    )

                    surprise = (
                        row.get(
                            "Surprise(%)"
                        )
                    )

                    if eps_estimate is not None:
                        data[
                            "eps_estimate"
                        ] = clean_number(
                            eps_estimate
                        )

                    if eps_actual is not None:
                        data[
                            "eps_actual"
                        ] = clean_number(
                            eps_actual
                        )

                    if surprise is not None:
                        data[
                            "eps_surprise_pct"
                        ] = clean_number(
                            surprise
                        )

                    # First useful row only.
                    if (
                        data["eps_actual"]
                        is not None
                        or data["eps_estimate"]
                        is not None
                    ):
                        break

                except Exception:
                    continue

    except Exception:
        pass

    return data


# =========================================================
# MARKET DATA
# =========================================================

def get_market_data(info):
    current_price = clean_number(
        safe_get(info, "currentPrice")
    )

    if current_price is None:

        current_price = clean_number(
            safe_get(info, "regularMarketPrice")
        )

    previous_close = clean_number(
        safe_get(info, "previousClose")
    )

    fifty_two_week_high = clean_number(
        safe_get(info, "fiftyTwoWeekHigh")
    )

    fifty_two_week_low = clean_number(
        safe_get(info, "fiftyTwoWeekLow")
    )

    fifty_two_week_position = None
    distance_from_high = None
    distance_from_low = None

    if (
        current_price is not None
        and fifty_two_week_high is not None
        and fifty_two_week_low is not None
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
            * 100
        )

        distance_from_high = (
            (
                current_price
                /
                fifty_two_week_high
            ) - 1
        ) * 100

        distance_from_low = (
            (
                current_price
                /
                fifty_two_week_low
            ) - 1
        ) * 100

    return {
        "current_price": current_price,
        "previous_close": previous_close,
        "market_cap": clean_number(
            safe_get(info, "marketCap")
        ),
        "enterprise_value": clean_number(
            safe_get(info, "enterpriseValue")
        ),
        "volume": clean_number(
            safe_get(info, "volume")
        ),
        "average_volume": clean_number(
            safe_get(info, "averageVolume")
        ),
        "fifty_two_week_high": fifty_two_week_high,
        "fifty_two_week_low": fifty_two_week_low,
        "fifty_two_week_position": fifty_two_week_position,
        "distance_from_52_week_high": distance_from_high,
        "distance_from_52_week_low": distance_from_low,
        "beta": clean_number(
            safe_get(info, "beta")
        ),
    }


# =========================================================
# FUNDAMENTALS
# =========================================================

def get_fundamentals(info):
    return {
        "revenue": clean_number(
            safe_get(info, "totalRevenue")
        ),
        "gross_profit": clean_number(
            safe_get(info, "grossProfits")
        ),
        "operating_income": clean_number(
            safe_get(info, "operatingIncome")
        ),
        "net_income": clean_number(
            safe_get(info, "netIncomeToCommon")
        ),
        "free_cash_flow": clean_number(
            safe_get(info, "freeCashflow")
        ),
        "operating_cash_flow": clean_number(
            safe_get(info, "operatingCashflow")
        ),
        "return_on_equity": percentage(
            safe_get(info, "returnOnEquity")
        ),
        "return_on_assets": percentage(
            safe_get(info, "returnOnAssets")
        ),
        "profit_margin": percentage(
            safe_get(info, "profitMargins")
        ),
        "operating_margin": percentage(
            safe_get(info, "operatingMargins")
        ),
        "gross_margin": percentage(
            safe_get(info, "grossMargins")
        ),
        "ebitda_margin": percentage(
            safe_get(info, "ebitdaMargins")
        ),
        "revenue_growth": percentage(
            safe_get(info, "revenueGrowth")
        ),
        "earnings_growth": percentage(
            safe_get(info, "earningsGrowth")
        ),
        "debt_to_equity": clean_number(
            safe_get(info, "debtToEquity")
        ),
        "current_ratio": clean_number(
            safe_get(info, "currentRatio")
        ),
        "quick_ratio": clean_number(
            safe_get(info, "quickRatio")
        ),
        "total_cash": clean_number(
            safe_get(info, "totalCash")
        ),
        "total_debt": clean_number(
            safe_get(info, "totalDebt")
        ),
    }


# =========================================================
# VALUATION DATA
# =========================================================

def get_valuation_data(info):
    return {
        "assessment": get_valuation(info),
        "forward_pe": clean_number(
            safe_get(info, "forwardPE")
        ),
        "trailing_pe": clean_number(
            safe_get(info, "trailingPE")
        ),
        "peg_ratio": clean_number(
            safe_get(info, "pegRatio")
        ),
        "price_to_book": clean_number(
            safe_get(info, "priceToBook")
        ),
        "price_to_sales": clean_number(
            safe_get(info, "priceToSalesTrailing12Months")
        ),
        "enterprise_to_revenue": clean_number(
            safe_get(info, "enterpriseToRevenue")
        ),
        "enterprise_to_ebitda": clean_number(
            safe_get(info, "enterpriseToEbitda")
        ),
    }


# =========================================================
# ANALYST DATA
# =========================================================

def get_analyst_data(info):
    consensus = get_analyst_consensus(info)

    current_price = clean_number(
        safe_get(info, "currentPrice")
        or safe_get(info, "regularMarketPrice")
    )

    target_mean = clean_number(
        safe_get(info, "targetMeanPrice")
    )

    target_high = clean_number(
        safe_get(info, "targetHighPrice")
    )

    target_low = clean_number(
        safe_get(info, "targetLowPrice")
    )

    target_median = clean_number(
        safe_get(info, "targetMedianPrice")
    )

    target_upside = None

    if (
        target_mean is not None
        and current_price is not None
        and current_price != 0
    ):
        target_upside = (
            target_mean
            /
            current_price
            - 1
        ) * 100

    return {
        "consensus": consensus,
        "analyst_count": safe_get(
            info,
            "numberOfAnalystOpinions"
        ),
        "target_mean": target_mean,
        "target_median": target_median,
        "target_high": target_high,
        "target_low": target_low,
        "target_upside": target_upside,
    }


# =========================================================
# SCORING MODEL
# =========================================================

def calculate_score(
    valuation,
    quality,
    quality_score,
    growth,
    analyst_consensus,
    risk,
    catalyst_strength,
    news_sentiment,
):
    """
    Multi-factor investment score.

    Starting point: 50

    Business quality: +/- 15
    Growth: +/- 15
    Valuation: +/- 10
    Analysts: +/- 8
    Catalysts: +/- 5
    News: +/- 4
    Risk: +/- 15

    Analyst consensus is deliberately one factor rather
    than the entire decision. This prevents a good company
    from automatically becoming a SELL simply because
    analysts are cautious.
    """

    score = 50

    # -----------------------------------------------------
    # BUSINESS QUALITY
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
    # GROWTH
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
    # VALUATION
    # -----------------------------------------------------

    if valuation == "ATTRACTIVE":
        score += 10

    elif valuation == "EXPENSIVE":
        score -= 10

    # -----------------------------------------------------
    # ANALYST CONSENSUS
    # -----------------------------------------------------

    if analyst_consensus == "STRONG BUY":
        score += 8

    elif analyst_consensus == "BUY":
        score += 5

    elif analyst_consensus == "SELL":
        score -= 5

    elif analyst_consensus == "STRONG SELL":
        score -= 8

    # HOLD / N/A deliberately receive no penalty.

    # -----------------------------------------------------
    # CATALYSTS
    # -----------------------------------------------------

    if catalyst_strength == "STRONG":
        score += 5

    elif catalyst_strength == "WEAK":
        score -= 2

    # -----------------------------------------------------
    # NEWS
    # -----------------------------------------------------

    if news_sentiment == "POSITIVE":
        score += 4

    elif news_sentiment == "NEGATIVE":
        score -= 4

    # -----------------------------------------------------
    # RISK
    # -----------------------------------------------------

    if risk == "VERY HIGH":
        score -= 15

    elif risk == "HIGH":
        score -= 8

    elif risk == "LOW":
        score += 3

    return max(
        0,
        min(100, round(score))
    )


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
    analyst_consensus = item["analyst_consensus"]
    sentiment = item.get(
        "overall_news_sentiment",
        "NEUTRAL"
    )

    reasons = []

    # -----------------------------------------------------
    # QUALITY
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
    # GROWTH
    # -----------------------------------------------------

    if growth >= 17:
        reasons.append("strong growth")

    elif growth >= 10:
        reasons.append("healthy growth")

    elif growth < 0:
        reasons.append("declining growth")

    elif growth <= 5:
        reasons.append("limited growth")

    # -----------------------------------------------------
    # VALUATION
    # -----------------------------------------------------

    if valuation == "ATTRACTIVE":
        reasons.append("attractive valuation")

    elif valuation == "EXPENSIVE":
        reasons.append("expensive valuation")

    elif valuation == "FAIR":
        reasons.append("fair valuation")

    # -----------------------------------------------------
    # ANALYSTS
    # -----------------------------------------------------

    analyst_text = get_analyst_text(
        item["info"]
    )

    if analyst_text:
        reasons.append(analyst_text)

    # -----------------------------------------------------
    # CATALYSTS
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
    # RISK
    # -----------------------------------------------------

    if risk == "VERY HIGH":
        reasons.append("very high risk")

    elif risk == "HIGH":
        reasons.append("high risk")

    elif risk == "LOW":
        reasons.append("relatively low risk")

    # -----------------------------------------------------
    # NEWS
    # -----------------------------------------------------

    if sentiment == "POSITIVE":
        reasons.append("positive recent news")

    elif sentiment == "NEGATIVE":
        reasons.append("negative recent news")

    # -----------------------------------------------------
    # ACTION
    #
    # Important:
    # The action is NOT simply analyst consensus.
    # It is based on the complete score and risk.
    # -----------------------------------------------------

    if (
        score >= 70
        and risk not in [
            "HIGH",
            "VERY HIGH",
        ]
    ):
        action = "BUY"

    elif score >= 50:
        action = "HOLD"

    else:
        action = "SELL"

    # -----------------------------------------------------
    # PRIORITISED REASONS
    # -----------------------------------------------------

    if action == "BUY":

        priority = [
            "attractive valuation",
            "strong growth",
            "healthy growth",
            "exceptional business quality",
            "strong business quality",
            "positive analyst consensus",
            "strong analyst consensus",
            "strong upcoming catalysts",
            "positive recent news",
            "relatively low risk",
            "fair valuation",
        ]

    elif action == "HOLD":

        priority = [
            "exceptional business quality",
            "strong business quality",
            "strong growth",
            "healthy growth",
            "attractive valuation",
            "fair valuation",
            "positive analyst consensus",
            "neutral analyst consensus",
            "expensive valuation",
            "high risk",
            "strong upcoming catalysts",
            "negative recent news",
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
            "negative recent news",
        ]

    selected = []

    for reason in priority:

        if reason in reasons:

            selected.append(reason)

        if len(selected) >= 3:
            break

    if not selected:
        selected = reasons[:3]

    # -----------------------------------------------------
    # CREATE NATURAL SENTENCE
    # -----------------------------------------------------

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

    elif len(selected) >= 3:

        explanation = (
            selected[0].capitalize()
            + ", "
            + selected[1]
            + ", with "
            + selected[2]
            + "."
        )

    else:

        explanation = (
            "Mixed signals across the investment model."
        )

    return action, explanation


# =========================================================
# NEWS
# =========================================================

def get_news(stock):
    news_items = []

    try:

        raw_news = stock.news

        if not raw_news:
            return news_items

        for item in raw_news[:5]:

            if not isinstance(item, dict):
                continue

            news_items.append(
                extract_news_item(item)
            )

    except Exception:
        pass

    return news_items


def get_overall_news_sentiment(news_items):
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

    if positive > negative:
        return "POSITIVE"

    if negative > positive:
        return "NEGATIVE"

    return "NEUTRAL"


# =========================================================
# STOCK ANALYSIS
# =========================================================

def analyse_stock(ticker):
    ticker = clean_ticker(ticker)

    if not ticker:
        return None

    try:

        stock = yf.Ticker(ticker)

        info = stock.info

        if not info:
            return {
                "ticker": ticker,
                "error": "No market data returned.",
            }

        # -------------------------------------------------
        # BASIC COMPANY INFORMATION
        # -------------------------------------------------

        name = safe_get(
            info,
            "longName",
            ticker
        )

        short_name = safe_get(
            info,
            "shortName",
            name
        )

        sector = safe_get(
            info,
            "sector",
            "N/A"
        )

        industry = safe_get(
            info,
            "industry",
            "N/A"
        )

        country = safe_get(
            info,
            "country",
            "N/A"
        )

        # -------------------------------------------------
        # MARKET DATA
        # -------------------------------------------------

        market_data = get_market_data(
            info
        )

        # -------------------------------------------------
        # NEWS
        # -------------------------------------------------

        news_items = get_news(
            stock
        )

        overall_news_sentiment = (
            get_overall_news_sentiment(
                news_items
            )
        )

        # -------------------------------------------------
        # FUNDAMENTALS
        # -------------------------------------------------

        fundamentals = get_fundamentals(
            info
        )

        # -------------------------------------------------
        # VALUATION
        # -------------------------------------------------

        valuation_data = get_valuation_data(
            info
        )

        valuation = valuation_data[
            "assessment"
        ]

        # -------------------------------------------------
        # BUSINESS QUALITY
        # -------------------------------------------------

        quality, quality_score = (
            get_business_quality(info)
        )

        # -------------------------------------------------
        # GROWTH
        # -------------------------------------------------

        growth = get_growth(info)

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        risk = get_risk(
            info,
            growth
        )

        # -------------------------------------------------
        # ANALYSTS
        # -------------------------------------------------

        analyst_data = get_analyst_data(
            info
        )

        analyst_consensus = (
            analyst_data["consensus"]
        )

        # -------------------------------------------------
        # CATALYST
        # -------------------------------------------------

        catalyst_strength = (
            get_catalyst_strength(info)
        )

        catalyst_score = (
            2
            if catalyst_strength == "STRONG"
            else
            1
            if catalyst_strength == "MODERATE"
            else
            0
        )

        # -------------------------------------------------
        # EARNINGS
        # -------------------------------------------------

        earnings = get_earnings_data(
            stock,
            info
        )

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        score = calculate_score(
            valuation=valuation,
            quality=quality,
            quality_score=quality_score,
            growth=growth,
            analyst_consensus=analyst_consensus,
            risk=risk,
            catalyst_strength=catalyst_strength,
            news_sentiment=overall_news_sentiment,
        )

        verdict = get_verdict(
            score
        )

        # -------------------------------------------------
        # KEY EVENTS
        # -------------------------------------------------

        key_events = get_events(
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
            "valuation": valuation,
            "catalyst": catalyst_score,
            "catalyst_strength": catalyst_strength,
            "verdict": verdict,
        }

        # -------------------------------------------------
        # COMPLETE RESULT
        # -------------------------------------------------

        result = {
            "ticker": ticker,
            "name": name,
            "short_name": short_name,
            "sector": sector,
            "industry": industry,
            "country": country,
            "info": info,

            # Market
            "market_data": market_data,

            # Convenient direct access
            "price": market_data[
                "current_price"
            ],

            "market_cap": market_data[
                "market_cap"
            ],

            "fifty_two_week_position":
                market_data[
                    "fifty_two_week_position"
                ],

            # Fundamentals
            "fundamentals": fundamentals,

            # Valuation
            "valuation": valuation,
            "valuation_data": valuation_data,

            # Analysts
            "analyst_consensus":
                analyst_consensus,

            "analyst_data":
                analyst_data,

            # Earnings
            "earnings": earnings,

            # Risk
            "risk": risk,

            # News
            "news": news_items,

            "sentiments": [
                item["sentiment"]
                for item in news_items
            ],

            "overall_news_sentiment":
                overall_news_sentiment,

            # Events
            "events": key_events,

            # Model
            "model": model,

            "score": score,

            "verdict": verdict,
        }

        # -------------------------------------------------
        # ACTION + REASON
        # -------------------------------------------------

        action, explanation = (
            get_action_and_reason(
                result
            )
        )

        result["action"] = action
        result["reason"] = explanation

        return result

    except Exception as error:

        return {
            "ticker": ticker,
            "error": str(error),
        }


# =========================================================
# REPORT-LEVEL SUMMARY
# =========================================================

def build_report_summary(results):
    valid_results = [
        item
        for item in results
        if not item.get("error")
    ]

    if not valid_results:
        return {
            "best_opportunity": None,
            "highest_risk": None,
            "most_attractive_valuation": None,
            "strongest_business": None,
            "strongest_catalyst": None,
            "overall_news_sentiment": "NEUTRAL",
            "positive_news": 0,
            "neutral_news": 0,
            "negative_news": 0,
            "companies_analysed": 0,
        }

    # -----------------------------------------------------
    # BEST OPPORTUNITY
    # -----------------------------------------------------

    best_opportunity = max(
        valid_results,
        key=lambda x: x["score"]
    )

    # -----------------------------------------------------
    # HIGHEST RISK
    # -----------------------------------------------------

    risk_order = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "VERY HIGH": 4,
    }

    highest_risk = max(
        valid_results,
        key=lambda x: risk_order.get(
            x["risk"],
            0
        )
    )

    # -----------------------------------------------------
    # MOST ATTRACTIVE VALUATION
    # -----------------------------------------------------

    attractive = [
        item
        for item in valid_results
        if item["valuation"]
        == "ATTRACTIVE"
    ]

    if attractive:

        most_attractive = max(
            attractive,
            key=lambda x: x["score"]
        )

    else:

        most_attractive = min(
            valid_results,
            key=lambda x: x["score"]
        )

    # -----------------------------------------------------
    # STRONGEST BUSINESS
    # -----------------------------------------------------

    strongest_business = max(
        valid_results,
        key=lambda x:
            x["model"]["quality_score"]
    )

    # -----------------------------------------------------
    # STRONGEST CATALYST
    # -----------------------------------------------------

    catalyst_results = [
        item
        for item in valid_results
        if item["model"][
            "catalyst_strength"
        ] == "STRONG"
    ]

    if catalyst_results:

        strongest_catalyst = max(
            catalyst_results,
            key=lambda x:
                x["model"]["catalyst"]
        )

    else:

        strongest_catalyst = None

    # -----------------------------------------------------
    # NEWS
    # -----------------------------------------------------

    positive = 0
    neutral = 0
    negative = 0

    for item in valid_results:

        positive += item[
            "sentiments"
        ].count("POSITIVE")

        neutral += item[
            "sentiments"
        ].count("NEUTRAL")

        negative += item[
            "sentiments"
        ].count("NEGATIVE")

    if positive > negative:
        overall_news = "POSITIVE"

    elif negative > positive:
        overall_news = "NEGATIVE"

    else:
        overall_news = "NEUTRAL"

    return {
        "best_opportunity":
            best_opportunity["ticker"],

        "best_opportunity_score":
            best_opportunity["score"],

        "highest_risk":
            highest_risk["ticker"],

        "highest_risk_level":
            highest_risk["risk"],

        "most_attractive_valuation":
            most_attractive["ticker"],

        "most_attractive_valuation_label":
            most_attractive["valuation"],

        "strongest_business":
            strongest_business["ticker"],

        "strongest_business_quality":
            strongest_business[
                "model"
            ]["quality"],

        "strongest_catalyst":
            (
                strongest_catalyst["ticker"]
                if strongest_catalyst
                else None
            ),

        "overall_news_sentiment":
            overall_news,

        "positive_news":
            positive,

        "neutral_news":
            neutral,

        "negative_news":
            negative,

        "companies_analysed":
            len(valid_results),
    }


# =========================================================
# REPORT GENERATOR
# =========================================================

def generate_report(portfolio):
    """
    Main function used by Streamlit.

    IMPORTANT:
    This accepts the portfolio supplied by the app.

    It does NOT import portfolio.py.

    Example:

        generate_report(["NVDA", "CCJ", "MSFT"])

    Returns a list of complete stock-analysis dictionaries.
    """

    if portfolio is None:
        return []

    # -----------------------------------------------------
    # Accept either:
    #   ["NVDA", "CCJ"]
    #
    # or:
    #   "NVDA, CCJ"
    # -----------------------------------------------------

    if isinstance(
        portfolio,
        str
    ):

        portfolio = portfolio.split(",")

    cleaned_portfolio = []

    for ticker in portfolio:

        cleaned = clean_ticker(
            ticker
        )

        if (
            cleaned
            and cleaned not in cleaned_portfolio
        ):
            cleaned_portfolio.append(
                cleaned
            )

    if not cleaned_portfolio:
        return []

    # -----------------------------------------------------
    # Analyse each stock
    # -----------------------------------------------------

    results = []

    for ticker in cleaned_portfolio:

        result = analyse_stock(
            ticker
        )

        if result is not None:

            results.append(
                result
            )

    # -----------------------------------------------------
    # Report-level summary
    #
    # Stored on the list itself is not possible,
    # so attach it to each result where useful.
    # The Streamlit app can also calculate its own
    # summary from the returned list.
    # -----------------------------------------------------

    summary = build_report_summary(
        results
    )

    for result in results:

        result["report_summary"] = summary

    return results


# =========================================================
# OPTIONAL COMMAND-LINE TEST
# =========================================================
#
# This does NOT affect Streamlit.
#
# If you run:
#
#     python main.py
#
# it will perform a small test.
#
# Streamlit will simply import generate_report().
# =========================================================

if __name__ == "__main__":

    test_portfolio = [
        "NVDA",
        "CCJ",
    ]

    test_results = generate_report(
        test_portfolio
    )

    print()
    print("=" * 70)
    print("INVESTMENT ANALYST TEST")
    print("=" * 70)

    for item in test_results:

        if item.get("error"):

            print(
                f"{item['ticker']}: "
                f"ERROR - "
                f"{item['error']}"
            )

            continue

        print()
        print(
            f"{item['ticker']} | "
            f"{item['action']} | "
            f"Score: {item['score']}"
        )

        print(
            f"Reason: "
            f"{item['reason']}"
        )

        print(
            f"Price: "
            f"{format_number(item['price'])}"
        )

        print(
            f"Valuation: "
            f"{item['valuation']}"
        )

        print(
            f"Quality: "
            f"{item['model']['quality']}"
        )

        print(
            f"Growth: "
            f"{item['model']['growth']:.1f}%"
        )

        print(
            f"Analysts: "
            f"{item['analyst_consensus']}"
        )

        print(
            f"Risk: "
            f"{item['risk']}"
        )

        position = item[
            "market_data"
        ][
            "fifty_two_week_position"
        ]

        if position is not None:

            print(
                f"52 Week Position: "
                f"{position:.1f}%"
            )

    print()
    print("=" * 70)
