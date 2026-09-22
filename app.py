import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

from engine import scan_stocks


# =========================================================
# SAYFA AYARLARI
# =========================================================

st.set_page_config(
    page_title="PRO AI TRADING DASHBOARD",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# HİSSE LİSTESİ
# =========================================================

stocks = [
    "THYAO.IS",
    "CANTE.IS",
    "BIMAS.IS",
    "FROTO.IS",
    "SISE.IS",
    "ARSAN.IS",
    "ASTOR.IS",
    "SASA.IS",
    "PGSUS.IS",
    "KRONT.IS",
    "TEKTU.IS",
    "FRIGO.IS",
    "RNPOL.IS"
]


# =========================================================
# BAŞLIK
# =========================================================

st.title("📊 PRO AI TRADING DASHBOARD (BIST)")

st.write(
    "Canlı teknik analiz + AI sinyal sistemi"
)


# =========================================================
# ENGINE TARAMASI
# =========================================================

with st.spinner("🤖 Hisseler taranıyor..."):

    try:
        results = scan_stocks(stocks)

    except Exception as e:

        st.error(
            f"❌ Engine çalışırken hata oluştu:\n\n{e}"
        )

        st.stop()


# =========================================================
# ENGINE KONTROLÜ
# =========================================================

if results is None or len(results) == 0:

    st.error(
        "❌ Engine veri üretmedi. "
        "Yahoo Finance verileri alınamadı."
    )

    st.stop()


df = pd.DataFrame(results)


if df.empty:

    st.error(
        "❌ Sinyal verisi oluşturulamadı."
    )

    st.stop()


# =========================================================
# GEREKLİ SÜTUN KONTROLLERİ
# =========================================================

required_engine_columns = [
    "Hisse",
    "Fiyat",
    "AI %",
    "RSI",
    "MACD",
    "MACD Signal",
    "EMA20",
    "EMA50",
    "EMA200",
    "Hacim Oranı",
    "Momentum %",
    "Destek",
    "Direnç",
    "Stop",
    "Hedef 1",
    "Hedef 2",
    "Sinyal"
]


missing_columns = [
    column
    for column in required_engine_columns
    if column not in df.columns
]


if missing_columns:

    st.error(
        "❌ Engine'de eksik sütunlar var:"
    )

    st.write(
        missing_columns
    )

    st.write(
        "Engine sütunları:",
        list(df.columns)
    )

    st.stop()


# =========================================================
# SAYISAL SÜTUNLAR
# =========================================================

numeric_columns = [
    "Fiyat",
    "AI %",
    "RSI",
    "MACD",
    "MACD Signal",
    "EMA20",
    "EMA50",
    "EMA200",
    "Hacim Oranı",
    "Momentum %",
    "Destek",
    "Direnç",
    "Stop",
    "Hedef 1",
    "Hedef 2"
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


df["AI %"] = df["AI %"].fillna(0)


# =========================================================
# AI FİLTRESİ
# =========================================================

min_ai = st.slider(
    "🎯 Minimum AI %",
    min_value=0,
    max_value=100,
    value=50,
    step=5
)


filtered = df[
    df["AI %"] >= min_ai
].copy()


# =========================================================
# SİNYAL TABLOSU
# =========================================================

st.subheader("📋 Sinyal Tablosu")


if filtered.empty:

    st.warning(
        f"AI % {min_ai} ve üzeri sinyal bulunamadı."
    )

else:

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# GÜÇLÜ AL ADAYLARI
# =========================================================

st.subheader("🔥 Güçlü AL Adayları (80+)")


strong_buy = df[
    df["AI %"] >= 80
].copy()


if strong_buy.empty:

    st.info(
        "Şu anda AI % 80 üzeri hisse bulunmuyor."
    )

else:

    st.dataframe(
        strong_buy,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# HİSSE ANALİZİ
# =========================================================

st.subheader("🔎 Hisse Analizi")


available_stocks = [
    stock
    for stock in stocks
    if stock in df["Hisse"].values
]


if not available_stocks:

    st.warning(
        "Analiz edilebilecek hisse bulunamadı."
    )

    st.stop()


selected = st.selectbox(
    "Hisse seç",
    available_stocks
)


selected_signal = df[
    df["Hisse"] == selected
]


# =========================================================
# SEÇİLEN HİSSE ÖZETİ
# =========================================================

if not selected_signal.empty:

    row = selected_signal.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Fiyat",
            f"{row['Fiyat']:.2f}"
        )

    with col2:

        st.metric(
            "AI %",
            f"{row['AI %']:.0f}"
        )

    with col3:

        st.metric(
            "RSI",
            f"{row['RSI']:.2f}"
        )

    with col4:

        st.metric(
            "Sinyal",
            str(row["Sinyal"])
        )


# =========================================================
# GRAFİK VERİSİ
# =========================================================

with st.spinner(
    f"📈 {selected} grafik verisi yükleniyor..."
):

    try:

        data = yf.download(
            selected,
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False
        )

    except Exception as e:

        st.warning(
            f"{selected} veri alınırken hata oluştu: {e}"
        )

        st.stop()


# =========================================================
# DATA KONTROL
# =========================================================

if data is None or data.empty:

    st.warning(
        f"{selected} için grafik verisi alınamadı."
    )

    st.stop()


# =========================================================
# YAHOO FINANCE MULTIINDEX DÜZELTME
# =========================================================

if isinstance(data.columns, pd.MultiIndex):

    data.columns = (
        data.columns
        .get_level_values(0)
    )


data = data.loc[
    :,
    ~data.columns.duplicated()
]


# =========================================================
# GEREKLİ OHLC SÜTUNLARI
# =========================================================

required_columns = [
    "Open",
    "High",
    "Low",
    "Close"
]


for column in required_columns:

    if column not in data.columns:

        st.warning(
            f"{selected} için {column} "
            "verisi bulunamadı."
        )

        st.stop()


# =========================================================
# SAYISAL VERİ
# =========================================================

for column in required_columns:

    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )


data = data.dropna(
    subset=required_columns
)


if data.empty:

    st.warning(
        f"{selected} için kullanılabilir veri yok."
    )

    st.stop()


# =========================================================
# TEKNİK HESAPLAMALAR
# =========================================================

close = data["Close"]


ema20 = close.ewm(
    span=20,
    adjust=False
).mean()


ema50 = close.ewm(
    span=50,
    adjust=False
).mean()


ema200 = close.ewm(
    span=200,
    adjust=False
).mean()


# =========================================================
# BOLLINGER BANDS
# =========================================================

window = 20


ma20 = close.rolling(
    window
).mean()


std20 = close.rolling(
    window
).std()


bb_upper = (
    ma20 +
    2 * std20
)


bb_lower = (
    ma20 -
    2 * std20
)


# =========================================================
# TEKNİK GRAFİK
# =========================================================

st.subheader(
    f"📈 {selected} Teknik Grafik"
)


fig = go.Figure()


# Mum grafiği

fig.add_trace(
    go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name=selected
    )
)


