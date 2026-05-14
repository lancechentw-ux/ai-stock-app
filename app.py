# ======================================
# 台股量化交易 Web App (Streamlit)
# ======================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def add_indicators(df):
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()

    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['foreign_buy'] = np.random.randint(-1000, 1000, len(df))
    df['chip_score'] = (df['foreign_buy'] > 0).astype(int).cumsum()

    return df

def generate_signal(df, chip_threshold=3):
    signals = []

    for i in range(1, len(df)):
        buy = (
            df['MACD'].iloc[i] > df['Signal'].iloc[i]
            and df['RSI'].iloc[i] < 70
            and df['chip_score'].iloc[i] >= chip_threshold
        )

        sell = df['RSI'].iloc[i] > 80

        if buy:
            signals.append('BUY')
        elif sell:
            signals.append('SELL')
        else:
            signals.append('HOLD')

    df = df.iloc[1:]
    df['Trade'] = signals
    return df
def backtest(df):

    cash = 100000
    position = 0

    equity_curve = []

    for i in range(len(df)):

        signal = str(df['Trade'].iloc[i])
        price = float(df['Close'].iloc[i])

        if signal == 'BUY' and cash > 0:

            position = cash / price
            cash = 0

        elif signal == 'SELL' and position > 0:

            cash = position * price
            position = 0

        equity = cash + position * price

        equity_curve.append(equity)

    df['Equity'] = equity_curve

    return df

st.title('📈 台股量化交易系統（Web App）')

stock = st.text_input('輸入股票代碼（例如 2330.TW）', '2330.TW')
chip_threshold = st.slider('籌碼門檻', 1, 10, 3)

if st.button('開始分析'):
    df = yf.download(stock, start='2022-01-01')

    if df.empty:
        st.error('抓不到資料，請確認股票代碼')
    else:
        df = add_indicators(df)
        df = generate_signal(df, chip_threshold)
        df = backtest(df)

        st.subheader('📊 價格')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20'))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='MA60'))
        st.plotly_chart(fig)

        st.subheader('💰 資產曲線')
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df.index, y=df['Equity'], name='Equity'))
        st.plotly_chart(fig2)

        st.subheader('📋 訊號')
        st.dataframe(df[['Close', 'Trade']].tail(20))
