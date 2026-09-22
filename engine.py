import yfinance as yf
import pandas as pd
import numpy as np


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

def clean_series(series):
    """Series'i güvenli şekilde tek boyutlu numeric hale getirir."""
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]

    return pd.to_numeric(series, errors="coerce")


def calculate_rsi(close, period=14):
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(close):
    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    return macd, signal


# =========================================================
# ANA TARAMA MOTORU
# =========================================================

def scan_stocks(stocks):

    results = []

    for symbol in stocks:

        try:

            print(f"Scanning {symbol}...")

            data = yf.download(
                symbol,
                period="1y",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False
            )

            if data is None or data.empty:

                print(f"No data: {symbol}")

                continue


            # =================================================
            # MULTIINDEX TEMİZLE
            # =================================================

            if isinstance(data.columns, pd.MultiIndex):

                data.columns = data.columns.get_level_values(0)


            data = data.loc[
                :,
                ~data.columns.duplicated()
            ]


            required = [
                "Close",
                "High",
                "Low",
                "Volume"
            ]

            if not all(
                col in data.columns
                for col in required
            ):

                print(
                    f"Missing columns: {symbol}"
                )

                continue


            close = clean_series(
                data["Close"]
            )

            high = clean_series(
                data["High"]
            )

            low = clean_series(
                data["Low"]
            )

            volume = clean_series(
                data["Volume"]
            )


            df = pd.DataFrame({
                "Close": close,
                "High": high,
                "Low": low,
                "Volume": volume
            }).dropna()


            if len(df) < 60:

                print(
                    f"Not enough data: {symbol}"
                )

                continue


            # =================================================
            # GÜNCEL FİYAT
            # =================================================

            price = float(
                df["Close"].iloc[-1]
            )


            # =================================================
            # EMA
            # =================================================

            ema20 = df["Close"].ewm(
                span=20,
                adjust=False
            ).mean()

            ema50 = df["Close"].ewm(
                span=50,
                adjust=False
            ).mean()

            ema200 = df["Close"].ewm(
                span=200,
                adjust=False
            ).mean()


            e20 = float(
                ema20.iloc[-1]
            )

            e50 = float(
                ema50.iloc[-1]
            )

            e200 = float(
                ema200.iloc[-1]
            )


            # =================================================
            # RSI
            # =================================================

            rsi_series = calculate_rsi(
                df["Close"]
            )

            rsi = float(
                rsi_series.iloc[-1]
            )


            # =================================================
            # MACD
            # =================================================

            macd_series, signal_series = (
                calculate_macd(
                    df["Close"]
                )
            )

            macd = float(
                macd_series.iloc[-1]
            )

            macd_signal = float(
                signal_series.iloc[-1]
            )


            # =================================================
            # BOLLINGER
            # =================================================

            ma20 = df["Close"].rolling(
                20
            ).mean()

            std20 = df["Close"].rolling(
                20
            ).std()

            bb_upper = (
                ma20 + 2 * std20
            )

            bb_lower = (
                ma20 - 2 * std20
            )

            upper = float(
                bb_upper.iloc[-1]
            )

            lower = float(
                bb_lower.iloc[-1]
            )


            # =================================================
            # HACİM
            # =================================================

            avg_volume = (
                df["Volume"]
                .rolling(20)
                .mean()
                .iloc[-1]
            )

            current_volume = float(
                df["Volume"].iloc[-1]
            )

            volume_ratio = (
                current_volume /
                avg_volume
                if avg_volume > 0
                else 0
            )


            # =================================================
            # MOMENTUM
            # =================================================

            momentum = (
                (
                    price /
                    float(df["Close"].iloc[-6])
                ) - 1
            ) * 100


            # =================================================
            # DESTEK / DİRENÇ
            # =================================================

            support = float(
                df["Low"]
                .tail(20)
                .min()
            )

            resistance = float(
                df["High"]
                .tail(20)
                .max()
            )


            # =================================================
            # AI SKOR
            # =================================================

            score = 0


            # EMA TREND
            if e20 > e50:
                score += 15

            if e50 > e200:
                score += 10

            if price > e20:
                score += 5


            # MOMENTUM
            if momentum > 0:
                score += 10

            if momentum > 3:
                score += 5


            # RSI
            if 40 <= rsi <= 70:

                score += 15

            elif 30 <= rsi < 40:

                score += 10

            elif rsi >= 70:

                score -= 5


            # MACD
            if macd > macd_signal:

                score += 15

            if macd > 0:

                score += 5


            # HACİM
            if volume_ratio >= 2:

                score += 15

            elif volume_ratio >= 1.5:

                score += 10

            elif volume_ratio >= 1.2:

                score += 5


            # BOLLINGER
            if lower <= price <= upper:

                score += 5

            elif price > upper:

                score -= 5


            score = max(
                0,
                min(100, score)
            )


            # =================================================
            # SİNYAL
            # =================================================

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


            # =================================================
            # STOP
            # =================================================

            stop = price * 0.95

            if support < price:

                stop = max(
                    stop,
                    support
                )


            # =================================================
            # HEDEFLER
            # =================================================

            target1 = price * 1.05
            target2 = price * 1.10

            if resistance > price:

                target1 = resistance


            # =================================================
            # SONUÇ
            # =================================================

            results.append({

                "Hisse": symbol,

                "Fiyat": round(
                    price,
                    2
                ),

                "AI %": score,

                "Sinyal": signal,

                "RSI": round(
                    rsi,
                    2
                ),

                "MACD": round(
                    macd,
                    4
                ),

                "MACD Signal": round(
                    macd_signal,
                    4
                ),

                "EMA20": round(
                    e20,
                    2
                ),

                "EMA50": round(
                    e50,
                    2
                ),

                "EMA200": round(
                    e200,
                    2
                ),

                "Hacim Oranı": round(
                    volume_ratio,
                    2
                ),

                "Momentum %": round(
                    momentum,
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
                    stop,
                    2
                ),

                "Hedef 1": round(
                    target1,
                    2
                ),

                "Hedef 2": round(
                    target2,
                    2
                )

            })


        except Exception as e:

            print(
                f"ERROR {symbol}: {e}"
            )

            continue


    return results
