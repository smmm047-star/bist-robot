# ============================================================
# PRO AI TRADING ENGINE
# BIST TECHNICAL ANALYSIS ENGINE
# ============================================================

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# AYARLAR
# ============================================================

DOWNLOAD_PERIOD = "6mo"
DOWNLOAD_INTERVAL = "1d"

MIN_DATA_LENGTH = 80


# ============================================================
# YAHOO FINANCE VERİSİNİ TEMİZLE
# ============================================================

def _download_data(symbol):
    """
    Yahoo Finance'dan veri indirir.
    MultiIndex ve 1D/2D Series problemlerini temizler.
    """

    try:
        data = yf.download(
            symbol,
            period=DOWNLOAD_PERIOD,
            interval=DOWNLOAD_INTERVAL,
            progress=False,
            auto_adjust=False,
            threads=False
        )

        if data is None or data.empty:
            return None

        # ----------------------------------------------------
        # MultiIndex düzeltme
        # ----------------------------------------------------

        if isinstance(data.columns, pd.MultiIndex):

            # Örn:
            # ('Close', 'THYAO.IS')
            # ('Open', 'THYAO.IS')

            level0 = data.columns.get_level_values(0)

            if all(
                column in level0
                for column in ["Open", "High", "Low", "Close"]
            ):
                data.columns = level0

            else:
                data.columns = [
                    str(col[0])
                    if isinstance(col, tuple)
                    else str(col)
                    for col in data.columns
                ]

        # Duplicate kolonları temizle
        data = data.loc[
            :,
            ~data.columns.duplicated()
        ]

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for column in required:

            if column not in data.columns:
                return None

            # ------------------------------------------------
            # DataFrame yerine Series olduğundan emin ol
            # ------------------------------------------------

            series = data[column]

            if isinstance(series, pd.DataFrame):

                series = series.iloc[:, 0]

            data[column] = pd.to_numeric(
                series,
                errors="coerce"
            )

        data = data.dropna(
            subset=[
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        if len(data) < MIN_DATA_LENGTH:
            return None

        return data

    except Exception:
        return None


# ============================================================
# GÜVENLİ SERIES
# ============================================================

def _safe_series(data, column):

    try:

        if column not in data.columns:
            return pd.Series(
                index=data.index,
                dtype=float
            )

        series = data[column]

        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]

        series = pd.to_numeric(
            series,
            errors="coerce"
        )

        return series.astype(float)

    except Exception:

        return pd.Series(
            index=data.index,
            dtype=float
        )


# ============================================================
# EMA
# ============================================================

def calculate_ema(series, period):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()


# ============================================================
# RSI
# ============================================================

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

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

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan
    )

    rsi = 100 - (
        100 / (1 + rs)
    )

    # Sürekli yükselen hisselerde RSI = 100 olabilir
    rsi = rsi.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return rsi.fillna(50)


# ============================================================
# MACD
# ============================================================

def calculate_macd(series):

    ema12 = series.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = series.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    histogram = macd - signal

    return macd, signal, histogram


# ============================================================
# HACİM ORANI
# ============================================================

def calculate_volume_ratio(volume, period=20):

    average_volume = volume.rolling(
        period
    ).mean()

    ratio = volume / average_volume.replace(
        0,
        np.nan
    )

    return ratio.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(1.0)


# ============================================================
# MOMENTUM
# ============================================================

def calculate_momentum(series, period=10):

    momentum = (
        series / series.shift(period) - 1
    ) * 100

    return momentum.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)


# ============================================================
# DESTEK / DİRENÇ
# ============================================================

