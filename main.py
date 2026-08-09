import yfinance as yf
from datetime import datetime, date

# =========================================================
# HELPERS
# =========================================================
def safe(info, key):
    return info.get(key) if info else None

def pct(v):
    return f"{v*100:.1f}%" if v is not None else "N/A"

def num(v):
    return f"{v:,.2f}" if v is not None else "N/A"

def large(v):
    if v is None:
        return "N/A"
    if v > 1e9:
        return f"{v/1e9:.2f}B"
    if v > 1e6:
        return f"{v/1e6:.2f}M"
    return f"{v:,.0f}"

# =========================================================
# NEWS SENTIMENT
# =========================================================
def sentiment(title):
    if not title:
        return "NEUTRAL"
    t = title.lower()

    pos = ["growth","profit","beat","strong","record","upgrade","launch","deal"]
    neg = ["loss","miss","weak","decline","risk","downgrade","delay"]

    p = sum(1 for w in pos if w in t)
    n = sum(1 for w in neg if w in t)

    if p > n:
        return "POSITIVE"
    if n > p:
        return "NEGATIVE"
    return "NEUTRAL"

# =========================================================
# ANALYST CONSENSUS
# =========================================================
def analyst(info):
    rec = safe(info, "recommendationKey")
    if not rec:
        return "N/A"

    rec = rec.lower()
    mapping = {
        "strong_buy":"STRONG BUY",
        "buy":"BUY",
        "hold":"HOLD",
        "sell":"SELL",
        "strong_sell":"STRONG SELL"
    }
    return mapping.get(rec, rec.upper())

# =========================================================
# VALUATION
# =========================================================
def valuation(info):
    pe = safe(info,"forwardPE")
    peg = safe(info,"pegRatio")

    if peg and peg < 1:
        return "ATTRACTIVE"
    if pe and pe < 20:
        return "ATTRACTIVE"
    if pe and pe > 40:
        return "EXPENSIVE"
    return "FAIR"

# =========================================================
# QUALITY
# =========================================================
def quality(info):
    roe = safe(info,"returnOnEquity")
    margin = safe(info,"profitMargins")

    score = 0
    if roe and roe > 0.2: score += 2
    elif roe and roe > 0.1: score += 1

    if margin and margin > 0.15: score += 2
    elif margin and margin > 0: score += 1

    if score >= 3:
        return "STRONG"
    if score >= 1:
        return "OK"
    return "WEAK"

# =========================================================
# GROWTH
# =========================================================
def growth(info):
    g = safe(info,"revenueGrowth")
    return g*100 if g else 0

# =========================================================
# RISK
# =========================================================
def risk(info, growth):
    beta = safe(info,"beta")
    debt = safe(info,"debtToEquity")

    score = 0
    if beta and beta > 1.5: score += 2
    if debt and debt > 120: score += 2
    if growth < 0: score += 1

    if score >= 4:
        return "VERY HIGH"
    if score >= 2:
        return "HIGH"
    return "MODERATE"

# =========================================================
# CATALYSTS
# =========================================================
def catalyst(info):
    if safe(info,"earningsTimestamp"):
        return "MODERATE"
    return "WEAK"

# =========================================================
# EVENTS
# =========================================================
def events(info):
    ev = []
    ts = safe(info,"earningsTimestamp")
    if ts:
        try:
            d = datetime.fromtimestamp(ts).date()
            ev.append(("EARNINGS", d))
        except:
            pass
    return ev

# =========================================================
# SCORE
# =========================================================
def score(q,g,v,r,a,s):
    score = 50

    if q == "STRONG": score += 10
    if q == "WEAK": score -= 10

    if g > 20: score += 15
    elif g > 10: score += 8
    elif g < 0: score -= 10

    if v == "ATTRACTIVE": score += 10
    if v == "EXPENSIVE": score -= 10

    if r == "HIGH": score -= 8
    if r == "VERY HIGH": score -= 12

    if a in ["BUY","STRONG BUY"]: score += 5
    if a in ["SELL","STRONG SELL"]: score -= 5

    if s == "POSITIVE": score += 4
    if s == "NEGATIVE": score -= 4

    return max(0,min(100,score))

def action(score):
    if score >= 70: return "BUY"
    if score >= 50: return "HOLD"
    return "SELL"

# =========================================================
# REASON
# =========================================================
def reason(q,g,v,r,a,s):
    rlist = []

    if q == "STRONG": rlist.append("strong business")
    if g > 10: rlist.append("good growth")
    if v == "ATTRACTIVE": rlist.append("attractive valuation")
    if r in ["HIGH","VERY HIGH"]: rlist.append("high risk")
    if a in ["BUY","STRONG BUY"]: rlist.append("analyst support")
    if s == "POSITIVE": rlist.append("positive news")

    return ", ".join(rlist[:3])

# =========================================================
# ANALYSE
# =========================================================
def analyse(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    price = safe(info,"currentPrice")
    high = safe(info,"fiftyTwoWeekHigh")
    low = safe(info,"fiftyTwoWeekLow")

    pos = None
    if price and high and low:
        pos = (price-low)/(high-low)*100

    # fundamentals
    q = quality(info)
    g = growth(info)
    v = valuation(info)
    r = risk(info,g)
    a = analyst(info)

    # news
    news = []
    sentiments = []
    try:
        for n in stock.news[:3]:
            t = n.get("title","")
            summ = n.get("summary", t[:120])
            s = sentiment(t)
            sentiments.append(s)
            news.append((t,summ,s))
    except:
        pass

    overall = "NEUTRAL"
    if sentiments.count("POSITIVE") > sentiments.count("NEGATIVE"):
        overall = "POSITIVE"
    elif sentiments.count("NEGATIVE") > sentiments.count("POSITIVE"):
        overall = "NEGATIVE"

    # scoring
    sc = score(q,g,v,r,a,overall)
    act = action(sc)
    why = reason(q,g,v,r,a,overall)

    return {
        "ticker":ticker,
        "price":price,
        "cap":safe(info,"marketCap"),
        "growth":g,
        "valuation":v,
        "risk":r,
        "quality":q,
        "analyst":a,
        "score":sc,
        "action":act,
        "reason":why,
        "pos":pos,
        "news":news,
        "events":events(info)
    }

# =========================================================
# REPORT
# =========================================================
def generate_report(portfolio):

    print("\n==============================")
    print("INVESTMENT ANALYST REPORT")
    print("==============================\n")

    results = []

    for t in portfolio:
        try:
            results.append(analyse(t))
        except Exception as e:
            print(f"Error: {t} {e}")

    if not results:
        print("No data")
        return

    print("SUMMARY\n")

    for r in results:
        print(f"{r['ticker']} | {r['action']} | {r['score']} | {r['reason']}")

    best = max(results,key=lambda x:x["score"])
    print(f"\nBest Opportunity: {best['ticker']} ({best['score']})")

    print("\n----------------------------------")

    for r in results:
        print(f"\n{r['ticker']}")
        print(f"Price: {num(r['price'])}")
        print(f"Market Cap: {large(r['cap'])}")
        print(f"Growth: {r['growth']:.1f}%")
        print(f"Valuation: {r['valuation']}")
        print(f"Risk: {r['risk']}")
        print(f"Quality: {r['quality']}")
        print(f"Analyst: {r['analyst']}")

        if r["pos"]:
            print(f"52 Week Position: {r['pos']:.1f}%")

        print("\nNews:")
        for n in r["news"]:
            print(f"- {n[0]}")
            print(f"  {n[1]}")

        print("\nKey Dates:")
        for e in r["events"]:
            print(f"{e[0]}: {e[1]}")
