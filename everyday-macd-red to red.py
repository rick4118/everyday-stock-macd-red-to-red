import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 設定網頁標題
st.set_page_config(page_title="日MACD「紅縮轉紅多」選股器", layout="wide")
st.title("📈 日MACD「紅縮轉紅多」選股工具")

def compute_macd(df, fast=12, slow=26, signal=9):
    df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = df['EMA_fast'] - df['EMA_slow']
    df['MACD'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['OSC'] = df['DIF'] - df['MACD']
    return df

def find_macd_red_expansion_stocks_daily(ticker_list, start_date, end_date):
    result = []
    details = []
    download_start = (pd.to_datetime(start_date) - pd.Timedelta(days=90)).strftime('%Y-%m-%d')

    for ticker in ticker_list:
        try:
            df = yf.download(ticker, start=download_start, end=end_date, interval="1d", group_by="column", auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty:
                continue

            df = compute_macd(df)
            df_filtered = df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]
            if len(df_filtered) < 3:
                continue
            recent = df_filtered.iloc[-3:].copy()

            osc_val = recent['OSC'].values.flatten()
            close_val = recent['Close'].values.flatten()

            # 判斷條件：前一日與當日皆為紅柱 > 0，且當日 OSC 大於前一日 OSC
            is_selected = osc_val[-2] > 0 and osc_val[-1] > 0 and osc_val[-1] > osc_val[-2]
            
            if is_selected:
                result.append(ticker)
                details.append({
                    "股票代號": ticker,
                    "最新收盤價": round(close_val[-1], 2),
                    "前日OSC": round(osc_val[-2], 4),
                    "今日OSC": round(osc_val[-1], 4),
                    "OSC增幅": round(osc_val[-1] - osc_val[-2], 4)
                })
        except Exception as e:
            pass

    return result, pd.DataFrame(details)

# 側邊欄設定
st.sidebar.header("參數設定")
default_tickers = "8099.TWO, 2352.TW, 6233.TWO, 3332.TWO, 2466.TW, 3379.TWO, 8455.TWO, 4568.TWO, 8089.TWO"
ticker_input = st.sidebar.text_area("請輸入股票代號 (以逗號分隔)", value=default_tickers, height=150)
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

today = datetime.today()
start_date = st.sidebar.date_input("搜尋起點日期", value=datetime(2025, 11, 1))
end_date = st.sidebar.date_input("搜尋終點日期", value=today)

# 執行按鈕
if st.sidebar.button("開始篩選", type="primary"):
    if not tickers:
        st.warning("請輸入至少一個股票代號！")
    else:
        with st.spinner("正在下載數據並計算 MACD..."):
            selected_stocks, df_details = find_macd_red_expansion_stocks_daily(tickers, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        st.subheader("篩選結果")
        if selected_stocks:
            st.success(f"符合 日MACD「紅縮轉紅多」股票：{', '.join(selected_stocks)}")
            st.dataframe(df_details, use_container_width=True)
        else:
            st.info("沒有符合條件的股票。")
