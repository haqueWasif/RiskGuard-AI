import pandas as pd
import ta # The new stable library
import numpy as np

class IndicatorService:
    """
    Computes the 'Safe Metrics' used for structural analysis.
    Uses the 'ta' library for stability on Railway.
    """

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies technical indicators to the OHLCV DataFrame.
        """
        # Ensure sufficient data depth
        if len(df) < 14:
             raise ValueError("Insufficient data. Need at least 14 candles.")

        # --- 1. Trend Strength (ADX) ---
        # Formula: Average Directional Index (14-period)
        # We catch warnings because ADX can be fussy with mostly-flat data
        try:
            adx_indicator = ta.trend.ADXIndicator(
                high=df['high'], 
                low=df['low'], 
                close=df['close'], 
                window=14
            )
            df['ADX'] = adx_indicator.adx()
        except Exception:
            df['ADX'] = 0 # Fallback

        # --- 2. Trend Bias (EMA Delta) ---
        # Formula: (Close - EMA_200) / EMA_200
        ema_indicator = ta.trend.EMAIndicator(close=df['close'], window=200)
        df['EMA_200'] = ema_indicator.ema_indicator()
        
        # Handle case where data is too short for EMA 200
        if df['EMA_200'].isnull().all():
             df['EMA_200'] = df['close'] # Fallback
        
        df['EMA_Delta'] = (df['close'] - df['EMA_200']) / df['EMA_200']

        # --- 3. Volatility Norm (ATR) ---
        # Formula: Average True Range (14-period)
        atr_indicator = ta.volatility.AverageTrueRange(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            window=14
        )
        df['ATR'] = atr_indicator.average_true_range()

        # --- 4. Volatility Regime (BBW_Pct) ---
        # Standard settings (20, 2)
        bb_indicator = ta.volatility.BollingerBands(
            close=df['close'], 
            window=20, 
            window_dev=2
        )
        
        df['BB_Upper'] = bb_indicator.bollinger_hband()
        df['BB_Lower'] = bb_indicator.bollinger_lband()
        df['BB_Mid']   = bb_indicator.bollinger_mavg()
        
        # Calculate Width % (Avoid division by zero)
        df['BBW_Pct'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid'].replace(0, np.nan)
        df['BBW_Pct'] = df['BBW_Pct'].fillna(0)

        # --- 5. Momentum (RSI) ---
        # Formula: Relative Strength Index (14-period)
        rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=14)
        df['RSI'] = rsi_indicator.rsi()

        # --- 6. Volume Delta ---
        # Formula: Volume / SMA_Volume(20)
        # 'ta' usually works on price, so we do this one manually with pandas (safer)
        df['Vol_SMA_20'] = df['volume'].rolling(window=20).mean()
        
        df['Volume_Delta'] = df.apply(
            lambda row: row['volume'] / row['Vol_SMA_20'] if row['Vol_SMA_20'] > 0 else 0, 
            axis=1
        )

        # --- 7. Helper for Regime Classifier (Percentile Rank) ---
        # "Compared against its own 50-period history"
        df['BBW_Percentile'] = df['BBW_Pct'].rolling(window=50).rank(pct=True)
        
        # Fill NaNs created by rolling windows to prevent JSON errors later
        df.fillna(0, inplace=True)

        return df

    def get_latest_metrics(self, df: pd.DataFrame) -> dict:
        """
        Returns the latest row as a dictionary for the API response.
        """
        latest = df.iloc[-1]
        return {
            "timestamp": latest['timestamp'],
            "close": latest['close'],
            "metrics": {
                "adx": round(float(latest['ADX']), 2),
                "ema_delta": round(float(latest['EMA_Delta']), 4),
                "atr": round(float(latest['ATR']), 4),
                "bbw_pct": round(float(latest['BBW_Pct']), 4),
                "bbw_percentile": round(float(latest['BBW_Percentile']), 2), 
                "rsi": round(float(latest['RSI']), 2),
                "volume_delta": round(float(latest['Volume_Delta']), 2)
            }
        }
