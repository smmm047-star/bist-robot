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

# ENGINE TARAMA

# =========================================================

with st.spinner("🤖 Hisseler taranıyor..."):

```
results = scan_stocks(stocks)
```

# =========================================================

# ENGINE KONTROL

# =========================================================

if results is None or len(results) == 0:

```
st.error(
    "❌ Engine veri üretmedi. "
    "Yahoo Finance verileri alınamadı veya hisseler taranamadı."
)

st.stop()
```

# =========================================================

# DATAFRAME

# =========================================================

df = pd.DataFrame(results)

if df.empty:

```
st.error(
    "❌ Sinyal verisi oluşturulamadı."
)

st.stop()
```

# =========================================================

# AI % KONTROL

# =========================================================

if "AI %" not in df.columns:

```
st.error(
    "❌ Engine 'AI %' sütununu oluşturamadı."
)

st.write(
    "Engine sütunları:",
    list(df.columns)
)

st.stop()
```

df["AI %"] = pd.to_numeric(
df["AI %"],
errors="coerce"
).fillna(0)

# =========================================================

# MINIMUM AI FİLTRESİ

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

```
st.warning(
    f"AI % {min_ai} ve üzeri sinyal bulunamadı."
)
```

else:

```
st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)
```

# =========================================================

# GÜÇLÜ AL ADAYLARI

# =========================================================

st.subheader("🔥 Güçlü AL Adayları (80+)")

strong_buy = df[
df["AI %"] >= 80
].copy()

if strong_buy.empty:

```
st.info(
    "Şu anda AI % 80 üzeri hisse bulunmuyor."
)
```

else:

```
st.dataframe(
    strong_buy,
    use_container_width=True,
    hide_index=True
)
```

# =========================================================

# HİSSE SEÇİMİ

# =========================================================

st.subheader("🔎 Hisse Analizi")

available_stocks = [
stock
for stock in stocks
if stock in df["Hisse"].values
]

if not available_stocks:

```
st.warning(
    "Analiz edilebilecek hisse bulunamadı."
)

st.stop()
```

selected = st.selectbox(
"Hisse seç",
available_stocks
)

# =========================================================

# SEÇİLEN HİSSE SİNYALİ

# =========================================================

selected_signal = df[
df["Hisse"] == selected
]

if not selected_signal.empty:

```
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
        row["Sinyal"]
    )
```

# =========================================================

# GRAFİK VERİSİ

# =========================================================

with st.spinner(
f"📈 {selected} grafik verisi yükleniyor..."
):

```
data = yf.download(
    selected,
    period="6mo",
    interval="1d",
    progress=False,
    auto_adjust=False,
    threads=False
)
```

# =========================================================

# VERİ KONTROL

# =========================================================

if data is None or data.empty:

```
st.warning(
    f"{selected} için grafik verisi alınamadı."
)

st.stop()
```

# =========================================================

# MULTIINDEX TEMİZLE

# =========================================================

if isinstance(
data.columns,
pd.MultiIndex
):

```
data.columns = (
    data.columns
    .get_level_values(0)
)
```

data = data.loc[
:,
~data.columns.duplicated()
]

# =========================================================

# GEREKLİ KOLONLAR

# =========================================================

required_columns = [
"Open",
"High",
"Low",
"Close"
]

for column in required_columns:

```
if column not in data.columns:

    st.warning(
        f"{selected} için "
        f"{column} verisi bulunamadı."
    )

    st.stop()
```

# =========================================================

# NUMERIC TEMİZLİK

# =========================================================

for column in required_columns:

```
data[column] = pd.to_numeric(
    data[column],
    errors="coerce"
)
```

data = data.dropna(
subset=required_columns
)

if data.empty:

```
st.warning(
    f"{selected} için kulla