def calculate_support_resistance(data):

    close = _safe_series(
        data,
        "Close"
    )

    high = _safe_series(
        data,
        "High"
    )

    low = _safe_series(
        data,
        "Low"
    )

    # Son 30 günlük bölge
    recent_close = close.tail(30)
    recent_high = high.tail(30)
    recent_low = low.tail(30)

    if recent_close.empty:
        return (
            float(close.iloc[-1]),
            float(close.iloc[-1])
        )

    # Destek
    support_candidates = [
        recent_low.min(),
        recent_close.quantile(0.20),
        close.tail(20).min()
    ]

    # Direnç
    resistance_candidates = [
        recent_high.max(),
        recent_close.quantile(0.80),
        close.tail(20).max()
    ]

    support = min(
        x for x in support_candidates
        if pd.notna(x)
    )

    resistance = max(
        x for x in resistance_candidates
        if pd.notna(x)
    )

    current_price = float(
        close.iloc[-1]
    )

    # Mantıksal düzeltme
    if support >= current_price:
        support = current_price * 0.97

    if resistance <= current_price:
        resistance = current_price * 1.03

    return (
        float(support),
        float(resistance)
    )


# ============================================================
# STOP
# ============================================================

def calculate_stop(
    price,
    support,
    ema20
):

    # Desteğin biraz altında
    support_stop = support * 0.97

    # EMA20 altında alternatif
    ema_stop = ema20 * 0.97

    stop = min(
        support_stop,
        ema_stop
    )

    # Stop fiyatın çok uzağına gitmesin
    if stop <= 0:
        stop = price * 0.95

    return float(stop)


# ============================================================
# HEDEFLER
# ============================================================

def calculate_targets(
    price,
    support,
    resistance
):

    risk = price - support

    # Risk çok küçükse minimum değer
    if risk <= 0:
        risk = price * 0.03

    # Hedef 1
    target1 = max(
        resistance,
        price + risk * 1.5
    )

    # Hedef 2
    target2 = max(
        target1 * 1.08,
        price + risk * 2.5
    )

    return (
        float(target1),
        float(target2)
    )


# ============================================================
# AI SKORU
# ============================================================

def calculate_ai_score(
    price,
    rsi,
    macd,
    macd_signal,
    ema20,
    ema50,
    ema200,
    volume_ratio,
    momentum
):

    score = 0.0

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if 50 <= rsi <= 65:
        score += 15

    elif 45 <= rsi < 50:
        score += 8

    elif 65 < rsi <= 72:
        score += 10

    elif rsi > 72:
        score += 4

    elif rsi < 30:
        # Aşırı satım = tepki ihtimali
        score += 5

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    if macd > macd_signal:
        score += 15

        if macd > 0:
            score += 5

    else:
        score += 3

    # --------------------------------------------------------
    # EMA TREND
    # --------------------------------------------------------

    if price > ema20:
        score += 10

    if price > ema50:
        score += 10

    if price > ema200:
        score += 10

    # EMA sıralaması
    if (
        ema20 > ema50
        and ema50 > ema200
    ):
        score += 10

    # --------------------------------------------------------
    # HACİM
    # --------------------------------------------------------

    if volume_ratio >= 1.5:
        score += 10

    elif volume_ratio >= 1.2:
        score += 7

    elif volume_ratio >= 1.0:
        score += 4

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    if momentum >= 10:
        score += 10

    elif momentum >= 5:
        score += 7

    elif momentum > 0:
        score += 4

    # --------------------------------------------------------
    # SCORE SINIRI
    # --------------------------------------------------------

    score = max(
        0,
        min(
            100,
            score
        )
    )

    return float(score)


# ============================================================
# SİNYAL
# ============================================================

def calculate_signal(
    ai_score,
    rsi,
    macd,
    macd_signal,
    price,
    ema20,
    ema50,
    volume_ratio
):

    # Güçlü AL
    if (
        ai_score >= 80
        and price > ema20
        and macd > macd_signal
    ):
        return "🟢 GÜÇLÜ AL"

    # AL
    if (
        ai_score >= 65
        and price > ema50
        and macd >= macd_signal
    ):
        return "🟢 AL"

    # Güçlü SAT
    if (
        ai_score <= 25
        and price < ema50
        and macd < macd_signal
    ):
        return "🔴 GÜÇLÜ SAT"

    # SAT
    if (
        ai_score <= 40
        and price < ema20
    ):
        return "🔴 SAT"

    # Aşırı alım
    if (
        rsi >= 75
        and ai_score < 70
    ):
        return "🟠 AŞIRI ALIM"

    return "🟡 BEKLE"


