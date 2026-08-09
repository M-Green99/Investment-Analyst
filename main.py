import yfinance as yf
from datetime import datetime, date

# =========================================================
# HELPERS
# =========================================================
def safe_get(d, key):
    return d.get(key) if d else None


def format_number(value):
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


def format_large(value):
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    return f"{value:,.0f}"


def format_percent(value):
    if value is None:
        return "N/A"
    return f"{value*100:.1f}%"


# =========================================================
# NEWS SENTIMENT
# =========================================================
def get_sentiment(title):
    text = title.lower()

    positive = ["growth", "profit", "beat", "upgrade", "strong", "record"]
    negative = ["loss", "miss", "downgrade", "weak", "decline", "risk"]

    pos = sum(1 for w in positive if w in text)
    neg = sum(1 for w in negative if w in text)

    if pos > neg:
        return "POSITIVE"
    elif neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


# =========================================================
# SCORING
# =========================================================
def score_stock(info, growth, valuation, risk, sentiment):
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

    # Sentiment
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
# ANALYSIS
# =========================================================
def analyse_stock(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    # Market data
    price = safe_get(info, "currentPrice")
    high_52 = safe_get(info, "fiftyTwoWeekHigh")
    low_52 = safe_get(info, "fiftyTwoWeekLow")

    if price and high_52 and low_52:
        position = (price - low_52) / (high_52 - low_52) * 100
    else:
        position = None

    # Growth
    growth = safe_get(info, "revenueGrowth")
    growth = growth * 100 if growth else 0

    # Valuation
    pe = safe_get(info, "forwardPE")
    if pe:
        if pe < 20:
            valuation = "ATTRACTIVE"
        elif pe > 40:
            valuation = "EXPENSIVE"
        else:
            valuation = "FAIR"
    else:
        valuation = "FAIR"

    # Risk
    beta = safe_get(info, "beta")
    if beta and beta > 1.5:
        risk = "HIGH"
    else:
        risk = "MODERATE"

    # News
    news_items = []
    sentiment_list = []

    try:
        news = stock.news
        for item in news[:3]:
            title = item.get("title", "")
            summary = item.get("summary", title[:150])
            sentiment = get_sentiment(title)

            sentiment_list.append(sentiment)

            news_items.append({
                "title": title,
                "summary": summary,
                "sentiment": sentiment
            })
    except:
        pass

    if sentiment_list.count("POSITIVE") > sentiment_list.count("NEGATIVE"):
        overall_sentiment = "POSITIVE"
    elif sentiment_list.count("NEGATIVE") > sentiment_list.count("POSITIVE"):
        overall_sentiment = "NEGATIVE"
    else:
        overall_sentiment = "NEUTRAL"

    # Score
    score = score_stock(info, growth, valuation, risk, overall_sentiment)
    action = get_action(score)

    return {
        "ticker": ticker,
        "price": price,
        "market_cap": safe_get(info, "marketCap"),
        "growth": growth,
        "valuation": valuation,
        "risk": risk,
        "score": score,
        "action": action,
        "position": position,
        "news": news_items,
        "sentiment": overall_sentiment,
        "target": safe_get(info, "targetMeanPrice")
    }


# =========================================================
# REPORT
# =========================================================
def generate_report(portfolio):

    results = []

    print("\n==============================")
    print("INVESTMENT ANALYST REPORT")
    print("==============================\n")

    for ticker in portfolio:
        try:
            result = analyse_stock(ticker)
            results.append(result)
        except Exception as e:
            print(f"Error with {ticker}: {e}")

    # Summary
    print("SUMMARY\n")

    for r in results:
        print(f"{r['ticker']} | {r['action']} | Score: {r['score']}")

    # Best opportunity
    best = max(results, key=lambda x: x["score"])
    print(f"\nBest Opportunity: {best['ticker']} ({best['score']})")

    # Detailed
    for r in results:
        print("\n----------------------------------")
        print(f"{r['ticker']}")

        print(f"Price: {format_number(r['price'])}")
        print(f"Market Cap: {format_large(r['market_cap'])}")

        print(f"Growth: {r['growth']:.1f}%")
        print(f"Valuation: {r['valuation']}")
        print(f"Risk: {r['risk']}")

        if r["position"] is not None:
            print(f"52 Week Position: {r['position']:.1f}%")

        print(f"Target Price: {format_number(r['target'])}")

        print("\nNews:")
        for n in r["news"]:
            print(f"- {n['title']}")
            print(f"  {n['summary']}")
