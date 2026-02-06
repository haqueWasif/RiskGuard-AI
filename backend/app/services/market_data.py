import ccxt.async_support as ccxt  # Asynchronous for API performance
import pandas as pd
import asyncio
from datetime import datetime, timedelta

class MarketDataService:
    def __init__(self):
        # Primary Source: CCXT connecting to Binance [cite: 3]
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            # 'options': {'defaultType': 'future'} # Default to futures if needed, or spot
        })

    async def close_connection(self):
        await self.exchange.close()

    async def get_candles(self, symbol: str, timeframe: str = '4h', limit: int = 300) -> pd.DataFrame:
        """
        Fetches OHLCV data. 
        Granularity: H4 (Primary) or D1 (Context)[cite: 6, 7].
        Required Depth: Minimum 200 candles[cite: 10].
        """
        try:
            # 1. Fetch OHLCV (Open, High, Low, Close, Volume) [cite: 4]
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 2. Edge Case: Fresh Listing (< 200 candles) 
            if len(df) < 200:
                raise ValueError("Asset too new for reliable Trend Analysis (EMA-200 req).")

            # 3. Edge Case: Data Gaps (> 3 missing candles) 
            # Calculate expected time difference based on timeframe
            # Simple check: compare actual duration vs expected duration
            timeframe_map = {'4h': 4, '1d': 24}
            hours_per_candle = timeframe_map.get(timeframe, 4)
            
            # Check continuity of the last 200 candles
            df_check = df.tail(200).copy()
            df_check['time_diff'] = df_check['timestamp'].diff()
            
            # Threshold: If gap is > 3 * candle_duration (converted to timedelta)
            gap_threshold = timedelta(hours=hours_per_candle * 3)
            
            # Skip first row (NaN diff)
            if (df_check['time_diff'].iloc[1:] > gap_threshold).any():
                raise ValueError("Insufficient Market Data Integrity (Data Gaps Detected).")

            # 4. Edge Case: Zero Volume 
            # Check if the latest confirmed candle has 0 volume
            if df['volume'].iloc[-1] == 0:
                # We raise a warning or flag. The spec says "Flag Regime as Unreliable", 
                # but for data ingestion we ensures it's usable. 
                # If strictly 0 volume on recent data, it's a critical issue.
                raise ValueError("Regime Unreliable/Illiquid (Zero Volume).")

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
            # Test fetching BTC/USDT on H4 [cite: 6]
            df = await service.get_candles("BTC/USDT", "4h")
            print(f"Successfully fetched {len(df)} candles.")
            print(df.tail())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await service.close_connection()

    # Run the test
    asyncio.run(main())