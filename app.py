import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

st.set_page_config(page_title="MITU FOREX AI", layout="wide")

st.title("🚀 MITU FOREX AI DASHBOARD V2")
st.write("Real market scanner for Forex, Gold, Silver, Crypto")

symbols = symbols = [
    # Forex
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",

    # Commodities
    "GC=F",
    "SI=F",

    # Crypto
    "BTC-USD",
    "ETH-USD",

    # Stocks
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "AMZN",
    "GOOGL",
    "META"
]


results = []

with st.spinner("Scanning market..."):
    for symbol in symbols:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
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
            "Pair": symbol,
            "Price": round(price, 5),
            "RSI": round(latest_rsi, 2),
            "Trend": trend,
            "MACD": macd_status,
            "Signal": signal,
            "Confidence": confidence,
            "Score": score,
            "Entry": round(entry, 5),
            "Stop Loss": round(stop_loss, 5) if stop_loss else "N/A",
            "Take Profit": round(take_profit, 5) if take_profit else "N/A",
            "Risk/Reward": risk_reward
        })

df = pd.DataFrame(results)
df = df.sort_values(by="Score", ascending=False)

st.subheader("📊 Market Scanner Results")
st.dataframe(df, use_container_width=True)

st.subheader("🏆 Top 3 Opportunities")
st.table(df.head(3))

st.warning("Paper trading only. Do not use real money yet.")