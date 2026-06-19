import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

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

print("\n=== MITU FOREX AI V5 ===")

for symbol in symbols:
    data = yf.download(symbol, period="6mo", interval="1d")
    close = data["Close"].squeeze()

    rsi = RSIIndicator(close, window=14).rsi()
    ema20 = EMAIndicator(close, window=20).ema_indicator()
    ema50 = EMAIndicator(close, window=50).ema_indicator()

    price = float(close.iloc[-1])
    latest_rsi = float(rsi.iloc[-1])
    latest_ema20 = float(ema20.iloc[-1])
    latest_ema50 = float(ema50.iloc[-1])

    trend = "UPTREND" if latest_ema20 > latest_ema50 else "DOWNTREND"

    score = 0
    if trend == "UPTREND":
        score += 50
    if latest_rsi < 50:
        score += 25
    if latest_rsi < 40:
        score += 25
    if latest_rsi > 70:
        score -= 25

if latest_rsi > 80:
    score -= 25   

    if score >= 75:
     signal = "BUY"
    confidence = "High"

elif score >= 50:
    signal = "WATCHLIST"
    confidence = "Medium"

elif score <= 25:
    signal = "SELL"
    confidence = "High"

else:
    signal = "WAIT"
    confidence = "Low"

if signal == "BUY":
    entry = price
    stop_loss = price * 0.99
    take_profit = price * 1.02
    risk_reward = "1:2"
elif signal == "SELL":
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
        "risk_reward": risk_reward,
        "pair": symbol,
        "price": round(price, 5),
        "rsi": round(latest_rsi, 2),
        "trend": trend,
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "entry": round(entry, 5),
        "stop_loss": round(stop_loss, 5) if stop_loss else "N/A",
        "take_profit": round(take_profit, 5) if take_profit else "N/A"
    })

    print("\nPair:", symbol)
    print("Price:", round(price, 5))
    print("RSI:", round(latest_rsi, 2))
    print("Trend:", trend)
    print("Signal:", signal)
    print("Confidence:", confidence)
    print("Score:", score)
    print("Entry:", round(entry, 5))
    print("Stop Loss:", round(stop_loss, 5) if stop_loss else "N/A")
    print("Take Profit:", round(take_profit, 5) if take_profit else "N/A")
    print("Risk/Reward:", risk_reward)
print("\n=== TOP 3 SCORE RANKING ===")

results = sorted(results, key=lambda x: x["score"], reverse=True)

for item in results[:3]:
    print(item)

print("\nNOTE: Paper trading only. Do not use real money yet.")