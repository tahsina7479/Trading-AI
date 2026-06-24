import os
from datetime import datetime

import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

st.set_page_config(page_title="MITU TRADE AI", layout="wide")

JOURNAL_FILE = "trade_journal.csv"

st.title("🚀 MITU TRADE AI PROFESSIONAL TERMINAL V13")
st.write("Professional AI analyst layer: market-separated scanner, confidence stars, ranking, journal, paper account, and equity curve")

account_balance = st.number_input("Starting Paper Account Balance ($)", min_value=10.0, value=1000.0, step=100.0)
risk_percent = st.number_input("Risk Per Trade (%)", min_value=0.1, max_value=10.0, value=2.0, step=0.5)
risk_amount = round(account_balance * (risk_percent / 100), 2)

market_filter = st.selectbox("Choose Market View", ["ALL", "FOREX", "COMMODITIES", "CRYPTO", "STOCKS"])
selected_signal = st.selectbox("Choose Signal", ["ALL", "STRONG BUY", "BUY WATCH", "WAIT", "SELL WATCH", "STRONG SELL"])
show_only_top = st.checkbox("Show only strong opportunities", value=False)

market_symbols = {
    "FOREX": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    "COMMODITIES": ["GC=F", "SI=F"],
    "CRYPTO": ["BTC-USD", "ETH-USD"],
    "STOCKS": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META"]
}

if market_filter == "ALL":
    symbols = []
    for group in market_symbols.values():
        symbols.extend(group)
else:
    symbols = market_symbols[market_filter]

if st.button("🔄 Refresh Market Data"):
    st.rerun()

def get_market_name(symbol):
    for market_name, symbol_list in market_symbols.items():
        if symbol in symbol_list:
            return market_name
    return "UNKNOWN"

def position_note(symbol):
    if symbol.endswith("=X"):
        return "Forex units estimate"
    if symbol in ["BTC-USD", "ETH-USD"]:
        return "Crypto coin amount"
    if symbol in ["GC=F", "SI=F"]:
        return "Commodity units estimate"
    return "Stock shares estimate"


def confidence_stars(score):
    if score >= 95:
        return "⭐⭐⭐⭐⭐"
    elif score >= 85:
        return "⭐⭐⭐⭐"
    elif score >= 75:
        return "⭐⭐⭐"
    elif score >= 65:
        return "⭐⭐"
    else:
        return "⭐"

