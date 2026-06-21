import os
from datetime import datetime

import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

st.set_page_config(page_title="MITU FOREX AI", layout="wide")

JOURNAL_FILE = "trade_journal.csv"

st.title("🚀 MITU TRADE AI DASHBOARD V10")
st.write("AI scanner + risk manager + real paper trading account + equity curve")

account_balance = st.number_input("Starting Paper Account Balance ($)", min_value=10.0, value=1000.0, step=100.0)
risk_percent = st.number_input("Risk Per Trade (%)", min_value=0.1, max_value=10.0, value=2.0, step=0.5)

risk_amount = round(account_balance * (risk_percent / 100), 2)

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
backtest_rows = []

with st.spinner("Scanning market..."):
    for symbol in symbols:
        try:
            data = yf.download(symbol, period="5d", interval="5m", progress=False)

            if data.empty or len(data) < 80:
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
            probability = min(probability, 95)

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

            if latest_rsi > 70:
                risk_level = "High"
            elif score >= 85 and 45 <= latest_rsi <= 65:
                risk_level = "Low"
            elif score >= 70:
                risk_level = "Medium"
            else:
                risk_level = "High"

            if "BUY" in signal:
                trade_type = "BUY"
                entry = price
                stop_loss = price * 0.99
                take_profit = price * 1.02
                risk_reward = "1:2"
            elif "SELL" in signal:
                trade_type = "SELL"
                entry = price
                stop_loss = price * 1.01
                take_profit = price * 0.98
                risk_reward = "1:2"
            else:
                trade_type = "WAIT"
                entry = price
                stop_loss = "N/A"
                take_profit = "N/A"
                risk_reward = "N/A"

            if stop_loss != "N/A":
                risk_per_unit = abs(entry - stop_loss)
                position_size = round(risk_amount / risk_per_unit, 4) if risk_per_unit > 0 else 0
                position_value = round(position_size * entry, 2)
            else:
                position_size = 0
                position_value = 0

            if symbol.endswith("=X"):
                position_note = "Forex units estimate"
            elif symbol in ["BTC-USD", "ETH-USD"]:
                position_note = "Crypto coin amount"
            elif symbol in ["GC=F", "SI=F"]:
                position_note = "Commodity units estimate"
            else:
                position_note = "Stock shares estimate"

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
                "Type": trade_type,
                "Confidence": confidence,
                "Score": score,
                "Probability %": probability,
                "AI Grade": ai_grade,
                "Risk Level": risk_level,
                "Entry": round(entry, 5),
                "Stop Loss": round(stop_loss, 5) if stop_loss != "N/A" else "N/A",
                "Take Profit": round(take_profit, 5) if take_profit != "N/A" else "N/A",
                "Risk/Reward": risk_reward,
                "Risk Amount $": risk_amount,
                "Position Size": position_size,
                "Position Value $": position_value,
                "Position Note": position_note,
                "Reason": reason
            })

            old_price = float(close.iloc[-20])
            new_price = float(close.iloc[-1])
            price_change = round(((new_price - old_price) / old_price) * 100, 2)

            if score >= 85 and price_change > 0:
                backtest_result = "WIN"
                backtest_profit = 1
            elif score >= 85 and price_change <= 0:
                backtest_result = "LOSS"
                backtest_profit = -1
            elif score <= 30 and price_change < 0:
                backtest_result = "WIN"
                backtest_profit = 1
            elif score <= 30 and price_change >= 0:
                backtest_result = "LOSS"
                backtest_profit = -1
            else:
                backtest_result = "NO TRADE"
                backtest_profit = 0

            backtest_rows.append({
                "Pair": symbol,
                "Past 20 Candle Move %": price_change,
                "Signal": signal,
                "Score": score,
                "Backtest Result": backtest_result,
                "Backtest Profit Point": backtest_profit
            })

        except Exception as e:
            st.write(f"Skipped {symbol}: {e}")

df = pd.DataFrame(results)
backtest_df = pd.DataFrame(backtest_rows)

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

st.subheader("🔥 Professional Best Trade Card")

st.success(
    f"""
BEST TRADE NOW: {best_trade['Pair']}

Signal: {best_trade['Signal']}  
Type: {best_trade['Type']}  
Score: {best_trade['Score']}  
Probability: {best_trade['Probability %']}%  
AI Grade: {best_trade['AI Grade']}  
Risk Level: {best_trade['Risk Level']}  

Entry: {best_trade['Entry']}  
Stop Loss: {best_trade['Stop Loss']}  
Take Profit: {best_trade['Take Profit']}  
Risk/Reward: {best_trade['Risk/Reward']}  

Risk Amount: ${best_trade['Risk Amount $']}  
Position Size: {best_trade['Position Size']}  
Position Value: ${best_trade['Position Value $']}  
"""
)

st.subheader("🏆 Top 3 Opportunities")

