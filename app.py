
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

st.set_page_config(page_title="公司成長潛力分析", layout="centered")
st.title("📈 公司成長潛力分析機器人")

st.write("輸入任一上市公司代碼（如 AAPL、TSLA、2330.TW）來分析其過去五年財務數據與成長潛力。")

def cagr(start, end, periods):
    return (end / start)**(1/periods) - 1 if start > 0 else 0

def safe_get(dataframe, column, fill_value=0):
    return dataframe[column] if column in dataframe.columns else pd.Series([fill_value]*5)

def standardize_series(series, target_len=5):
    values = series.dropna().iloc[::-1].values
    if len(values) >= target_len:
        return values[:target_len]
    else:
        return np.pad(values, (0, target_len - len(values)), 'constant', constant_values=np.nan)

def analyze_company(ticker):
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials.T
        cashflow = stock.cashflow.T
        balance_sheet = stock.balance_sheet.T
        info = stock.info

        revenue = standardize_series(safe_get(financials, 'Total Revenue'))
        net_income = standardize_series(safe_get(financials, 'Net Income'))
        gross_profit = standardize_series(safe_get(financials, 'Gross Profit'))
        cfo = standardize_series(safe_get(cashflow, 'Total Cash From Operating Activities'))
        capex = standardize_series(safe_get(cashflow, 'Capital Expenditures'))
        total_assets = standardize_series(safe_get(balance_sheet, 'Total Assets'))
        shareholder_equity = standardize_series(safe_get(balance_sheet, 'Total Stockholder Equity'))
        interest_expense = standardize_series(safe_get(financials, 'Interest Expense'))
        ebit = standardize_series(safe_get(financials, 'EBIT'))

        if len(revenue) < 2 or len(net_income) < 2:
            st.error("❌ 主要財報資料不足，無法分析該公司。")
            return

        years = len(revenue) - 1
        revenue_cagr = cagr(revenue[0], revenue[-1], years)
        netincome_cagr = cagr(net_income[0], net_income[-1], years)

        gross_margin = gross_profit / revenue
        net_margin = net_income / revenue
        fcf = cfo + capex
        roa = net_income / total_assets
        roe = net_income / shareholder_equity

        with np.errstate(divide='ignore', invalid='ignore'):
            interest_coverage = np.where(interest_expense != 0, ebit / (-interest_expense), np.nan)
            d_to_e = np.where(shareholder_equity != 0, (total_assets - shareholder_equity) / shareholder_equity, np.nan)

        score = 100
        analysis = []

        if revenue_cagr > 0.1:
            analysis.append(f"✅ 營收 CAGR：{revenue_cagr:.2%}")
        else:
            score -= 10
            analysis.append(f"❌ 營收 CAGR：{revenue_cagr:.2%}")

        if netincome_cagr > 0.1:
            analysis.append(f"✅ 淨利 CAGR：{netincome_cagr:.2%}")
        else:
            score -= 10
            analysis.append(f"❌ 淨利 CAGR：{netincome_cagr:.2%}")

        if np.all(np.diff(gross_margin[~np.isnan(gross_margin)]) >= 0):
            analysis.append("✅ 毛利率持續上升")
        else:
            score -= 5
            analysis.append("❌ 毛利率不穩")

        if np.all(np.diff(net_margin[~np.isnan(net_margin)]) >= 0):
            analysis.append("✅ 淨利率持續上升")
        else:
            score -= 5
            analysis.append("❌ 淨利率不穩")

        if np.all(cfo > 0):
            analysis.append("✅ 營業現金流為正")
        else:
            score -= 5
            analysis.append("❌ 營業現金流異常")

        if np.all(fcf > 0):
            analysis.append("✅ 自由現金流為正")
        else:
            score -= 5
            analysis.append("❌ 自由現金流異常")

        if np.nanmean(roe) > 0.1:
            analysis.append("✅ ROE 穩定高")
        else:
            score -= 5
            analysis.append("❌ ROE 偏低")

        if d_to_e[-1] < 1.5:
            analysis.append("✅ 財務結構穩健")
        else:
            score -= 10
            analysis.append("❌ 負債比偏高")

        if interest_coverage[-1] > 3:
            analysis.append("✅ 利息保障良好")
        else:
            score -= 10
            analysis.append("❌ 償債能力不足")

        try:
            pe_ratio = info.get('trailingPE', None)
            if pe_ratio and netincome_cagr > 0:
                peg = pe_ratio / (netincome_cagr * 100)
                analysis.append(f"📌 PEG 預期成長比：{peg:.2f}（越接近 1 越合理）")
            else:
                analysis.append("📌 PEG 無法計算（可能缺 PE 或成長率為 0）")
        except:
            analysis.append("📌 PEG 無法取得")

        st.subheader("📋 分析報告")
        for a in analysis:
            st.write(a)

        st.subheader("📊 綜合成長潛力評分")
        st.write(f"### {score}/100")
        if score >= 80:
            st.success("🟢 評價：高成長潛力公司")
        elif score >= 60:
            st.info("🟡 評價：穩健成長公司")
        elif score >= 40:
            st.warning("🟠 評價：成長潛力中等")
        else:
            st.error("🔴 評價：潛力不足，須謹慎")
    except Exception as e:
        st.error(f"❌ 發生錯誤：{e}")

ticker_input = st.text_input("輸入公司代碼：", "TSLA")
if st.button("分析公司"):
    with st.spinner("分析中..."):
        analyze_company(ticker_input)
