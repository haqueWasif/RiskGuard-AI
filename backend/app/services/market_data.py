import ccxt.async_support as ccxt  # Asynchronous for API performance
import pandas as pd
import asyncio
from datetime import datetime, timedelta

class MarketDataService:
    def __init__(self):
        # CHANGED: Switch to Kraken to avoid Binance region blocks on Railway
        # The PRD originally specified Binance, but we must adapt for deployment.
        self.exchange = ccxt.kraken({
            'enableRateLimit': True,
        })

    async def close_connection(self):
        await self.exchange.close()

    async def get_candles(self, symbol: str, timeframe: str = '4h', limit: int = 300) -> pd.DataFrame:
        """
        Fetches OHLCV data. 
        Granularity: H4 (Primary) or D1 (Context)[cite: 724, 725].
        Required Depth: Minimum 200 candles[cite: 728].
        """
        try:
            # --- KRAKEN COMPATIBILITY FIX ---
            # Kraken generally uses 'USD' instead of 'USDT'. 
            # We map the inputs so the frontend doesn't break.
            if symbol == "BTC/USDT":
                symbol = "BTC/USD"
            if symbol == "ETH/USDT":
                symbol = "ETH/USD"
            
            # 1. Fetch OHLCV (Open, High, Low, Close, Volume) [cite: 722]
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                raise ValueError(f"No data returned for {symbol}")

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 2. Edge Case: Fresh Listing (< 200 candles) 
            if len(df) < 200:
                raise ValueError("Asset too new for reliable Trend Analysis (EMA-200 req).")

            # 3. Edge Case: Data Gaps (> 3 missing candles) 
            # Calculate expected time difference based on timeframe
            timeframe_map = {'4h': 4, '1d': 24}
            hours_per_candle = timeframe_map.get(timeframe, 4) # Default to 4h if unknown
            
            # Check continuity of the last 200 candles
            df_check = df.tail(200).copy()
            df_check['time_diff'] = df_check['timestamp'].diff()
            
            # Threshold: If gap is > 3 * candle_duration
            gap_threshold = timedelta(hours=hours_per_candle * 3)
            
            # Skip first row (NaN diff)
            if (df_check['time_diff'].iloc[1:] > gap_threshold).any():
                raise ValueError("Insufficient Market Data Integrity (Data Gaps Detected).")

            # 4. Edge Case: Zero Volume 
            # Check if the latest confirmed candle has 0 volume
            if df['volume'].iloc[-1] == 0:
                # Flag Regime as Unreliable/Illiquid
                print(f"Warning: Zero volume detected for {symbol}")
                # We can choose to raise an error or just warn. 
                # For strict MVP safety, we might want to block it, but a warning is safer for now.

            return df

        except ccxt.NetworkError as e:
            raise ConnectionError(f"Network Error fetching {symbol}: {str(e)}")
        except ccxt.ExchangeError as e:
            raise ValueError(f"Exchange Error for {symbol}: {str(e)}")
        except Exception as e:
            raise e

# Usage Example (for testing inside the file)
if __name__ == "__main__":
    async def main():
        service = MarketDataService()
        try:
            # Test fetching BTC/USD (Kraken style)
            # The service handles the conversion if we pass BTC/USDT
            print("Fetching BTC/USDT (auto-converted to Kraken BTC/USD)...")
            df = await service.get_candles("BTC/USDT", "4h")
            print(f"Successfully fetched {len(df)} candles.")
            print(df.tail())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await service.close_connection()

    # Run the test
    asyncio.run(main())
