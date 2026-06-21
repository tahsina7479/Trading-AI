import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

st.set_page_config(page_title="MITU FOREX AI", layout="wide")

st.title("🚀 MITU TRADE AI DASHBOARD V5")
st.write("Paper trading scanner with Probability %, AI Grade, Market Filter")

asset_type = st.selectbox(
    "Choose Market",
    ["ALL", "FOREX", "COMMODITIES", "CRYPTO", "STOCKS"]
)

selected_signal = st.selectbox(
    "Choose Signal",
    ["ALL", "STRONG BUY", "BUY WATCH", "WAIT", "SELL WATCH", "STRONG SELL"]
)

show_only_top = st.checkbox("Show only strong opportunities", value=False)

market_symbols = {
    "FOREX": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    "COMMODITIES": ["GC=F", "SI=F"],
    "CRYPTO": ["BTC-USD", "ETH-USD"],
    "STOCKS": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META"]
}

if asset_type == "ALL":
    symbols = []
    for group in market_symbols.values():
        symbols.extend(group)
else:
    symbols = market_symbols[asset_type]

if st.button("🔄 Refresh Market Data"):
    st.rerun()

results = []

with st.spinner("Scanning market..."):
    for symbol in symbols:
        try:
            data = yf.download(symbol, period="5d", interval="5m", progress=False)

            if data.empty or len(data) < 60:
                continue

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

            score = 0

            if trend == "UPTREND":
                score += 35

            if macd_status == "BULLISH":
                score += 35

            if 45 <= latest_rsi <= 60:
                score += 30
            elif 60 < latest_rsi <= 65:
                score += 25
            elif 35 <= latest_rsi < 45:
                score += 20
            elif 65 < latest_rsi <= 70:
                score += 15
            elif latest_rsi > 70:
                score += 5
            else:
                score += 10

            score = min(score, 100)

            probability = round((score * 0.8) + 10, 1)

            if probability > 95:
                probability = 95

            if score >= 85:
                signal = "STRONG BUY"
                confidence = "High"
            elif score >= 70:
                signal = "BUY WATCH"
                confidence = "Medium"
            elif score >= 45:
                signal = "WAIT"
                confidence = "Low"
            elif score >= 30:
                signal = "SELL WATCH"
                confidence = "Medium"
            else:
                signal = "STRONG SELL"
                confidence = "High"

            if score >= 90:
                ai_grade = "A+"
            elif score >= 80:
                ai_grade = "A"
            elif score >= 70:
                ai_grade = "B"
            elif score >= 55:
                ai_grade = "C"
            else:
                ai_grade = "D"

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
                stop_loss = "N/A"
                take_profit = "N/A"
                risk_reward = "N/A"

            reason = ""

            if trend == "UPTREND":
                reason += "EMA trend bullish. "
            else:
                reason += "EMA trend bearish. "

            if macd_status == "BULLISH":
                reason += "MACD bullish. "
            else:
                reason += "MACD bearish. "

            if latest_rsi < 70:
                reason += "RSI not overbought. "
            else:
                reason += "RSI overbought caution. "

            if score >= 85:
                reason += "High quality setup. "
            elif score >= 70:
                reason += "Good watch setup. "
            else:
                reason += "Weak or neutral setup. "

            results.append({
                "Pair": symbol,
                "Price": round(price, 5),
                "RSI": round(latest_rsi, 2),
                "Trend": trend,
                "MACD": macd_status,
                "Signal": signal,
                "Confidence": confidence,
                "Score": score,
                "Probability %": probability,
                "AI Grade": ai_grade,
                "Entry": round(entry, 5),
                "Stop Loss": round(stop_loss, 5) if stop_loss != "N/A" else "N/A",
                "Take Profit": round(take_profit, 5) if take_profit != "N/A" else "N/A",
                "Risk/Reward": risk_reward,
                "Reason": reason
            })

        except Exception as e:
            st.write(f"Skipped {symbol}: {e}")

df = pd.DataFrame(results)

st.write("Total symbols in list:", len(symbols))
st.write("Total results found:", len(results))

