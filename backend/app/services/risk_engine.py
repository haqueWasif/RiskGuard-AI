from typing import Dict, Any, Optional

class RiskEngine:
    """
    Calculates position sizing and risk guardrails.
    Ref: Section 4 - Risk Calculations
    Strictly forbids: Target Prices, ROI predictions, Win Rates.
    """

    def calculate(self, 
                  current_price: float, 
                  atr: float, 
                  atr_mean_50: float, 
                  balance: float, 
                  risk_pct: float = 0.01) -> Dict[str, Any]:
        """
        Computes risk metrics based on current volatility.
        
        Args:
            current_price: Latest close price.
            atr: Current ATR(14) value.
            atr_mean_50: Average ATR over last 50 periods (for Flash Crash detection).
            balance: Account balance in USD.
            risk_pct: Risk per trade as decimal (e.g., 0.01 for 1%).
        """

        # --- 1. Validate Inputs (Guardrails) ---
        # "Risk % (max 2% allowed in UI)" 
        # We enforce this cap in the backend for safety.
        safe_risk_pct = min(risk_pct, 0.02)
        
        if safe_risk_pct != risk_pct:
            warning_risk = "Risk capped at 2% max per system rules."
        else:
            warning_risk = None

        # --- 2. Calculate Stop Width (The "R" Unit) ---
        # Formula: Min_Stop_Width = 1.5 * ATR(14) 
        stop_width = 1.5 * atr
        
        # --- 3. Calculate Position Size ---
        # Formula: Position_Size = (Balance * Risk_Pct) / Stop_Width 
        # Risk Amount ($) = Balance * Risk_Pct
        risk_amount_usd = balance * safe_risk_pct
        
        if stop_width > 0:
            position_size_units = risk_amount_usd / stop_width
        else:
            position_size_units = 0

        # --- 4. Volatility Multiples (Not "Targets") ---
        # "Display: 2R Distance = Current Price + (2* Stop_Width)" [cite: 50]
        # We provide the absolute distance so the UI can map it to Long or Short.
        dist_1r = stop_width
        dist_2r = 2 * stop_width
        dist_3r = 3 * stop_width

        # --- 5. Flash Crash Detection (Edge Case) ---
        # "ATR spikes > 500% of mean" -> Warning Banner 
        flash_crash_warning = False
        if atr_mean_50 > 0 and atr > (atr_mean_50 * 5.0):
            flash_crash_warning = True

        # --- 6. Construct JSON Output ---
        return {
            "risk_parameters": {
                "account_balance": balance,
                "risk_percentage_used": safe_risk_pct,
                "risk_amount_usd": round(risk_amount_usd, 2)
            },
            "stop_loss_guardrails": {
                "atr_value": round(atr, 4),
                "min_stop_width_price": round(stop_width, 4), # This is 1 R
                "formula": "1.5 * ATR(14)"
            },
            "position_sizing": {
                "recommended_units": round(position_size_units, 4),
                "notional_value": round(position_size_units * current_price, 2)
            },
            "volatility_distances": {
                "1R_distance": round(dist_1r, 4),
                "2R_distance": round(dist_2r, 4),
                "3R_distance": round(dist_3r, 4),
                "note": "Distances are volatility-based, not predictive targets."
            },
            "warnings": {
                "risk_cap_active": (warning_risk is not None),
                "flash_crash_detected": flash_crash_warning,
                "message": "Extreme Volatility Detected. Standard risk metrics may fail." if flash_crash_warning else warning_risk
            }
        }