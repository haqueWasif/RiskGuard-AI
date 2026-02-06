from enum import Enum
from typing import Dict, Any

class MarketState(str, Enum):
    # Volatility States
    SQUEEZE = "SQUEEZE"         # Low Volatility (< 20th percentile)
    NORMAL = "NORMAL"           # Normal Volatility
    EXPANSION = "EXPANSION"     # High Volatility (> 80th percentile)

    # Trend States
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    RANGE = "RANGE"
    NEUTRAL = "NEUTRAL"         # For the grey area (ADX 20-25)

class RegimeClassifier:
    """
    Implements the deterministic IF/THEN logic for market classification.
    Ref: Section 3 - Market Regime Classification Rules
    """

    def classify(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """
        Classifies the market regime based on Volatility and Trend.
        
        Args:
            metrics: Dictionary containing 'bbw_percentile', 'adx', 'ema_delta'
        
        Returns:
            Dictionary with 'volatility_state', 'trend_state', and 'suggested_strategy'
        """
        
        # --- 1. Check Volatility First [cite: 18] ---
        bbw_pct_rank = metrics.get('bbw_percentile', 0.5)
        
        if bbw_pct_rank < 0.20:
            vol_state = MarketState.SQUEEZE
        elif bbw_pct_rank > 0.80:
            vol_state = MarketState.EXPANSION
        else:
            vol_state = MarketState.NORMAL

        # --- 2. Check Trend Second [cite: 22] ---
        # Note: We use EMA_Delta to determine Close vs EMA_200 relationship.
        # EMA_Delta > 0 implies Close > EMA_200.
        
        adx = metrics.get('adx', 0)
        ema_delta = metrics.get('ema_delta', 0)

        if adx > 25 and ema_delta > 0:
            trend_state = MarketState.BULL_TREND
        elif adx > 25 and ema_delta < 0:
            trend_state = MarketState.BEAR_TREND
        elif adx < 20:
            trend_state = MarketState.RANGE
        else:
            # Handling the gap between 20 and 25 (not explicitly defined in spec, treating as Neutral/Choppy)
            trend_state = MarketState.NEUTRAL

        # --- 3. Strategy Mapping [cite: 27, 30, 31] ---
        strategy = "WAIT"

        # "Breakout" Strategy requires: SQUEEZE Volatility [cite: 30]
        if vol_state == MarketState.SQUEEZE:
            strategy = "BREAKOUT_SETUP"
            
        # "Trend Following" Strategy requires: BULL/BEAR TREND + NORMAL or EXPANSION Volatility [cite: 27]
        elif (trend_state in [MarketState.BULL_TREND, MarketState.BEAR_TREND]) and \
             (vol_state in [MarketState.NORMAL, MarketState.EXPANSION]):
            strategy = "TREND_FOLLOWING"
            
        # "Mean Reversion" Strategy requires: RANGE + NORMAL Volatility [cite: 31]
        elif (trend_state == MarketState.RANGE) and (vol_state == MarketState.NORMAL):
            strategy = "MEAN_REVERSION"

        return {
            "volatility_state": vol_state.value,
            "trend_state": trend_state.value,
            "suggested_strategy": strategy
        }