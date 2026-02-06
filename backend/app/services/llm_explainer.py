import json
import os
from typing import Dict, Any

# Placeholder for LLM Client (e.g., OpenAI or Google Generative AI)
# In production, use: from openai import AsyncOpenAI
# client = AsyncOpenAI(api_key=os.getenv("LLM_API_KEY"))

class NarrativeExplainer:
    """
    Agent 5: Explanation Agent (LLM Wrapper)
    Role: Summarize data into natural language using 'Risk Intelligence Audit' persona.
    Ref: Explanation Agent Prompt Pack Design.pdf
    """

    def __init__(self):
        self.model = "gpt-4-mini" # or gemini-2.0-flash [cite: 245]
        self.temperature = 0.0    # Strict determinism [cite: 246]

    async def generate_narrative(self, 
                                 regime: Dict[str, str], 
                                 alignment: Dict[str, Any],
                                 metrics: Dict[str, Any],
                                 risk: Dict[str, Any],
                                 strategy_name: str,
                                 asset_pair: str) -> Dict[str, str]:
        """
        Generates the 3-sentence JSON summary.
        Includes Hard Fallback if LLM fails.
        """
        
        # --- 1. Construct Data Payload [cite: 255] ---
        payload = f"""
        DATA PAYLOAD:
        Asset: {asset_pair}
        Current Price: {metrics.get('close', 'N/A')}
        
        1. REGIME DETECTOR:
        - Trend State: {regime.get('trend_state')} (ADX: {metrics.get('adx', 0)})
        - Volatility State: {regime.get('volatility_state')} (Percentile: {metrics.get('bbw_percentile', 0)*100}%)
        - Momentum Bias: {'Price > EMA' if metrics.get('ema_delta', 0) > 0 else 'Price < EMA'}
        
        2. STRATEGY ALIGNMENT (User Strategy: {strategy_name}):
        - Final Score: {alignment.get('alignment_score')}
        - Passing Rules: {[r['rule'] for r in alignment.get('confluence_checks', []) if r['status'] == 'PASS']}
        - FAILED Rules: {[r['rule'] for r in alignment.get('confluence_checks', []) if r['status'] == 'FAIL']}
        
        3. RISK GUARDRAILS:
        - 14-Period ATR: {metrics.get('atr', 0)}
        - Recommended Stop Width (1.5x ATR): {risk['stop_loss_guardrails']['min_stop_width_price']}
        - Max Position Size (1% Risk): {risk['position_sizing']['recommended_units']}
        """

        # --- 2. System Prompt (Immutable) [cite: 216] ---
        system_prompt = """
        You are the "Risk Intelligence Audit" engine.
        YOUR ROLE: Interpret deterministic market data into neutral, professional summaries.
        
        CRITICAL PROHIBITIONS:
        1. NO SIGNALS: Never use "Buy", "Sell", "Long", "Short".
        2. NO PREDICTIONS: Never use future tense about price.
        3. NO PROBABILITIES: Never invent win rates.
        4. NO EMOTION: Avoid "Exciting", "Safe", "Dangerous".
        
        OUTPUT FORMAT (JSON ONLY):
        {
            "market_context": "One sentence describing regime and volatility.",
            "alignment_verdict": "One sentence explaining Alignment Score based on failed/passed rules.",
            "risk_note": "One sentence highlighting stop width or position size."
        }
        """

        try:
            # --- 3. LLM Call (Simulation) ---
            # In real implementation:
            # response = await client.chat.completions.create(
            #     model=self.model,
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": f"Summarize this audit:\n{payload}"}
            #     ],
            #     temperature=self.temperature,
            #     max_tokens=150,
            #     stop=["Buy", "Sell", "Target", "Profit"] # Safety Breakers [cite: 249]
            # )
            # content = response.choices[0].message.content
            
            # SIMULATED RESPONSE for this environment:
            content = self._simulate_llm_response(regime, alignment, risk)
            
            # --- 4. Parse & Validate JSON ---
            parsed_json = json.loads(content)
            
            # Basic validation of keys
            required_keys = ["market_context", "alignment_verdict", "risk_note"]
            if not all(key in parsed_json for key in required_keys):
                raise ValueError("LLM Output missing required keys")
                
            return parsed_json

        except Exception as e:
            # --- 5. Hard Fallback (Template) ---
            print(f"LLM Error: {e}. Using Fallback.")
            return self._fallback_template(regime, alignment, risk)

    def _fallback_template(self, regime, alignment, risk) -> Dict[str, str]:
        """
        Deterministic string builder used if LLM fails or times out.
        """
        return {
            "market_context": f"Market is currently in {regime.get('trend_state')} with {regime.get('volatility_state')} volatility.",
            "alignment_verdict": f"Strategy alignment is {alignment.get('alignment_score')}. Check specific rule failures in the dashboard.",
            "risk_note": f"Volatility requires a minimum stop width of {risk['stop_loss_guardrails']['min_stop_width_price']} to avoid noise."
        }

    def _simulate_llm_response(self, regime, alignment, risk):
        """
        Simulates what the LLM would return for testing purposes.
        """
        trend = regime.get('trend_state')
        score = alignment.get('alignment_score')
        stop = risk['stop_loss_guardrails']['min_stop_width_price']
        
        return json.dumps({
            "market_context": f"The asset currently exhibits a {trend} structure with volatility measures within standard bounds.",
            "alignment_verdict": f"Strategy alignment is rated {score} due to the confluence of price action and trend definitions.",
            "risk_note": f"Current ATR values suggest a defensive stop width of {stop} is necessary to account for market noise."
        })