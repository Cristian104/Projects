import json
import re
from loguru import logger
from app.core.config import settings

class QuantBrain:
    def __init__(self, host=None):
        self.brain_mode = settings.BRAIN_MODE      # readable from DB; no longer routes backends
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info(f"☁️ Gemini API configured | Model: {settings.GEMINI_MODEL}")
            except Exception as e:
                logger.warning(f"⚠️ Gemini API init failed: {e}")
        logger.info("🧠 Gemini API Brain Online")

    def _query_gemini(self, prompt: str) -> str:
        """Send a prompt to the Gemini cloud API and return the response text."""
        if self._gemini_client is None:
            logger.error("❌ Gemini client not initialised — no API key configured")
            return ""
        try:
            from google.genai import types
            response = self._gemini_client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            return response.text
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            return ""

    def _query_model(self, prompt: str, model: str = "") -> str:
        """Always dispatches to Gemini API."""
        return self._query_gemini(prompt)

    def triage_sentiment(self, ticker: str, headlines: list) -> dict:
        """STAGE 1: The 8b Analyst rapidly scores raw news."""
        logger.info(f"🕵️‍♂️ Analyst (8b) reviewing news for {ticker}...")
        
        prompt = f"""You are a rapid sentiment triage agent for a quantitative hedge fund. 
        Your task is to process raw financial headlines and assess their immediate market impact.
        
        Input Headlines for {ticker}: 
        {headlines}
        
        Read the provided headlines and output ONLY a score from 0 to 100 (0 is maximum bearish, 50 is neutral, 100 is maximum bullish) and exactly one sentence explaining the reason for interest. Do not include any conversational filler.
        
        Required Output Format:
        Score: <int>
        Reason: <1-sentence explanation>"""

        response = self._query_model(prompt)
        
        # Parse the strict output
        score = 50
        reason = "Neutral/No data parsed."
        try:
            score_match = re.search(r"Score:\s*(\d+)", response)
            reason_match = re.search(r"Reason:\s*(.*)", response)
            if score_match: score = int(score_match.group(1))
            if reason_match: reason = reason_match.group(1).strip()
        except Exception as e:
            logger.warning(f"⚠️ Analyst parsing error: {e}")

        return {"score": score, "reason": reason}

    def execute_decision(self, ticker: str, analyst_report: dict, technicals: dict, portfolio: dict, history: list = None) -> dict:
        """STAGE 2: The 14b Manager cross-checks data, memory, and issues a JSON order."""
        logger.info(f"👔 Portfolio Manager (14b) synthesizing data for {ticker}...")
        
        # Format the memory for the prompt
        memory_context = "No previous logs for this ticker."
        if history:
            memory_context = "\n".join([
                f"- Date: {h['timestamp']} | Sentiment: {h['sentiment_score']} | Order: {h['manager_order']} | Logic: {h['manager_reasoning']}" 
                for h in history
            ])

        prompt = f"""You are the Lead Execution Agent for a quantitative hedge fund. You must synthesize multiple streams of market data and your own HISTORICAL MEMORY to output a final trading decision strictly in JSON format.

        Inputs for {ticker}:
        1. Current Sentiment Triage: Score {analyst_report['score']}/100. Reason: {analyst_report['reason']}
        2. Technical Levels: {technicals}
        3. Portfolio State: {portfolio}
        4. Historical Memory (Last {len(history) if history else 0} scans):
        {memory_context}

        TEMPORAL REASONING PROTOCOL: 
        - Does the current sentiment score show an accelerating trend (upward) or a reversal?
        - If past reasoning warned of a competitor entry or data leak, check if current headlines confirm resolution or escalation.
        - Convergence is key. If logic conflicts with history, prioritize the most recent data but explain why the thesis changed.

        Output final decision as JSON object ONLY.
        
        Required JSON Schema:
        {{
            "Order": "BUY" | "SELL" | "HOLD",
            "Conviction": <float between 0.0 and 1.0>,
            "Reasoning": "<Concise synthesis including temporal context>"
        }}

        CRITICAL OUTPUT RULES:
        - Output ONLY the raw JSON object. No markdown, no code fences, no <think> blocks.
        - Do not write anything before or after the JSON.
        - The response must start with {{ and end with }}"""

        response = self._query_model(prompt)

        # Attempt 1: parse with think-tag and markdown stripping
        json_str = re.sub(r"```json|```|<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        try:
            decision = json.loads(json_str)
            logger.success(f"⚖️ Manager Decision for {ticker}: {decision.get('Order')} ({decision.get('Conviction')})")
            return decision
        except json.JSONDecodeError:
            if settings.BRAIN_JSON_RETRY:
                # Attempt 2: retry with minimal prompt
                logger.warning(f"⚠️ Manager JSON parse failed for {ticker}. Retrying with simplified prompt.")
                retry_prompt = f'Output ONLY valid JSON for {ticker}: {{"Order": "BUY" or "HOLD" or "SELL", "Conviction": 0.0 to 1.0, "Reasoning": "brief"}}'
                retry_response = self._query_model(retry_prompt)
                retry_str = re.sub(r"```json|```|<think>.*?</think>", "", retry_response, flags=re.DOTALL).strip()
                try:
                    decision = json.loads(retry_str)
                    logger.success(f"⚖️ Manager Decision (retry) for {ticker}: {decision.get('Order')}")
                    return decision
                except json.JSONDecodeError:
                    logger.error(f"❌ Manager hallucinated non-JSON output for {ticker} after retry. Defaulting to HOLD.")
                    return {"Order": "HOLD", "Conviction": 0.0, "Reasoning": "JSON parsing failure after retry."}
            logger.error(f"❌ Manager hallucinated non-JSON output for {ticker}. Defaulting to HOLD.")
            return {"Order": "HOLD", "Conviction": 0.0, "Reasoning": "JSON parsing failure."}

    def generate_market_summary(self, recent_logs: list) -> str:
        """STAGE 3: The 14b Manager synthesizes all recent actions into a transactional summary."""
        logger.info("📝 Manager (14b) synthesizing transactional market summary...")
        
        if not recent_logs:
            return "### ⏸️ Cycle Summary: No Actions Taken\nNo significant market movements or intelligence gathered during this period."
            
        logs_str = "\n".join([f"- {log['ticker']} ({log['type']}): {log['reason']} (Score: {log['score']})" for log in recent_logs])
        
        prompt = f"""You are the Lead Portfolio Manager. Summarize the LAST 30 MINUTES of trading activity. 

        Input Data:
        {logs_str}

        Required Format:
        ### 🚀 Last Cycle Summary
        - **Total Actions:** [Count of BUY/SELL vs total scans]
        - **Executed Trades:** [e.g., +NVDA (3 shares), -SAP (Partial 30%)] or [None]
        
        ### 🎯 Top Alpha Candidates
        - **[Ticker]:** [1-sentence reason why it's the strongest pick right now]
        
        ### 📉 Market Sentiment & Logic
        - [A brief 2-sentence explanation of why we didn't buy more or why we avoided specific sectors based on the news provided].

        Keep it punchy, technical, and data-driven. Do not use conversational filler.
        """

        response = self._query_model(prompt)
        clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        return clean_response
