import os
import json
from groq import Groq
from dotenv import load_dotenv
from agents.ingestion import log_audit

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def action_agent(state):
    scenario  = state["scenario"]
    diagnosis = state["diagnosis"]
    anomalies = state["anomalies"]

    prompt = f"""You are an enterprise cost analyst. Generate a specific action plan.
Scenario: {scenario}
Diagnosis: {json.dumps(diagnosis, indent=2)}
Anomalies: {json.dumps(anomalies[:3], indent=2)}

Return ONLY a JSON object in this exact format, no other text:
{{
  "actions": [
    {{
      "priority": 1,
      "action": "specific action to take",
      "owner": "who should do it",
      "estimated_saving_inr": 100000,
      "timeline_days": 7,
      "requires_approval": true
    }}
  ],
  "total_estimated_saving_inr": 500000,
  "payback_period_days": 30
}}
Include 3 to 5 actions. Be specific with rupee amounts."""

    print("⚡ Action Agent: Generating action plan...")

    # Small model for structured output (cost efficiency!)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    # Clean up if model adds extra text
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            if "{" in part:
                raw = part
                break
    if raw.startswith("json"):
        raw = raw[4:]

    # Find the JSON object
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    raw   = raw[start:end]

    plan = json.loads(raw)

    log_audit(
        "ActionAgent",
        f"Action plan generated with {len(plan['actions'])} actions",
        f"Total estimated saving: Rs {plan['total_estimated_saving_inr']:,}"
    )

    print(f"✅ Action Agent: Plan ready! Estimated saving: Rs {plan['total_estimated_saving_inr']:,}")

    return {**state, "action_plan": plan, "awaiting_approval": True}