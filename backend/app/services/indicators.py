import pandas as pd
import pandas_ta as ta  # Requires: pip install pandas_ta
import numpy as np

class IndicatorService:
    """
    Computes the 'Safe Metrics' used for structural analysis.
    NO predictive models. NO forecasting.
    """

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies technical indicators to the OHLCV DataFrame.
        """
        # Ensure sufficient data depth
        if len(df) < 50:
            # We relax the 200 limit slightly for testing, but warn
            print(f"Warning: Data depth {len(df)} is low. EMA-200 may be unstable.")
        
        if len(df) < 14:
             raise ValueError("Insufficient data. Need at least 14 candles.")

        # --- 1. Trend Strength (ADX) ---
        # Formula: Average Directional Index (14-period)
        # pandas_ta returns 'ADX_14', 'DMP_14', 'DMN_14'
        adx_df = df.ta.adx(length=14)
        if adx_df is not None and 'ADX_14' in adx_df.columns:
            df['ADX'] = adx_df['ADX_14']
        else:
            df['ADX'] = 0 # Fallback

        # --- 2. Trend Bias (EMA Delta) ---
        # Formula: (Close - EMA_200) / EMA_200
        df['EMA_200'] = df.ta.ema(length=200)
        # Handle case where data is too short for EMA 200 (fill with Close or SMA)
        if df['EMA_200'].isnull().all():
             df['EMA_200'] = df['close'] # Fallback to prevent crash
        
        df['EMA_Delta'] = (df['close'] - df['EMA_200']) / df['EMA_200']

        # --- 3. Volatility Norm (ATR) ---
        # Formula: Average True Range (14-period)
        df['ATR'] = df.ta.atr(length=14)

        # --- 4. Volatility Regime (BBW_Pct) ---
        # Formula: (BB_Upper - BB_Lower) / BB_Mid
        # Standard settings (20, 2)
        bb_df = df.ta.bbands(length=20, std=2)
        
        # --- FIX: Dynamic Column Finding ---
        # Instead of guessing 'BBU_20_2.0', we look for columns starting with BBU/BBL/BBM
        if bb_df is not None:
            # Find the actual column names returned by pandas_ta
            bbu_col = next((c for c in bb_df.columns if c.startswith('BBU')), None)
            bbl_col = next((c for c in bb_df.columns if c.startswith('BBL')), None)
            bbm_col = next((c for c in bb_df.columns if c.startswith('BBM')), None)

            if bbu_col and bbl_col and bbm_col:
                df['BB_Upper'] = bb_df[bbu_col]
                df['BB_Lower'] = bb_df[bbl_col]
                df['BB_Mid']   = bb_df[bbm_col]
                
                # Calculate Width % strictly according to spec formula
                # Avoid division by zero
                df['BBW_Pct'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid'].replace(0, np.nan)
            else:
                 # Fallback if calculation failed
                 df['BBW_Pct'] = 0
        else:
             df['BBW_Pct'] = 0

        # --- 5. Momentum (RSI) ---
        # Formula: Relative Strength Index (14-period)
        df['RSI'] = df.ta.rsi(length=14)

        # --- 6. Volume Delta ---
        # Formula: Volume / SMA_Volume(20)
        df['Vol_SMA_20'] = df['volume'].rolling(window=20).mean()
        
        # Handle Division by Zero
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