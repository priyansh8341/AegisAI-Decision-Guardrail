import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

def _safe_json_extract(text: str):
    """
    Try to extract JSON object from a mixed LLM response.
    """
    # If it's already JSON
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except:
            pass

    # Try to find the first {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        chunk = m.group(0)
        try:
            return json.loads(chunk)
        except:
            pass

    return None

def assess_decision(decision_text: str) -> dict:
    prompt = f"""
You are AegisAI, an enterprise Decision Guardrail Agent.

Goal:
Evaluate a proposed business/technical decision BEFORE execution and predict risks and mitigation.

Return ONLY valid JSON using this schema:
{{
  "overall_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "risk_score": 0-100,
  "confidence": 0-1,
  "decision_recommendation": "APPROVE|REVISE|BLOCK",
  "primary_risks": [{{"title": "...", "why": "...", "severity": "LOW|MEDIUM|HIGH|CRITICAL"}}],
  "second_order_effects": ["...", "..."],
  "guardrails": ["...", "..."],
  "monitoring_signals": ["...", "..."],
  "30_day_outlook": {{
    "best_case": "...",
    "base_case": "...",
    "worst_case": "..."
  }},
  "executive_summary": "One short paragraph for leadership."
}}

Decision proposal:
\"\"\"{decision_text}\"\"\"
""".strip()

    r = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=180
    )
    r.raise_for_status()
    raw = r.json().get("response", "").strip()

    data = _safe_json_extract(raw)
    if data is None:
        # Fallback if model outputs something messy
        return {
            "overall_risk_level": "MEDIUM",
            "risk_score": 55,
            "confidence": 0.55,
            "decision_recommendation": "REVISE",
            "primary_risks": [{"title": "Unstructured output", "why": "Model returned non-JSON response.", "severity": "MEDIUM"}],
            "second_order_effects": [],
            "guardrails": ["Force JSON-only responses; tighten prompt; add validation."],
            "monitoring_signals": [],
            "30_day_outlook": {"best_case": "", "base_case": "", "worst_case": ""},
            "executive_summary": raw[:700]
        }

    return data
