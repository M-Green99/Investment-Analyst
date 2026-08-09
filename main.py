import yfinance as yf
from datetime import datetime, date

# =========================================================
# SAFE HELPERS
# =========================================================
def safe_get(info, key):
    return info.get(key) if info else None


def pct(value):
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def num(value):
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


def large(value):
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    return f"{value:,.0f}"


# =========================================================
# SENTIMENT
# =========================================================
def get_sentiment(text):
    if not text:
        return "NEUTRAL"

    text = text.lower()

    positive = ["growth", "profit", "beat", "strong", "record", "upgrade"]
    negative = ["loss", "miss", "weak", "decline", "risk", "downgrade"]

    pos = sum(1 for w in positive if w in text)
    neg = sum(1 for w in negative if w in text)

    if pos > neg:
        return "POSITIVE"
    elif neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


# =========================================================
# VALUATION
# =========================================================
def get_valuation(info):
    pe = safe_get(info, "forwardPE")

    if pe is None:
        return "FAIR"

    if pe < 20:
        return "ATTRACTIVE"
    elif pe > 40:
        return "EXPENSIVE"
    return "FAIR"


# =========================================================
# GROWTH
# =========================================================
def get_growth(info):
    growth = safe_get(info, "revenueGrowth")
    return growth * 100 if growth else 0


# =========================================================
# RISK
# =========================================================
def get_risk(info):
    beta = safe_get(info, "beta")

    if beta is None:
        return "MODERATE"

    if beta > 1.5:
        return "HIGH"
    return "MODERATE"


# =========================================================
# SCORING
# =========================================================
def score_stock(growth, valuation, risk, sentiment):
    score = 50

    # Growth
    if growth > 20:
        score += 15
    elif growth > 10:
        score += 10
    elif growth < 0:
        score -= 10

    # Valuation
    if valuation == "ATTRACTIVE":
        score += 10
    elif valuation == "EXPENSIVE":
        score -= 10

    # Risk
    if risk == "HIGH":
        score -= 8

    # News
    if sentiment == "POSITIVE":
        score += 5
    elif sentiment == "NEGATIVE":
        score -= 5

    return max(0, min(100, score))


def get_action(score):
    if score >= 70:
        return "BUY"
    elif score >= 50:
        return "HOLD"
    return "SELL"


# =========================================================
# ANALYSE STOCK
# =========================================================
def analyse_stock(ticker):

    stock = yf.Ticker(ticker)
    info = stock.info

    price = safe_get(info, "currentPrice")
    market_cap = safe_get(info, "marketCap")

    high = safe_get(info, "fiftyTwoWeekHigh")
    low = safe_get(info, "fiftyTwoWeekLow")

    if price and high and low:
        position = (price - low) / (high - low) * 100
    else:
        position = None

    # fundamentals
    growth = get_growth(info)
    valuation = get_valuation(info)
    risk = get_risk(info)

    # news
    news_items = []
    sentiments = []

    try:
        news = stock.news
        for item in news[:3]:
            title = item.get("title", "")
            summary = item.get("summary", title[:120])
            sentiment = get_sentiment(title)

            sentiments.append(sentiment)

            news_items.append({
                "title": title,
                "summary": summary,
                "sentiment": sentiment
            })
    except:
        pass

    # overall sentiment
    if sentiments.count("POSITIVE") > sentiments.count("NEGATIVE"):
        overall_sentiment = "POSITIVE"
    elif sentiments.count("NEGATIVE") > sentiments.count("POSITIVE"):
        overall_sentiment = "NEGATIVE"
    else:
        overall_sentiment = "NEUTRAL"

    # scoring
    score = score_stock(growth, valuation, risk, overall_sentiment)
    action = get_action(score)

    return {
        "ticker": ticker,
        "price": price,
        "market_cap": market_cap,
        "growth": growth,
        "valuation": valuation,
        "risk": risk,
        "position": position,
        "score": score,
        "action": action,
        "sentiment": overall_sentiment,
        "news": news_items,
        "target": safe_get(info, "targetMeanPrice")
    }


# =========================================================
# MAIN REPORT
# =========================================================
def generate_report(portfolio):

    print("\n==============================")
    print("INVESTMENT ANALYST REPORT")
    print("==============================\n")

    results = []

    for ticker in portfolio:
        try:
            result = analyse_stock(ticker)
            results.append(result)
        except Exception as e:
            print(f"Error analysing {ticker}: {e}")

    if not results:
        print("No data available.")
        return

    # =========================
    # SUMMARY
    # =========================
    print("SUMMARY\n")

    for r in results:
        print(f"{r['ticker']} | {r['action']} | Score: {r['score']}")

    best = max(results, key=lambda x: x["score"])
    print(f"\nBest Opportunity: {best['ticker']} ({best['score']})")

    # =========================
    # DETAILS
    # =========================
    for r in results:
        print("\n----------------------------------")
        print(r["ticker"])

        print(f"Price: {num(r['price'])}")
        print(f"Market Cap: {large(r['market_cap'])}")
        print(f"Growth: {r['growth']:.1f}%")
        print(f"Valuation: {r['valuation']}")
        print(f"Risk: {r['risk']}")

        if r["position"]:
            print(f"52 Week Position: {r['position']:.1f}%")

        print(f"Target Price: {num(r['target'])}")

        print("\nNews:")
        for n in r["news"]:
            print(f"- {n['title']}")
            print(f"  {n['summary']}")
