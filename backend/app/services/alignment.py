from typing import Dict, List, Any

class StrategyAlignmentService:
    """
    Agent 3: Strategy Alignment Agent
    Role: Check if the user's strategy fits the current regime.
    Ref: Modular Agent Architecture - Section 3
    """

    def evaluate(self, strategy_type: str, regime: Dict[str, str]) -> Dict[str, Any]:
        """
        Determines alignment score based on Strategy vs. Regime rules.
        """
        volatility = regime.get("volatility_state") # SQUEEZE, NORMAL, EXPANSION
        trend = regime.get("trend_state")           # BULL_TREND, BEAR_TREND, RANGE
        
        score = "MEDIUM"
        blockers = []
        rules_checked = []

        # --- Rule Set [cite: 123, 124] ---
        
        # Strategy: TREND_FOLLOWING
        if strategy_type == "TREND_FOLLOWING":
            # Rule 1: Needs a Trend
            if trend in ["BULL_TREND", "BEAR_TREND"]:
                rules_checked.append({"rule": "Trend Exists", "status": "PASS", "detail": f"Market is in {trend}"})
            else:
                score = "LOW"
                blockers.append(f"Market is {trend} (Needs Trend)")
                rules_checked.append({"rule": "Trend Exists", "status": "FAIL", "detail": "No clear trend"})

            # Rule 2: Volatility check
            # Trend following works best in Normal or Expansion. Squeeze might be too early (choppy).
            if volatility == "SQUEEZE":
                score = "LOW" if score == "MEDIUM" else "LOW" 
                blockers.append("Volatility is Squeezed (Wait for expansion)")
                rules_checked.append({"rule": "Volatility Expansion", "status": "FAIL", "detail": "In Squeeze"})
            else:
                 rules_checked.append({"rule": "Volatility Expansion", "status": "PASS", "detail": "Volatility Active"})

        # Strategy: BREAKOUT
        elif strategy_type == "BREAKOUT":
            # Rule 1: Needs Squeeze (Pre-expansion)
            if volatility == "SQUEEZE":
                score = "HIGH"
                rules_checked.append({"rule": "Volatility Squeeze", "status": "PASS", "detail": "Market is Squeezed"})
            elif volatility == "EXPANSION":
                score = "LOW"
                blockers.append("Volatility already Expanded (Missed the move)") # [cite: 124]
                rules_checked.append({"rule": "Volatility Squeeze", "status": "FAIL", "detail": "Already Expanded"})
            else:
                score = "MEDIUM"
                rules_checked.append({"rule": "Volatility Squeeze", "status": "NEUTRAL", "detail": "Normal Volatility"})

        # Strategy: MEAN_REVERSION
        elif strategy_type == "MEAN_REVERSION":
            # Rule 1: Needs Range
            if trend == "RANGE":
                score = "HIGH"
                rules_checked.append({"rule": "Market Ranging", "status": "PASS", "detail": "Market is Ranging"})
            else:
                score = "LOW"
                blockers.append(f"Market is {trend} (Needs Range)")
                rules_checked.append({"rule": "Market Ranging", "status": "FAIL", "detail": "Trending"})

        # Final Confluence Logic
        if not blockers and score != "HIGH":
            score = "HIGH" # Default to High if no blockers found

        return {
            "alignment_score": score,
            "confluence_checks": rules_checked,
            "blockers": blockers
        }