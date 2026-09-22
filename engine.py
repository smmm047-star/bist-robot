```python
import yfinance as yf
import pandas as pd
import numpy as np


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

def get_series(df, column):
    """
    yfinance bazen normal kolon, bazen MultiIndex döndürür.
    Her durumda tek boyutlu Series üretir.
    """

    if column not in df.columns and not isinstance(df.columns, pd.MultiIndex):
        return pd.Series(dtype="float64")

    try:
        data = df[column]

        # DataFrame geldiyse ilk sütunu al
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]

        return pd.to_numeric(data, errors="coerce").dropna()

    except Exception:
        return pd.Series(dtype="float64")


def calculate_rsi(close, period=14):
    """
    RSI hesaplama
    """

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(close):
    """
    MACD
    """

    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    macd_line = ema12 - ema26

    signal_line = macd_line.ewm(
        span=9,
        adjust=False
    ).mean()

    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


# =========================================================
# ANA SCANNER
# =========================================================

def scan_stocks(stocks):

    results = []

    print("========================================")
    print("BIST AI SCANNER BASLADI")
    print("========================================")

    for symbol in stocks:

        try:

            print(f"{symbol} taraniyor...")

            # -------------------------------------------------
            # VERİ ÇEK
            # -------------------------------------------------

            df = yf.download(
                symbol,
                period="1y",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False
            )

            if df is None or df.empty:
                print(f"{symbol}: veri yok")
                continue

            # -------------------------------------------------
            # MULTIINDEX TEMİZLE
            # -------------------------------------------------

            if isinstance(df.columns, pd.MultiIndex):

                # Örnek:
                # ('Close', 'THYAO.IS')
                # ('Volume', 'THYAO.IS')

                try:
                    df.columns = df.columns.get_level_values(0)
                except Exception:
                    df.columns = [
                        col[0] if isinstance(col, tuple) else col
                        for col in df.columns
                    ]

            # Aynı isimli kolonları temizle
            df = df.loc[:, ~df.columns.duplicated()]

            # -------------------------------------------------
            # CLOSE / VOLUME
            # -------------------------------------------------

            close = get_series(df, "Close")
            volume = get_series(df, "Volume")

            if close.empty:
                print(f"{symbol}: Close verisi bulunamadi")
                continue

            if volume.empty:
                volume = pd.Series(
                    0,
                    index=close.index,
                    dtype="float64"
                )

            # -------------------------------------------------
            # VERİ SAYISI
            # -------------------------------------------------

            if len(close) < 60:
                print(
                    f"{symbol}: yetersiz veri "
                    f"({len(close)} gün)"
                )
                continue

            # -------------------------------------------------
            # SON VERİLER
            # -------------------------------------------------

            close = close.astype(float)
            volume = volume.astype(float)

            last_price = float(close.iloc[-1])

            # -------------------------------------------------
            # EMA
            # -------------------------------------------------

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

            # -------------------------------------------------
            # RSI
            # -------------------------------------------------

            rsi = calculate_rsi(close)

            # -------------------------------------------------
            # MACD
            # -------------------------------------------------

            macd_line, signal_line, macd_hist = calculate_macd(
                close
            )

            # -------------------------------------------------
            # BOLLINGER BANDS
            # -------------------------------------------------

            bb_middle = close.rolling(20).mean()

            bb_std = close.rolling(20).std()

            bb_upper = bb_middle + (2 * bb_std)

            bb_lower = bb_middle - (2 * bb_std)

            # -------------------------------------------------
            # HACİM
            # -------------------------------------------------

            volume_avg20 = volume.rolling(20).mean()

            last_volume = float(volume.iloc[-1])

            avg_volume = float(
                volume_avg20.iloc[-1]
            ) if not pd.isna(volume_avg20.iloc[-1]) else 0

            volume_ratio = 0

            if avg_volume > 0:
                volume_ratio = last_volume / avg_volume

            # -------------------------------------------------
            # MOMENTUM
            # -------------------------------------------------

            momentum_5 = 0

            if len(close) >= 6:

                old_price = float(close.iloc[-6])

                if old_price > 0:
                    momentum_5 = (
                        (last_price / old_price) - 1
                    ) * 100

            # -------------------------------------------------
            # DESTEK / DİRENÇ
            # -------------------------------------------------

            support = float(
                close.tail(20).min()
            )

            resistance = float(
                close.tail(20).max()
            )

            # -------------------------------------------------
            # SON İNDİKATÖR DEĞERLERİ
            # -------------------------------------------------

            last_ema20 = float(ema20.iloc[-1])
            last_ema50 = float(ema50.iloc[-1])
            last_ema200 = float(ema200.iloc[-1])

            last_rsi = float(rsi.iloc[-1])

            last_macd = float(macd_line.iloc[-1])
            last_macd_signal = float(signal_line.iloc[-1])

            last_bb_upper = float(bb_upper.iloc[-1])
            last_bb_lower = float(bb_lower.iloc[-1])

            # -------------------------------------------------
            # SCORE
            # -------------------------------------------------

            score = 0

            # =================================================
            # 1 - EMA TREND
            # =================================================

            if last_ema20 > last_ema50:
                score += 15

            if last_ema50 > last_ema200:
                score += 10

            if last_price > last_ema20:
                score += 5

            # =================================================
            # 2 - MOMENTUM
            # =================================================

            if momentum_5 > 0:
                score += 10

            if momentum_5 > 3:
                score += 5

            # =================================================
            # 3 - RSI
            # =================================================

            if 40 <= last_rsi < 70:
                score += 15

            elif 30 <= last_rsi < 40:
                score += 10

            elif last_rsi >= 70:
                score -= 5

            # =================================================
            # 4 - MACD
            # =================================================

            if last_macd > last_macd_signal:
                score += 15

            if last_macd > 0:
                score += 5

            # =================================================
            # 5 - HACİM
            # =================================================

            if volume_ratio >= 2:
                score += 15

            elif volume_ratio >= 1.5:
                score += 10

            elif volume_ratio >= 1.2:
                score += 5

            # =================================================
            # 6 - BOLLINGER
            # =================================================

            if last_price > last_bb_lower:

                if last_price < last_bb_upper:
                    score += 5

            if last_price > last_bb_upper:
                score -= 5

            # =================================================
            # SCORE SINIRLA
            # =================================================

            score = max(0, min(100, int(score)))

            ai_percent = score

            # -------------------------------------------------
            # SİNYAL
            # -------------------------------------------------

            if score >= 80:

                signal = "🟢 STRONG BUY"

            elif score >= 65:

                signal = "🟢 BUY"

            elif score >= 50:

                signal = "🟡 WATCH"

            elif score >= 35:

                signal = "🟠 WEAK"

            else:

                signal = "🔴 SELL"

            # -------------------------------------------------
            # STOP LOSS
            # -------------------------------------------------

            stop_loss = last_price * 0.95

            # Destek fiyatı daha yakınsa onu kullan
            if support < last_price:

                support_stop = support * 0.98

                if support_stop > stop_loss:
                    stop_loss = support_stop

            # -------------------------------------------------
            # HEDEF
            # -------------------------------------------------

            target_1 = last_price * 1.05
            target_2 = last_price * 1.10

            if resistance > last_price:

                target_1 = resistance

            # -------------------------------------------------
            # SONUÇ
            # -------------------------------------------------

            results.append({

                "Hisse": symbol,

                "Fiyat": round(last_price, 2),

                "AI %": int(ai_percent),

                "Sinyal": signal,

                "RSI": round(last_rsi, 2),

                "MACD": round(last_macd, 4),

                "MACD Signal": round(
                    last_macd_signal,
                    4
                ),

                "EMA20": round(
                    last_ema20,
                    2
                ),

                "EMA50": round(
                    last_ema50,
                    2
                ),

                "EMA200": round(
                    last_ema200,
                    2
                ),

                "Hacim Oranı": round(
                    volume_ratio,
                    2
                ),

                "Momentum %": round(
                    momentum_5,
                    2
                ),

                "Destek": round(
                    support,
                    2
                ),

                "Direnç": round(
                    resistance,
                    2
                ),

                "Stop": round(
                    stop_loss,
                    2
                ),

                "Hedef 1": round(
                    target_1,
                    2
                ),

                "Hedef 2": round(
                    target_2,
                    2
                )
            })

            print(
                f"{symbol}: "
                f"{last_price:.2f} | "
                f"AI {score}% | "
                f"{signal}"
            )

        except Exception as e:

            print(
                f"{symbol} ERROR: "
                f"{type(e).__name__}: {e}"
            )

            continue

    print("========================================")
    print(
        f"SCAN TAMAMLANDI: "
        f"{len(results)} hisse"
    )
    print("========================================")

    return results
```
