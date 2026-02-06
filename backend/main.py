from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd # Needed for on-the-fly rolling calc

# Import Agents (Services)
from app.services.market_data import MarketDataService
from app.services.indicators import IndicatorService
from app.services.regime_classifier import RegimeClassifier
from app.services.alignment import StrategyAlignmentService
from app.services.risk_engine import RiskEngine
from app.services.llm_explainer import NarrativeExplainer
from fastapi.middleware.cors import CORSMiddleware # <--- Make sure this import is at the top

app = FastAPI(title="Trading Agent Orchestrator")

# --- ADD THIS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Explicitly allow the frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------

# --- Input Schema ---
class AuditRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "4h"
    strategy_type: str = "TREND_FOLLOWING" # TREND_FOLLOWING, BREAKOUT, MEAN_REVERSION
    account_balance: float = 10000.0
    risk_percentage: float = 0.01

# --- Output Schemas (UI Report) ---
class DecisionReport(BaseModel):
    report_id: str
    timestamp: str
    asset: str
    status: str
    ui_components: dict

# --- Dependency Injection ---
market_data = MarketDataService()
indicators = IndicatorService()
regime_classifier = RegimeClassifier()
alignment_agent = StrategyAlignmentService() # Agent 3
risk_engine = RiskEngine()
explainer = NarrativeExplainer() # Agent 5

@app.on_event("startup")
async def startup_event():
    pass

@app.on_event("shutdown")
async def shutdown_event():
    await market_data.close_connection()

@app.post("/api/v1/audit", response_model=DecisionReport)
async def audit_asset(request: AuditRequest):
    """
    Orchestrator Pipeline:
    1. Fetch OHLCV
    2. Compute Metrics (Agents 2, 3, 4)
    3. Generate Explanation (Agent 5)
    4. Return JSON
    """
    try:
        # --- 1. Fetch Data (Data Layer) ---
        # "Fetch raw market data once" [cite: 65]
        df = await market_data.get_candles(request.symbol, request.timeframe)
        
        # --- 2. Compute Indicators (Deterministic Core) ---
        df_analyzed = indicators.calculate_metrics(df)
        latest_metrics = indicators.get_latest_metrics(df_analyzed)
        
        # Calculate ATR Mean (50) for Flash Crash detection 
        # We compute this here to ensure the Risk Engine gets the historical context
        atr_mean_50 = df_analyzed['ATR'].rolling(window=50).mean().iloc[-1]
        if pd.isna(atr_mean_50):
            atr_mean_50 = latest_metrics['metrics']['atr'] # Fallback for very short history

        # --- 3. Classify Regime (Agent 2) ---
        # "Classify the 'battlefield' conditions" [cite: 94]
        regime_state = regime_classifier.classify(latest_metrics['metrics'])
        
        # --- 4. Check Alignment (Agent 3) ---
        # "Check if the user's strategy fits the current regime" [cite: 119]
        alignment = alignment_agent.evaluate(
            strategy_type=request.strategy_type, 
            regime=regime_state
        )
        
        # --- 5. Compute Risk (Agent 4) ---
        # "Calculate risk based on current volatility" [cite: 33]
        risk_calc = risk_engine.calculate(
            current_price=latest_metrics['close'],
            atr=latest_metrics['metrics']['atr'],
            atr_mean_50=atr_mean_50,
            balance=request.account_balance,
            risk_pct=request.risk_percentage
        )
        
        # --- 6. Generate Explanation (Agent 5) ---
        # "Aggregates their structured outputs... feeds to LLM" [cite: 65]
        # "Input Schema" includes Regime, Alignment, and Risk [cite: 178-180]
        explanation = await explainer.generate_narrative(
            regime=regime_state,
            alignment=alignment,
            metrics=latest_metrics['metrics'],
            risk=risk_calc,
            strategy_name=request.strategy_type,
            asset_pair=request.symbol
        )
        
        # --- 7. Construct UI Decision Report ---
        
        # Derive Traffic Light Color based on Alignment Score [cite: 198]
        color_map = {"HIGH": "GREEN", "MEDIUM": "YELLOW", "LOW": "RED"}
        traffic_light_color = color_map.get(alignment['alignment_score'], "GREY")
        
        return {
            "report_id": f"audit_{int(latest_metrics['timestamp'].timestamp())}",
            "timestamp": latest_metrics['timestamp'].isoformat(),
            "asset": request.symbol,
            "status": "COMPLETE",
            "ui_components": {
                "traffic_light": {
                    "color": traffic_light_color,
                    "label": f"{alignment['alignment_score']} Alignment"
                },
                "regime_card": {
                    "title": "Market Context",
                    "value": f"{regime_state['trend_state']} / {regime_state['volatility_state']}",
                    "subtext": explanation['market_context'] # Generated by LLM
                },
                "risk_card": {
                    "title": "Safety Guardrails",
                    "metric_1": f"Stop Width: ${risk_calc['stop_loss_guardrails']['min_stop_width_price']}",
                    "metric_2": f"Max Size: {risk_calc['position_sizing']['recommended_units']} Units"
                },
                "ai_analysis": {
                    "text": explanation['alignment_verdict'] + " " + explanation['risk_note'],
                    "blockers": alignment['blockers']
                }
            }
        }

    except Exception as e:
        # Catch-all for API stability
        import traceback
        traceback.print_exc()  # <--- THIS PRINTS THE REAL ERROR
        print(f"CRITICAL ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))