if df.empty:
    st.warning("No signals found.")
    st.stop()

if selected_signal != "ALL":
    df = df[df["Signal"] == selected_signal]

if show_only_top:
    df = df[df["Score"] >= 85]

if df.empty:
    st.warning("No signals found for this filter.")
    st.stop()

df = df.sort_values(by=["Score", "Probability %"], ascending=False)

best_trade = df.iloc[0]

st.success(
    f"🔥 BEST TRADE NOW: {best_trade['Pair']} | "
    f"{best_trade['Signal']} | "
    f"Score: {best_trade['Score']} | "
    f"Probability: {best_trade['Probability %']}% | "
    f"Grade: {best_trade['AI Grade']}"
)

st.subheader("🏆 Top 3 Opportunities")

for _, row in df.head(3).iterrows():
    message = (
        f"{row['Pair']} | {row['Signal']} | "
        f"Score: {row['Score']} | "
        f"Probability: {row['Probability %']}% | "
        f"Grade: {row['AI Grade']} | "
        f"Entry: {row['Entry']} | "
        f"SL: {row['Stop Loss']} | "
        f"TP: {row['Take Profit']}"
    )

    if row["Score"] >= 85:
        st.success("🟢 " + message)
    elif row["Score"] >= 70:
        st.warning("🟡 " + message)
    elif row["Score"] >= 45:
        st.info("🔵 " + message)
    else:
        st.error("🔴 " + message)

strong_buy_count = len(df[df["Signal"] == "STRONG BUY"])
buy_watch_count = len(df[df["Signal"] == "BUY WATCH"])
sell_signal_count = len(df[df["Signal"].isin(["SELL WATCH", "STRONG SELL"])])
total_signal_trades = strong_buy_count + buy_watch_count + sell_signal_count

signal_bias = round(
    ((strong_buy_count + buy_watch_count) / total_signal_trades) * 100, 1
) if total_signal_trades > 0 else 0

average_probability = round(df["Probability %"].mean(), 1)

st.subheader("📈 Performance Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Signal Trades", total_signal_trades)
col2.metric("Strong Buy", strong_buy_count)
col3.metric("Sell Signals", sell_signal_count)
col4.metric("Avg Probability %", average_probability)

col5, col6, col7, col8 = st.columns(4)
col5.metric("Buy Watch", buy_watch_count)
col6.metric("Signal Bias %", signal_bias)
col7.metric("Best Score", int(df["Score"].max()))
col8.metric("Best Grade", best_trade["AI Grade"])

st.subheader("🧠 Market Direction Panel")

bullish_count = len(df[(df["Trend"] == "UPTREND") & (df["MACD"] == "BULLISH")])
bearish_count = len(df[(df["Trend"] == "DOWNTREND") & (df["MACD"] == "BEARISH")])
neutral_count = len(df) - bullish_count - bearish_count

col9, col10, col11 = st.columns(3)
col9.metric("Bullish Markets", bullish_count)
col10.metric("Bearish Markets", bearish_count)
col11.metric("Neutral / Mixed", neutral_count)

st.subheader("📊 Market Scanner Results")

df["Stop Loss"] = df["Stop Loss"].astype(str)
df["Take Profit"] = df["Take Profit"].astype(str)
df["Entry"] = df["Entry"].astype(str)

st.dataframe(df, use_container_width=True)

st.warning("Paper trading only. Do not use real money yet.")

st.subheader("📒 Trade Journal")

try:
    journal = pd.read_csv("trade_journal.csv")
    st.dataframe(journal, use_container_width=True)

    total_journal_trades = len(journal)
    total_profit = journal["ProfitLoss"].sum()
    journal_wins = len(journal[journal["ProfitLoss"] > 0])
    journal_win_rate = round((journal_wins / total_journal_trades) * 100, 2) if total_journal_trades > 0 else 0

    st.metric("Journal Total Trades", total_journal_trades)
    st.metric("Journal Win Rate %", journal_win_rate)
    st.metric("Journal Total Profit", total_profit)

except:
    st.warning("No trade journal found yet.")