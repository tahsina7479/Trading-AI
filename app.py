import time
import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

st.set_page_config(page_title="MITU FOREX AI", layout="wide")

st.title("🚀 MITU TRADE AI DASHBOARD V2")
st.write("Real market scanner for Forex, Gold, Silver, Crypto")
refresh_seconds = st.selectbox("Auto Refresh", [0, 30, 60, 300], index=2)

if st.button("🔄 Refresh Now"):
    st.rerun()

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
st.subheader("🎯 Signal Filter")

selected_signal = st.selectbox(
    "Choose Signal",
    ["ALL", "STRONG BUY", "BUY WATCH", "WAIT", "SELL WATCH", "STRONG SELL"]
)

with st.spinner("Scanning market..."):
    for symbol in symbols:
        data = yf.download(symbol, period="5d", interval="5m", progress=False)
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

        reason = ""

if trend == "UPTREND":
    reason += "EMA trend bullish. "

if macd_status == "BULLISH":
    reason += "MACD bullish. "

if latest_rsi < 70:
    reason += "RSI not overbought. "

if latest_rsi > 70:
    reason += "RSI overbought caution. "    

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
            "Risk/Reward": risk_reward,
            "Reason": reason
        })

df = pd.DataFrame(results)

if selected_signal != "ALL":
    df = df[df["Signal"] == selected_signal]

if df.empty:
    st.warning("No signals found.")
    st.stop()

df = df.sort_values(by="Score", ascending=False)

best_trade = df.iloc[0]

st.success(
    f"🔥 BEST TRADE NOW: {best_trade['Pair']} | "
    f"{best_trade['Signal']} | "
    f"Score: {best_trade['Score']}"
)
df = df.sort_values(by="Score", ascending=False)
st.subheader("🏆 Top 3 Opportunities")

top3 = df.head(3)

for index, row in top3.iterrows():

    message = (
        f"{row['Pair']} | {row['Signal']} | "
        f"Score: {row['Score']} | "
        f"Entry: {row['Entry']} | "
        f"SL: {row['Stop Loss']} | "
        f"TP: {row['Take Profit']}"
    )

    if row["Score"] >= 90:
        st.success("🟢 " + message)

    elif row["Score"] >= 80:
        st.info("🔵 " + message)

    elif row["Score"] >= 70:
        st.warning("🟡 " + message)

    else:
        st.error("🔴 " + message)
    wins = len(df[df["Signal"] == "STRONG BUY"])
losses = len(df[df["Signal"] == "STRONG SELL"])
total_trades = wins + losses

if total_trades > 0:
    win_rate = round((wins / total_trades) * 100, 1)
else:
    win_rate = 0

st.subheader("📈 Performance Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Trades", total_trades)
col2.metric("Wins", wins)
col3.metric("Losses", losses)
col4.metric("Win Rate %", win_rate)  
st.subheader("📒 Trade Journal")

journal = pd.read_csv("trade_journal.csv")

st.dataframe(journal, use_container_width=True)  

st.subheader("📊 Market Scanner Results")
st.button("Refresh Market Data")
df["Stop Loss"] = df["Stop Loss"].astype(str)
df["Take Profit"] = df["Take Profit"].astype(str)
df["Entry"] = df["Entry"].astype(str)
st.dataframe(df, use_container_width=True)

st.subheader("🏆 Top 3 Opportunities")
st.table(df.head(3))

st.warning("Paper trading only. Do not use real money yet.")


try:
    journal = pd.read_csv("trade_journal.csv")

    st.dataframe(journal)

    total_trades = len(journal)

    total_profit = journal["ProfitLoss"].sum()

    wins = len(journal[journal["ProfitLoss"] > 0])

    win_rate = round((wins / total_trades) * 100, 2)

    st.metric("Total Trades", total_trades)
    st.metric("Win Rate %", win_rate)
    st.metric("Total Profit", total_profit)

except:
    st.warning("No trade journal found yet.")