for _, row in df.head(3).iterrows():
    message = (
        f"{row['Pair']} | {row['Signal']} | "
        f"Score: {row['Score']} | "
        f"Probability: {row['Probability %']}% | "
        f"Grade: {row['AI Grade']} | "
        f"Risk: {row['Risk Level']} | "
        f"Entry: {row['Entry']} | "
        f"SL: {row['Stop Loss']} | "
        f"TP: {row['Take Profit']} | "
        f"Size: {row['Position Size']}"
    )

    if row["Score"] >= 85:
        st.success("🟢 " + message)
    elif row["Score"] >= 70:
        st.warning("🟡 " + message)
    elif row["Score"] >= 45:
        st.info("🔵 " + message)
    else:
        st.error("🔴 " + message)

st.subheader("💾 Open Best Trade in Journal")

if st.button("Open Best Trade"):
    new_trade = pd.DataFrame([{
        "Open Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Close Date": "",
        "Pair": best_trade["Pair"],
        "Type": best_trade["Type"],
        "Entry": best_trade["Entry"],
        "Stop Loss": best_trade["Stop Loss"],
        "Take Profit": best_trade["Take Profit"],
        "Signal": best_trade["Signal"],
        "Score": best_trade["Score"],
        "Probability %": best_trade["Probability %"],
        "AI Grade": best_trade["AI Grade"],
        "Risk Level": best_trade["Risk Level"],
        "Risk Amount $": best_trade["Risk Amount $"],
        "Position Size": best_trade["Position Size"],
        "Position Value $": best_trade["Position Value $"],
        "Exit": "",
        "ProfitLoss": 0,
        "Status": "OPEN",
        "Result": "",
        "Reason": best_trade["Reason"]
    }])

    if os.path.exists(JOURNAL_FILE):
        old_journal = pd.read_csv(JOURNAL_FILE)
        updated_journal = pd.concat([old_journal, new_trade], ignore_index=True)
    else:
        updated_journal = new_trade

    updated_journal.to_csv(JOURNAL_FILE, index=False)
    st.success("Best trade opened in journal ✅")

st.subheader("✅ Close Open Trade Manually")

