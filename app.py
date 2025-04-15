
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

st.set_page_config(page_title="公司成長潛力分析", layout="centered")
st.title("📈 公司成長潛力分析機器人")

st.write("輸入任一上市公司代碼（如 AAPL、TSLA、2330.TW）來分析其過去五年財務數據與成長潛力。")

def cagr(start, end, periods):
    return (end / start)**(1/periods) - 1 if start > 0 else 0

def analyze_company(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials.T
    cashflow = stock.cashflow.T
    balance_sheet = stock.balance_sheet.T
    info = stock.info

    try:
        revenue = financials['Total Revenue'].dropna().iloc[::-1].values[:5]
        net_income = financials['Net Income'].dropna().iloc[::-1].values[:5]
        gross_profit = financials['Gross Profit'].dropna().iloc[::-1].values[:5]
        cfo = cashflow['Total Cash From Operating Activities'].dropna().iloc[::-1].values[:5]
        capex = cashflow['Capital Expenditures'].dropna().iloc[::-1].values[:5]
        total_assets = balance_sheet['Total Assets'].dropna().iloc[::-1].values[:5]
        shareholder_equity = balance_sheet['Total Stockholder Equity'].dropna().iloc[::-1].values[:5]
        interest_expense = financials['Interest Expense'].dropna().iloc[::-1].values[:5]
        ebit = financials['EBIT'].dropna().iloc[::-1].values[:5]
    except KeyError:
        st.error("❌ 財報欄位缺漏，無法完整分析該公司。")
        return

    years = len(revenue) - 1
    revenue_cagr = cagr(revenue[0], revenue[-1], years)
    netincome_cagr = cagr(net_income[0], net_income[-1], years)

    gross_margin = gross_profit / revenue
    net_margin = net_income / revenue
    fcf = cfo + capex
    roa = net_income / total_assets
    roe = net_income / shareholder_equity
    interest_coverage = ebit / (-interest_expense)
    d_to_e = (total_assets - shareholder_equity) / shareholder_equity

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

    if np.all(np.diff(gross_margin) >= 0):
        analysis.append("✅ 毛利率持續上升")
    else:
        score -= 5
        analysis.append("❌ 毛利率不穩")

    if np.all(np.diff(net_margin) >= 0):
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

    if roe.mean() > 0.1:
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

ticker_input = st.text_input("輸入公司代碼：", "AAPL")
if st.button("分析公司"):
    with st.spinner("分析中..."):
        analyze_company(ticker_input)