# ============================================================
# TEK HİSSE ANALİZİ
# ============================================================

def analyze_stock(symbol):

    try:

        data = _download_data(
            symbol
        )

        if data is None:
            return None

        close = _safe_series(
            data,
            "Close"
        )

        volume = _safe_series(
            data,
            "Volume"
        )

        high = _safe_series(
            data,
            "High"
        )

        low = _safe_series(
            data,
            "Low"
        )

        if close.empty:
            return None

        # ----------------------------------------------------
        # GÖSTERGELER
        # ----------------------------------------------------

        ema20_series = calculate_ema(
            close,
            20
        )

        ema50_series = calculate_ema(
            close,
            50
        )

        ema200_series = calculate_ema(
            close,
            200
        )

        rsi_series = calculate_rsi(
            close,
            14
        )

        macd_series, signal_series, histogram_series = calculate_macd(
            close
        )

        volume_ratio_series = calculate_volume_ratio(
            volume,
            20
        )

        momentum_series = calculate_momentum(
            close,
            10
        )

        # ----------------------------------------------------
        # SON DEĞERLER
        # ----------------------------------------------------

        price = float(
            close.iloc[-1]
        )

        ema20 = float(
            ema20_series.iloc[-1]
        )

        ema50 = float(
            ema50_series.iloc[-1]
        )

        ema200 = float(
            ema200_series.iloc[-1]
        )

        rsi = float(
            rsi_series.iloc[-1]
        )

        macd = float(
            macd_series.iloc[-1]
        )

        macd_signal = float(
            signal_series.iloc[-1]
        )

        volume_ratio = float(
            volume_ratio_series.iloc[-1]
        )

        momentum = float(
            momentum_series.iloc[-1]
        )

        # ----------------------------------------------------
        # DESTEK / DİRENÇ
        # ----------------------------------------------------

        support, resistance = calculate_support_resistance(
            data
        )

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        stop = calculate_stop(
            price,
            support,
            ema20
        )

        # ----------------------------------------------------
        # HEDEFLER
        # ----------------------------------------------------

        target1, target2 = calculate_targets(
            price,
            support,
            resistance
        )

        # ----------------------------------------------------
        # AI SCORE
        # ----------------------------------------------------

        ai_score = calculate_ai_score(
            price=price,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            ema20=ema20,
            ema50=ema50,
            ema200=ema200,
            volume_ratio=volume_ratio,
            momentum=momentum
        )

        # ----------------------------------------------------
        # SİNYAL
        # ----------------------------------------------------

        signal = calculate_signal(
            ai_score=ai_score,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            price=price,
            ema20=ema20,
            ema50=ema50,
            volume_ratio=volume_ratio
        )

        # ----------------------------------------------------
        # SONUÇ
        # ----------------------------------------------------

        return {

            "Hisse": symbol,

            "Fiyat": round(
                price,
                2
            ),

            "AI %": round(
                ai_score,
                1
            ),

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
                ema20,
                2
            ),

            "EMA50": round(
                ema50,
                2
            ),

            "EMA200": round(
                ema200,
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
            ),

            "Sinyal": signal
        }

    except Exception as e:

        print(
            f"{symbol} analiz hatası: {e}"
        )

        return None


# ============================================================
# TÜM HİSSELERİ TARA
# ============================================================

def scan_stocks(stocks):

    results = []

    if stocks is None:
        return results

    for symbol in stocks:

        try:

            result = analyze_stock(
                symbol
            )

            if result is not None:
                results.append(
                    result
                )

        except Exception as e:

            print(
                f"{symbol} tarama hatası: {e}"
            )

            continue

    return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_stocks = [
        "THYAO.IS",
        "ASELS.IS",
        "ASTOR.IS",
        "KRONT.IS"
    ]

    results = scan_stocks(
        test_stocks
    )

    if results:

        df = pd.DataFrame(
            results
        )

        print(
            "\n===== PRO AI ENGINE =====\n"
        )

        print(
            df.to_string(
                index=False
            )
        )

    else:

        print(
            "Veri alınamadı."
        )
