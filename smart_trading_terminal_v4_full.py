# --- BEGIN SMART TRADING TERMINAL V4 FULL ---

import streamlit as st
import pandas as pd
import yfinance as yf
import smtplib
from email.message import EmailMessage
import matplotlib.pyplot as plt
import datetime
import os
import alpaca_trade_api as tradeapi

# Embedded credentials (replace with yours)
API_KEY = "AK9NT5DXOZ3DXLRD9JHA"
SECRET_KEY = "K1GDSDDgDj1jSglAW4BexhPQl8HTmfOdHNYDofDG"
BASE_URL = "https://api.alpaca.markets"
EMAIL_SENDER = "bob.naf02@gmail.com"
EMAIL_RECEIVER = "bob.naf02@gmail.com"
EMAIL_APP_PASSWORD = "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"
DEFAULT_INTERVAL_MINUTES = 120

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

st.set_page_config(page_title="Smart Trading Terminal", layout="wide")
st.title("📈 Smart Trading Terminal (Live Trading)")

# Persistent session storage
if "watchlist" not in st.session_state:
    st.session_state.watchlist = {
        "VAS.AX": {"buy_below": 90, "sell_above": 110, "stop_loss": 80, "trailing_profit": 5},
        "VHY.AX": {"buy_below": 60, "sell_above": 75, "stop_loss": 50, "trailing_profit": 5},
        "NDQ.AX": {"buy_below": 30, "sell_above": 45, "stop_loss": 25, "trailing_profit": 5}
    }

if "trades" not in st.session_state:
    st.session_state.trades = []

# Sidebar - Editable watchlist
st.sidebar.header("🛠 Settings")
editable_symbols = list(st.session_state.watchlist.keys())
selected_etfs = st.sidebar.multiselect("✅ Select ETFs", editable_symbols, default=editable_symbols)

st.sidebar.subheader("⏱ Market Check Interval")
interval = st.sidebar.number_input("Minutes", min_value=1, value=DEFAULT_INTERVAL_MINUTES)

st.sidebar.subheader("📧 Email Alerts")
alerts_enabled = st.sidebar.checkbox("Enable Email Alerts", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add / Remove ETFs")
new_symbol = st.sidebar.text_input("New ETF Symbol")
if st.sidebar.button("Add ETF") and new_symbol:
    st.session_state.watchlist[new_symbol] = {"buy_below": 0, "sell_above": 0, "stop_loss": 0, "trailing_profit": 0}
    st.experimental_rerun()

symbol_to_remove = st.sidebar.selectbox("Remove ETF", [""] + editable_symbols)
if st.sidebar.button("Remove") and symbol_to_remove:
    del st.session_state.watchlist[symbol_to_remove]
    st.experimental_rerun()

def send_email_alert(subject, body):
    if not alerts_enabled:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)

def get_price(symbol):
    data = yf.Ticker(symbol).history(period="1d", interval="1m")
    return data["Close"].iloc[-1] if not data.empty else None

def check_and_trade():
    trade_log = []
    for symbol in selected_etfs:
        config = st.session_state.watchlist[symbol]
        price = get_price(symbol)
        if not price:
            continue

        try:
            pos = api.get_position(symbol)
            qty = float(pos.qty)
            cost_basis = float(pos.avg_entry_price)
            if price <= config["stop_loss"]:
                api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="gtc")
                msg = f"Stop-loss: Sold {symbol} at {price}"
                trade_log.append(msg)
                send_email_alert("Stop-loss Triggered", msg)
            elif price >= cost_basis + config["trailing_profit"]:
                api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="gtc")
                msg = f"Trailing profit: Sold {symbol} at {price}"
                trade_log.append(msg)
                send_email_alert("Trailing Profit Triggered", msg)
        except:
            qty = 1
            if price <= config["buy_below"]:
                api.submit_order(symbol=symbol, qty=qty, side="buy", type="market", time_in_force="gtc")
                msg = f"Bought {symbol} at {price}"
                trade_log.append(msg)
                send_email_alert("Buy Executed", msg)

        if price >= config["sell_above"]:
            try:
                pos = api.get_position(symbol)
                qty = float(pos.qty)
                api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="gtc")
                msg = f"Sold {symbol} at {price}"
                trade_log.append(msg)
                send_email_alert("Sell Executed", msg)
            except:
                pass

    st.session_state.trades += trade_log
    return trade_log

if st.button("▶ Run Bot Now"):
    logs = check_and_trade()
    for log in logs:
        st.success(log)

st.subheader("📊 ETF Price Monitor")
for symbol in selected_etfs:
    col1, col2 = st.columns(2)
    price = get_price(symbol)
    col1.metric(label=f"{symbol} Price", value=f"${price:.2f}" if price else "N/A")
    with col2:
        config = st.session_state.watchlist[symbol]
        config["buy_below"] = st.number_input(f"{symbol} Buy Below", value=config["buy_below"])
        config["sell_above"] = st.number_input(f"{symbol} Sell Above", value=config["sell_above"])
        config["stop_loss"] = st.number_input(f"{symbol} Stop Loss", value=config["stop_loss"])
        config["trailing_profit"] = st.number_input(f"{symbol} Trailing Profit", value=config["trailing_profit"])

st.subheader("📈 Price History")
for symbol in selected_etfs:
    df = yf.Ticker(symbol).history(period="5d", interval="1h")
    if not df.empty:
        st.line_chart(df["Close"])

st.subheader("🧾 Trade History")
if st.session_state.trades:
    for t in st.session_state.trades[-10:][::-1]:
        st.code(t)

# --- END OF FILE ---