# EMA20

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=ema20,
        name="EMA20",
        mode="lines"
    )
)


# EMA50

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=ema50,
        name="EMA50",
        mode="lines"
    )
)


# EMA200

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=ema200,
        name="EMA200",
        mode="lines"
    )
)


# Bollinger üst

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=bb_upper,
        name="BB Upper",
        mode="lines"
    )
)


# Bollinger alt

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=bb_lower,
        name="BB Lower",
        mode="lines"
    )
)


fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    hovermode="x unified"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# AI SİNYAL DETAYI
# =========================================================

st.subheader(
    "🤖 AI Sinyal Detayı"
)


if not selected_signal.empty:

    st.dataframe(
        selected_signal,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "Bu hisse için sinyal verisi bulunamadı."
    )


# =========================================================
# TEKNİK SEVİYELER
# =========================================================

if not selected_signal.empty:

    row = selected_signal.iloc[0]

    st.subheader(
        "🎯 Teknik Seviyeler"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Destek",
            f"{row['Destek']:.2f}"
        )


    with col2:

        st.metric(
            "Direnç",
            f"{row['Direnç']:.2f}"
        )


    with col3:

        st.metric(
            "Stop",
            f"{row['Stop']:.2f}"
        )


    with col4:

        st.metric(
            "Hedef 1",
            f"{row['Hedef 1']:.2f}"
        )


    st.metric(
        "Hedef 2",
        f"{row['Hedef 2']:.2f}"
    )


# =========================================================
# TEKNİK GÖSTERGELER
# =========================================================

if not selected_signal.empty:

    row = selected_signal.iloc[0]

    st.subheader(
        "📊 Teknik Göstergeler"
    )


    indicator_col1, indicator_col2, indicator_col3 = (
        st.columns(3)
    )


    with indicator_col1:

        st.write(
            f"**RSI:** {row['RSI']:.2f}"
        )

        st.write(
            f"**MACD:** {row['MACD']:.4f}"
        )

        st.write(
            f"**MACD Signal:** "
            f"{row['MACD Signal']:.4f}"
        )


    with indicator_col2:

        st.write(
            f"**EMA20:** {row['EMA20']:.2f}"
        )

        st.write(
            f"**EMA50:** {row['EMA50']:.2f}"
        )

        st.write(
            f"**EMA200:** {row['EMA200']:.2f}"
        )


    with indicator_col3:

        st.write(
            f"**Hacim Oranı:** "
            f"{row['Hacim Oranı']:.2f}x"
        )

        st.write(
            f"**Momentum:** "
            f"{row['Momentum %']:.2f}%"
        )


# =========================================================
# ALT BİLGİ
# =========================================================

st.divider()

st.caption(
    "⚠️ Bu dashboard teknik/algoritmik analiz amacıyla "
    "tasarlanmıştır. Veriler Yahoo Finance üzerinden alınmaktadır."
)