def analyst_verdict(signal, score, risk_level):
    if signal == "STRONG BUY" and score >= 85 and risk_level != "High":
        return "High-quality setup for paper trading watchlist."
    elif signal == "STRONG BUY":
        return "Strong setup, but check risk and chart before paper trading."
    elif signal == "BUY WATCH":
        return "Good watchlist setup. Wait for confirmation."
    elif signal == "WAIT":
        return "Neutral setup. No rush to trade."
    elif signal in ["SELL WATCH", "STRONG SELL"]:
        return "Bearish setup. Only paper trade if your rules allow short/sell setups."
    return "No clear edge."

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
            probability = min(round((score * 0.8) + 10, 1), 95)

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
                pos_size = round(risk_amount / risk_per_unit, 4) if risk_per_unit > 0 else 0
                pos_value = round(pos_size * entry, 2)
            else:
                pos_size = 0
                pos_value = 0

            reason = ""
            reason += "EMA trend bullish. " if trend == "UPTREND" else "EMA trend bearish. "
            reason += "MACD bullish. " if macd_status == "BULLISH" else "MACD bearish. "
            reason += "RSI not overbought. " if latest_rsi < 70 else "RSI overbought caution. "
            reason += "High quality setup. " if score >= 85 else "Good watch setup. " if score >= 70 else "Weak or neutral setup. "

            market_name = get_market_name(symbol)

            results.append({
                "Market": market_name,
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
                "Confidence Stars": confidence_stars(score),
                "Risk Level": risk_level,
                "Entry": round(entry, 5),
                "Stop Loss": round(stop_loss, 5) if stop_loss != "N/A" else "N/A",
                "Take Profit": round(take_profit, 5) if take_profit != "N/A" else "N/A",
                "Risk/Reward": risk_reward,
                "Risk Amount $": risk_amount,
                "Position Size": pos_size,
                "Position Value $": pos_value,
                "Position Note": position_note(symbol),
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
                "Market": market_name,
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

st.subheader("🔥 Overall Best Trade")
st.success(
    f"""
BEST TRADE NOW: {best_trade['Pair']} ({best_trade['Market']})

Signal: {best_trade['Signal']}  
Type: {best_trade['Type']}  
Score: {best_trade['Score']}  
Probability: {best_trade['Probability %']}%  
AI Grade: {best_trade['AI Grade']}  
Confidence: {best_trade['Confidence Stars']}  
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

st.subheader("🧠 AI Analyst Explanation")

st.info(
    f"""
PAIR: {best_trade['Pair']} ({best_trade['Market']})

FINAL VERDICT: {analyst_verdict(best_trade['Signal'], best_trade['Score'], best_trade['Risk Level'])}

Signal: {best_trade['Signal']}  
Score: {best_trade['Score']}  
Probability: {best_trade['Probability %']}%  
AI Grade: {best_trade['AI Grade']}  
Confidence Stars: {best_trade['Confidence Stars']}  
Risk Level: {best_trade['Risk Level']}  

Technical Reason:
{best_trade['Reason']}
"""
)

st.subheader("🏆 Best Trade by Market")
market_cards = ["FOREX", "COMMODITIES", "CRYPTO", "STOCKS"]
card_cols = st.columns(4)

for i, market_name in enumerate(market_cards):
    market_df = df[df["Market"] == market_name].sort_values(by=["Score", "Probability %"], ascending=False)

    with card_cols[i]:
        st.write(f"### {market_name}")

        if not market_df.empty:
            row = market_df.iloc[0]
            st.success(
                f"""
{row['Pair']}

{row['Signal']}  
Score: {row['Score']}  
Probability: {row['Probability %']}%  
Grade: {row['AI Grade']}  
Stars: {row['Confidence Stars']}  
Risk: {row['Risk Level']}
"""
            )
        else:
            st.info("No signal")

st.subheader("🏆 Top 3 Opportunities by Market")

for market_name in market_cards:
    market_df = df[df["Market"] == market_name].sort_values(by=["Score", "Probability %"], ascending=False)

    if not market_df.empty:
        st.write(f"### {market_name} Top 3")

        for _, row in market_df.head(3).iterrows():
            message = (
                f"{row['Pair']} | {row['Signal']} | "
                f"Score: {row['Score']} | "
                f"Probability: {row['Probability %']}% | "
                f"Grade: {row['AI Grade']} | "
                f"Stars: {row['Confidence Stars']} | "
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

if st.button("Open Overall Best Trade"):
    new_trade = pd.DataFrame([{
        "Open Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Close Date": "",
        "Market": best_trade["Market"],
        "Pair": best_trade["Pair"],
        "Type": best_trade["Type"],
        "Entry": best_trade["Entry"],
        "Stop Loss": best_trade["Stop Loss"],
        "Take Profit": best_trade["Take Profit"],
        "Signal": best_trade["Signal"],
        "Score": best_trade["Score"],
        "Probability %": best_trade["Probability %"],
        "AI Grade": best_trade["AI Grade"],
        "Confidence Stars": best_trade["Confidence Stars"],
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

    st.download_button(
        "⬇️ Download Trade Journal CSV",
        journal.to_csv(index=False),
        "trade_journal_v13.csv",
        "text/csv"
    )

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
        wins = len(closed_journal[closed_journal["ProfitLoss"] > 0])
        losses = len(closed_journal[closed_journal["ProfitLoss"] <= 0])
        win_rate = round((wins / closed_count) * 100, 2)

        best_real_trade = round(closed_journal["ProfitLoss"].max(), 5)
        worst_real_trade = round(closed_journal["ProfitLoss"].min(), 5)

        average_win = round(closed_journal[closed_journal["ProfitLoss"] > 0]["ProfitLoss"].mean(), 5) if wins > 0 else 0
        average_loss = round(closed_journal[closed_journal["ProfitLoss"] <= 0]["ProfitLoss"].mean(), 5) if losses > 0 else 0

        gross_profit = closed_journal[closed_journal["ProfitLoss"] > 0]["ProfitLoss"].sum()
        gross_loss = abs(closed_journal[closed_journal["ProfitLoss"] < 0]["ProfitLoss"].sum())
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else "N/A"

        closed_journal["Equity"] = account_balance + closed_journal["ProfitLoss"].cumsum()
        current_balance = round(account_balance + total_profit, 2)
    else:
        total_profit = 0
        wins = 0
        losses = 0
        win_rate = 0
        best_real_trade = 0
        worst_real_trade = 0
        average_win = 0
        average_loss = 0
        profit_factor = 0
        current_balance = account_balance

    st.subheader("💵 Paper Trading Account")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Starting Balance", f"${account_balance}")
    c2.metric("Current Balance", f"${current_balance}")
    c3.metric("Total Profit/Loss", f"${total_profit}")
    c4.metric("Real Win Rate %", win_rate)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total Journal Trades", total_journal_trades)
    c6.metric("Open Trades", open_count)
    c7.metric("Closed Trades", closed_count)
    c8.metric("Real Wins", wins)

    c9, c10, c11, c12 = st.columns(4)
    c9.metric("Real Losses", losses)
    c10.metric("Best Trade", best_real_trade)
    c11.metric("Worst Trade", worst_real_trade)
    c12.metric("Profit Factor", profit_factor)

    c13, c14 = st.columns(2)
    c13.metric("Average Win", average_win)
    c14.metric("Average Loss", average_loss)

    st.subheader("📅 Daily Performance")

    if "Close Date" in closed_journal.columns and closed_count > 0:
        temp_daily = closed_journal.copy()
        temp_daily["Close Date"] = pd.to_datetime(temp_daily["Close Date"], errors="coerce")
        temp_daily = temp_daily.dropna(subset=["Close Date"])
        if not temp_daily.empty:
            temp_daily["Day"] = temp_daily["Close Date"].dt.date
            daily_summary = temp_daily.groupby("Day").agg(
                Trades=("ProfitLoss", "count"),
                Wins=("ProfitLoss", lambda x: (x > 0).sum()),
                Losses=("ProfitLoss", lambda x: (x <= 0).sum()),
                Profit=("ProfitLoss", "sum")
            ).reset_index()
            daily_summary["Win Rate %"] = round((daily_summary["Wins"] / daily_summary["Trades"]) * 100, 2)
            st.dataframe(daily_summary, use_container_width=True)
        else:
            st.info("No closed trades with close dates yet.")
    else:
        st.info("Close trades to see daily performance.")

    if closed_count > 0:
        st.subheader("📈 Real Equity Curve")
        st.line_chart(closed_journal["Equity"])

        st.subheader("📊 Win Rate by Market")

        if "Market" in closed_journal.columns:
            market_summary = closed_journal.groupby("Market").agg(
                Trades=("ProfitLoss", "count"),
                Wins=("ProfitLoss", lambda x: (x > 0).sum()),
                Losses=("ProfitLoss", lambda x: (x <= 0).sum()),
                Total_Profit=("ProfitLoss", "sum")
            ).reset_index()

            market_summary["Win Rate %"] = round((market_summary["Wins"] / market_summary["Trades"]) * 100, 2)
            st.dataframe(market_summary, use_container_width=True)

        st.subheader("📊 Closed Trades Analytics")
        st.dataframe(closed_journal, use_container_width=True)

except:
    st.warning("No trade journal found yet.")

st.subheader("📈 Signal Dashboard")

strong_buy_count = len(df[df["Signal"] == "STRONG BUY"])
buy_watch_count = len(df[df["Signal"] == "BUY WATCH"])
sell_signal_count = len(df[df["Signal"].isin(["SELL WATCH", "STRONG SELL"])])
total_signal_trades = strong_buy_count + buy_watch_count + sell_signal_count
signal_bias = round(((strong_buy_count + buy_watch_count) / total_signal_trades) * 100, 1) if total_signal_trades > 0 else 0
average_probability = round(df["Probability %"].mean(), 1)

s1, s2, s3, s4 = st.columns(4)
s1.metric("Signal Trades", total_signal_trades)
s2.metric("Strong Buy", strong_buy_count)
s3.metric("Sell Signals", sell_signal_count)
s4.metric("Avg Probability %", average_probability)

s5, s6, s7, s8 = st.columns(4)
s5.metric("Buy Watch", buy_watch_count)
s6.metric("Signal Bias %", signal_bias)
s7.metric("Best Score", int(df["Score"].max()))
s8.metric("Best Grade", best_trade["AI Grade"])

st.subheader("💰 Risk Manager")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Account Balance", f"${account_balance}")
r2.metric("Risk Per Trade", f"{risk_percent}%")
r3.metric("Risk Amount", f"${risk_amount}")
r4.metric("Best Trade Size", best_trade["Position Size"])

st.subheader("🧠 Market Direction Panel")

for market_name in market_cards:
    market_df = df[df["Market"] == market_name]

    bullish_count = len(market_df[(market_df["Trend"] == "UPTREND") & (market_df["MACD"] == "BULLISH")])
    bearish_count = len(market_df[(market_df["Trend"] == "DOWNTREND") & (market_df["MACD"] == "BEARISH")])
    neutral_count = len(market_df) - bullish_count - bearish_count

    st.write(f"### {market_name}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Bullish", bullish_count)
    m2.metric("Bearish", bearish_count)
    m3.metric("Neutral / Mixed", neutral_count)

st.subheader("🧪 Basic Backtest Score Panel")

if not backtest_df.empty:
    backtest_trades = backtest_df[backtest_df["Backtest Result"] != "NO TRADE"]
    backtest_total = len(backtest_trades)
    backtest_wins = len(backtest_trades[backtest_trades["Backtest Result"] == "WIN"])
    backtest_losses = len(backtest_trades[backtest_trades["Backtest Result"] == "LOSS"])
    backtest_score = round((backtest_wins / backtest_total) * 100, 1) if backtest_total > 0 else 0
    backtest_profit = backtest_trades["Backtest Profit Point"].sum() if backtest_total > 0 else 0

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Backtest Trades", backtest_total)
    b2.metric("Backtest Wins", backtest_wins)
    b3.metric("Backtest Losses", backtest_losses)
    b4.metric("Backtest Score %", backtest_score)

    st.metric("Backtest Profit Points", backtest_profit)

    backtest_df["Equity Curve"] = backtest_df["Backtest Profit Point"].cumsum()
    st.line_chart(backtest_df["Equity Curve"])
    st.dataframe(backtest_df, use_container_width=True)
else:
    st.warning("No backtest data found.")

st.subheader("📌 Market Strength Ranking")

ranking_df = df[[
    "Market",
    "Pair",
    "Signal",
    "Score",
    "Probability %",
    "AI Grade",
    "Confidence Stars",
    "Risk Level"
]].sort_values(by=["Score", "Probability %"], ascending=False)

st.dataframe(ranking_df, use_container_width=True)

st.download_button(
    "⬇️ Download Scanner Results CSV",
    df.to_csv(index=False),
    "mitu_trade_ai_scanner_v13.csv",
    "text/csv"
)

st.subheader("📊 Market Scanner Results")

df["Stop Loss"] = df["Stop Loss"].astype(str)
df["Take Profit"] = df["Take Profit"].astype(str)
df["Entry"] = df["Entry"].astype(str)

st.dataframe(df, use_container_width=True)

st.warning("Paper trading only. Do not use real money yet.")
