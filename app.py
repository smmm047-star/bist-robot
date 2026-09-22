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
    layout="wide"
)


# =========================================================
# BIST HİSSELERİ
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
    "SASA.IS",
    "TEKTU.IS",
    "FRIGO.IS",
    "RNPOL.IS"
]


# =========================================================
# BAŞLIK
# =========================================================

st.title("📊 PRO AI TRADING DASHBOARD (BIST)")
st.write("Canlı teknik analiz + AI sinyal sistemi")


# =========================================================
# ENGINE
# =========================================================

with st.spinner("Hisseler taranıyor..."):
    results = scan_stocks(stocks)


if results is None or len(results) == 0:

    st.error(
        "Engine veri üretmiyor. "
        "Yahoo Finance verileri alınamadı veya hisseler taranamadı."
    )

    st.stop()


# =========================================================
# DATAFRAME
# =========================================================

df = pd.DataFrame(results)


if df.empty:

    st.error("Sinyal verisi oluşturulamadı.")

    st.stop()


# =========================================================
# AI % SAYISAL OLARAK GARANTİ ET
# =========================================================

if "AI %" in df.columns:

    df["AI %"] = pd.to_numeric(
        df["AI %"],
        errors="coerce"
    ).fillna(0)


# =========================================================
# FİLTRE
# =========================================================

min_ai = st.slider(
    "Minimum AI %",
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

strong_buy = df[
    df["AI %"] >= 80
].copy()


st.subheader("🔥 Güçlü AL Adayları (80+)")

if strong_buy.empty:

    st.info("Şu anda AI % 80 üzeri hisse bulunmuyor.")

else:

    st.dataframe(
        strong_buy,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# HİSSE SEÇ
# =========================================================

selected = st.selectbox(
    "Hisse seç",
    stocks
)


# =========================================================
# GRAFİK VERİSİ
# =========================================================

with st.spinner(f"{selected} grafik verisi yükleniyor..."):

    data = yf.download(
        selected,
        period="6mo",
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False
    )


if data is None or data.empty:

    st.warning(
        f"{selected} için grafik verisi alınamadı."
    )

    st.stop()


# =========================================================
# MULTIINDEX TEMİZLE
# =========================================================

if isinstance(data.columns, pd.MultiIndex):

    try:

        data.columns = data.columns.get_level_values(0)

    except Exception:

        data.columns = [
            col[0] if isinstance(col, tuple) else col
            for col in data.columns
        ]


data = data.loc[
    :,
    ~data.columns.duplicated()
]


required_columns = [
    "Open",
    "High",
    "Low",
    "Close"
]


for column in required_columns:

    if column not in data.columns:

        st.warning(
            f"{selected} için {column} verisi bulunamadı."
        )

        st.stop()


data = data.dropna(
    subset=required_columns
)


if data.empty:

    st.warning(
        f"{selected} için kullanılabilir veri yok."
    )

    st.stop()


# =========================================================
# CLOSE SERIES
# =========================================================

close = pd.to_numeric(
    data["Close"],
    errors="coerce"
).dropna()


# =========================================================
# İNDİKATÖRLER
# =========================================================

ema20 = close.ewm(
    span=20,
    adjust=False
).mean()


ema50 = close.ewm(
    span=50,
    adjust=False
).mean()


window = 20

ma = close.rolling(
    window
).mean()


std = close.rolling(
    window
).std()


bb_upper = ma + (
    2 * std
)


bb_lower = ma - (
    2 * std
)


# =========================================================
# GRAFİK
# =========================================================

st.subheader(
    f"📈 {selected} Teknik Grafik"
)


fig = go.Figure()


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


fig.add_trace(
    go.Scatter(
        x=data.index,
        y=ema20,
        name="EMA20"
    )
)


fig.add_trace(
    go.Scatter(
        x=data.index,
        y=ema50,
        name="EMA50"
    )
)


fig.add_trace(
    go.Scatter(
        x=data.index,
        y=bb_upper,
        name="BB Upper"
    )
)


fig.add_trace(
    go.Scatter(
        x=data.index,
        y=bb_lower,
        name="BB Lower"
    )
)


fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# AI DETAY
# =========================================================

st.subheader(
    "🤖 AI Sinyal Detayı"
)


match = df[
    df["Hisse"] == selected
]


if not match.empty:

    st.dataframe(
        match,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "Bu hisse için sinyal verisi bulunamadı."
    )
```