if os.path.exists(JOURNAL_FILE):
    journal_for_close = pd.read_csv(JOURNAL_FILE)

    if "Status" in journal_for_close.columns:
        open_trades = journal_for_close[journal_for_close["Status"] == "OPEN"]

        if not open_trades.empty:
            open_index = st.selectbox("Choose open trade to close", open_trades.index.tolist())
            selected_open_trade = journal_for_close.loc[open_index]

            st.write("Selected Trade:")
            st.write(selected_open_trade)

            exit_price = st.number_input("Exit Price", min_value=0.0, step=0.0001, format="%.5f")
            close_note = st.text_input("Close Note", "")

            if st.button("Close Selected Trade"):
                entry_price = float(selected_open_trade["Entry"])
                trade_type = selected_open_trade["Type"]

                if trade_type == "BUY":
                    profit_loss = exit_price - entry_price
                elif trade_type == "SELL":
                    profit_loss = entry_price - exit_price
                else:
                    profit_loss = 0

                result = "WIN" if profit_loss > 0 else "LOSS"

                journal_for_close.loc[open_index, "Exit"] = exit_price
                journal_for_close.loc[open_index, "ProfitLoss"] = round(profit_loss, 5)
                journal_for_close.loc[open_index, "Status"] = "CLOSED"
                journal_for_close.loc[open_index, "Result"] = result
                journal_for_close.loc[open_index, "Close Date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                journal_for_close.loc[open_index, "Close Note"] = close_note

                journal_for_close.to_csv(JOURNAL_FILE, index=False)
                st.success("Trade closed and journal updated ✅")
        else:
            st.info("No open trades to close.")
    else:
        st.info("Old journal format found. Open a new trade first.")
else:
    st.info("No journal file yet. Open a trade first.")

st.subheader("📒 Real Trade Journal + Paper Account")

try:
    journal = pd.read_csv(JOURNAL_FILE)
    st.dataframe(journal, use_container_width=True)

    total_journal_trades = len(journal)

    if "Status" in journal.columns:
        open_count = len(journal[journal["Status"] == "OPEN"])
        closed_journal = journal[journal["Status"] == "CLOSED"].copy()
    else:
        open_count = 0
        closed_journal = journal.copy()

    closed_count = len(closed_journal)

    if closed_count > 0 and "ProfitLoss" in closed_journal.columns:
        closed_journal["ProfitLoss"] = pd.to_numeric(closed_journal["ProfitLoss"], errors="coerce").fillna(0)

        total_profit = round(closed_journal["ProfitLoss"].sum(), 5)
        journal_wins = len(closed_journal[closed_journal["ProfitLoss"] > 0])
        journal_losses = len(closed_journal[closed_journal["ProfitLoss"] <= 0])
        journal_win_rate = round((journal_wins / closed_count) * 100, 2)

        best_real_trade = round(closed_journal["ProfitLoss"].max(), 5)
        worst_real_trade = round(closed_journal["ProfitLoss"].min(), 5)

        average_win = round(closed_journal[closed_journal["ProfitLoss"] > 0]["ProfitLoss"].mean(), 5) if journal_wins > 0 else 0
        average_loss = round(closed_journal[closed_journal["ProfitLoss"] <= 0]["ProfitLoss"].mean(), 5) if journal_losses > 0 else 0

        gross_profit = closed_journal[closed_journal["ProfitLoss"] > 0]["ProfitLoss"].sum()
        gross_loss = abs(closed_journal[closed_journal["ProfitLoss"] < 0]["ProfitLoss"].sum())
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else "N/A"

        closed_journal["Equity"] = account_balance + closed_journal["ProfitLoss"].cumsum()
        current_balance = round(account_balance + total_profit, 2)
    else:
        total_profit = 0
        journal_wins = 0
        journal_losses = 0
        journal_win_rate = 0
        best_real_trade = 0
        worst_real_trade = 0
        average_win = 0
        average_loss = 0
        profit_factor = 0
        current_balance = account_balance

    st.subheader("💵 Paper Trading Account")

    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    col_a1.metric("Starting Balance", f"${account_balance}")
    col_a2.metric("Current Balance", f"${current_balance}")
    col_a3.metric("Total Profit/Loss", f"${total_profit}")
    col_a4.metric("Real Win Rate %", journal_win_rate)

    col16, col17, col18, col19 = st.columns(4)
    col16.metric("Total Journal Trades", total_journal_trades)
    col17.metric("Open Trades", open_count)
    col18.metric("Closed Trades", closed_count)
    col19.metric("Real Wins", journal_wins)

    col20, col21, col22, col23 = st.columns(4)
    col20.metric("Real Losses", journal_losses)
    col21.metric("Best Trade", best_real_trade)
    col22.metric("Worst Trade", worst_real_trade)
    col23.metric("Profit Factor", profit_factor)

    col24, col25 = st.columns(2)
    col24.metric("Average Win", average_win)
    col25.metric("Average Loss", average_loss)

    if closed_count > 0:
        st.subheader("📈 Real Equity Curve")
        st.line_chart(closed_journal["Equity"])
        st.subheader("📊 Closed Trades Analytics")
        st.dataframe(closed_journal, use_container_width=True)

except:
    st.warning("No trade journal found yet.")

strong_buy_count = len(df[df["Signal"] == "STRONG BUY"])
buy_watch_count = len(df[df["Signal"] == "BUY WATCH"])
sell_signal_count = len(df[df["Signal"].isin(["SELL WATCH", "STRONG SELL"])])
total_signal_trades = strong_buy_count + buy_watch_count + sell_signal_count

signal_bias = round(((strong_buy_count + buy_watch_count) / total_signal_trades) * 100, 1) if total_signal_trades > 0 else 0
average_probability = round(df["Probability %"].mean(), 1)

st.subheader("📈 Signal Dashboard")

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

st.subheader("💰 Risk Manager")

col_r1, col_r2, col_r3, col_r4 = st.columns(4)
col_r1.metric("Account Balance", f"${account_balance}")
col_r2.metric("Risk Per Trade", f"{risk_percent}%")
col_r3.metric("Risk Amount", f"${risk_amount}")
col_r4.metric("Best Trade Size", best_trade["Position Size"])

st.subheader("🧠 Market Direction Panel")

bullish_count = len(df[(df["Trend"] == "UPTREND") & (df["MACD"] == "BULLISH")])
bearish_count = len(df[(df["Trend"] == "DOWNTREND") & (df["MACD"] == "BEARISH")])
neutral_count = len(df) - bullish_count - bearish_count

col9, col10, col11 = st.columns(3)
col9.metric("Bullish Markets", bullish_count)
col10.metric("Bearish Markets", bearish_count)
col11.metric("Neutral / Mixed", neutral_count)

st.subheader("🧪 Basic Backtest Score Panel")

if not backtest_df.empty:
    backtest_trades = backtest_df[backtest_df["Backtest Result"] != "NO TRADE"]
    backtest_total = len(backtest_trades)
    backtest_wins = len(backtest_trades[backtest_trades["Backtest Result"] == "WIN"])
    backtest_losses = len(backtest_trades[backtest_trades["Backtest Result"] == "LOSS"])
    backtest_score = round((backtest_wins / backtest_total) * 100, 1) if backtest_total > 0 else 0
    backtest_profit = backtest_trades["Backtest Profit Point"].sum() if backtest_total > 0 else 0

    col12, col13, col14, col15 = st.columns(4)
    col12.metric("Backtest Trades", backtest_total)
    col13.metric("Backtest Wins", backtest_wins)
    col14.metric("Backtest Losses", backtest_losses)
    col15.metric("Backtest Score %", backtest_score)

    st.metric("Backtest Profit Points", backtest_profit)

    backtest_df["Equity Curve"] = backtest_df["Backtest Profit Point"].cumsum()

    st.line_chart(backtest_df["Equity Curve"])
    st.dataframe(backtest_df, use_container_width=True)
else:
    st.warning("No backtest data found.")

st.subheader("📊 Market Scanner Results")

df["Stop Loss"] = df["Stop Loss"].astype(str)
df["Take Profit"] = df["Take Profit"].astype(str)
df["Entry"] = df["Entry"].astype(str)

st.dataframe(df, use_container_width=True)

st.warning("Paper trading only. Do not use real money yet.")