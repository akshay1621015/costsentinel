import os
import json
from groq import Groq
from dotenv import load_dotenv
from agents.ingestion import log_audit

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def diagnosis_agent(state):
    scenario  = state["scenario"]
    anomalies = state["anomalies"]

    prompt = f"""You are an enterprise cost intelligence analyst.
Scenario type: {scenario}
Anomalies detected: {json.dumps(anomalies[:5], indent=2)}

Provide a root cause diagnosis. Be specific. Cite the data.
Return ONLY a JSON object in this exact format, no other text:
{{
  "root_cause": "explain what is wrong and why",
  "confidence": "High or Medium or Low",
  "evidence": ["evidence point 1", "evidence point 2", "evidence point 3"],
  "risk_level": "Critical or High or Medium"
}}"""

    print("🧠 Diagnosis Agent: Thinking...")

    # Big model for complex reasoning
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    # Clean up if model adds extra text
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    diagnosis = json.loads(raw)

    log_audit(
        "DiagnosisAgent",
        f"Root cause identified: {diagnosis['root_cause'][:80]}",
        f"Confidence: {diagnosis['confidence']} | Risk: {diagnosis['risk_level']}"
    )

    print(f"✅ Diagnosis Agent: {diagnosis['risk_level']} risk detected!")

    return {**state, "diagnosis": [diagnosis]}