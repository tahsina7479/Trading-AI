import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

symbols = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "GC=F",
    "SI=F",
    "BTC-USD",
    "ETH-USD"
]

results = []

print("\n=== MITU FOREX AI V8 ===")

for symbol in symbols:
    data = yf.download(symbol, period="6mo", interval="1d")
    close = data["Close"].squeeze()

    rsi = RSIIndicator(close, window=14).rsi()
    ema20 = EMAIndicator(close, window=20).ema_indicator()
    ema50 = EMAIndicator(close, window=50).ema_indicator()

    macd_indicator = MACD(close)
    macd_line = macd_indicator.macd()
    macd_signal = macd_indicator.macd_signal()

    price = float(close.iloc[-1])
    latest_rsi = float(rsi.iloc[-1])
    latest_ema20 = float(ema20.iloc[-1])
    latest_ema50 = float(ema50.iloc[-1])
    latest_macd = float(macd_line.iloc[-1])
    latest_macd_signal = float(macd_signal.iloc[-1])

    trend = "UPTREND" if latest_ema20 > latest_ema50 else "DOWNTREND"
    macd_status = "BULLISH" if latest_macd > latest_macd_signal else "BEARISH"

    score = 50

    if trend == "UPTREND":
        score += 20
    else:
        score -= 20

    if latest_rsi < 40:
        score += 20
    elif latest_rsi > 70:
        score -= 20

    if macd_status == "BULLISH":
        score += 20
    else:
        score -= 20

    if score >= 80:
        signal = "STRONG BUY"
        confidence = "High"
    elif score >= 65:
        signal = "BUY WATCH"
        confidence = "Medium"
    elif score <= 20:
        signal = "STRONG SELL"
        confidence = "High"
    elif score <= 35:
        signal = "SELL WATCH"
        confidence = "Medium"
    else:
        signal = "WAIT"
        confidence = "Low"

    if "BUY" in signal:
        entry = price
        stop_loss = price * 0.99
        take_profit = price * 1.02
        risk_reward = "1:2"
    elif "SELL" in signal:
        entry = price
        stop_loss = price * 1.01
        take_profit = price * 0.98
        risk_reward = "1:2"
    else:
        entry = price
        stop_loss = None
        take_profit = None
        risk_reward = "N/A"

    results.append({
        "pair": symbol,
        "price": round(price, 5),
        "rsi": round(latest_rsi, 2),
        "trend": trend,
        "macd": macd_status,
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "entry": round(entry, 5),
        "stop_loss": round(stop_loss, 5) if stop_loss else "N/A",
        "take_profit": round(take_profit, 5) if take_profit else "N/A",
        "risk_reward": risk_reward
    })

    print("\nPair:", symbol)
    print("Price:", round(price, 5))
    print("RSI:", round(latest_rsi, 2))
    print("Trend:", trend)
    print("MACD:", macd_status)
    print("Signal:", signal)
    print("Confidence:", confidence)
    print("Score:", score)
    print("Entry:", round(entry, 5))
    print("Stop Loss:", round(stop_loss, 5) if stop_loss else "N/A")
    print("Take Profit:", round(take_profit, 5) if take_profit else "N/A")
    print("Risk/Reward:", risk_reward)

print("\n=== TOP 3 OPPORTUNITIES ===")

results = sorted(results, key=lambda x: x["score"], reverse=True)

for i, item in enumerate(results[:3], 1):
    print(f"\n#{i}")
    print("Pair:", item["pair"])
    print("Signal:", item["signal"])
    print("Score:", item["score"])
    print("Trend:", item["trend"])
    print("MACD:", item["macd"])
    print("RSI:", item["rsi"])
    print("Entry:", item["entry"])
    print("Stop Loss:", item["stop_loss"])
    print("Take Profit:", item["take_profit"])

print("\nNOTE: Paper trading only. Do not use real money yet.")