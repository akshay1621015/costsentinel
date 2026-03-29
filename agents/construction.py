import pandas as pd
import numpy as np
import os
import json
from groq import Groq
from dotenv import load_dotenv
from agents.ingestion import log_audit

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def construction_agent(state):

    # Load all data
    jcr_df    = pd.read_csv("data/jcr_data.csv")
    scurve_df = pd.read_csv("data/scurve_data.csv")
    boq_df    = pd.read_csv("data/boq_evm.csv")

    with open("data/project_meta.json") as f:
        meta = json.load(f)

    # --- JCR Summary ---
    total_ace      = jcr_df["approved_ace"].sum()
    total_ctd      = jcr_df["cost_to_date"].sum()
    total_rev_est  = jcr_df["revised_estimate"].sum()
    total_variance = jcr_df["variance"].sum()

    # Sales (assumed at 15% margin)
    total_sales    = round(total_ace * 1.15)
    gross_margin   = total_sales - total_rev_est
    margin_pct     = round(gross_margin / total_sales * 100, 1)

    # --- EVM Project Level ---
    total_pv  = boq_df["planned_value"].sum()
    total_ev  = boq_df["earned_value"].sum()
    total_ac  = boq_df["actual_cost"].sum()
    total_eac = boq_df["EAC"].sum()

    project_cpi = round(total_ev / total_ac,  3)
    project_spi = round(total_ev / total_pv,  3)
    total_overrun = int(total_eac - boq_df["budgeted_cost"].sum())

    critical_items   = boq_df[boq_df["CPI"] < 0.85].to_dict("records")
    warning_items    = boq_df[(boq_df["CPI"] >= 0.85) & (boq_df["CPI"] < 0.95)].to_dict("records")

    # Latest S-curve month
    latest = scurve_df.iloc[-2]  # second last (last month complete)
    scurve_variance = int(latest["cumulative_actual"] - latest["cumulative_planned"])

    summary = {
        "project_name":          meta["project_name"],
        "client":                meta["client"],
        "job_code":              meta["job_code"],
        "report_month":          meta["report_month"],
        "contractual_completion":meta["contractual_completion"],
        "expected_completion":   meta["expected_completion"],
        "total_budget_inr":      int(total_ace),
        "cost_to_date_inr":      int(total_ctd),
        "revised_estimate_inr":  int(total_rev_est),
        "total_variance_inr":    int(total_variance),
        "gross_margin_inr":      int(gross_margin),
        "margin_pct":            margin_pct,
        "project_CPI":           project_cpi,
        "project_SPI":           project_spi,
        "predicted_overrun_inr": total_overrun,
        "predicted_overrun_pct": round(total_overrun / boq_df["budgeted_cost"].sum() * 100, 1),
        "critical_items_count":  len(critical_items),
        "warning_items_count":   len(warning_items),
        "scurve_variance_inr":   scurve_variance,
    }

    # --- LLM Analysis ---
    prompt = f"""You are a Senior Construction Cost Engineer with 15 years of experience in L&T style projects.
Analyze this Job Cost Report (JCR) and provide expert recommendations.

PROJECT: {meta['project_name']}
CLIENT:  {meta['client']}
REPORT MONTH: {meta['report_month']}

JCR SUMMARY:
{json.dumps(summary, indent=2)}

CRITICAL BOQ ITEMS (CPI < 0.85):
{json.dumps(critical_items[:4], indent=2)}

Return ONLY a JSON object in this exact format, no other text:
{{
  "project_health": "Critical or At Risk or Healthy",
  "overrun_forecast": "one sentence with exact rupee amount and percentage",
  "top_risks": ["risk 1", "risk 2", "risk 3"],
  "immediate_actions": [
    {{
      "priority": 1,
      "action": "very specific action",
      "owner": "who is responsible",
      "impact_inr": 5000000,
      "deadline_days": 7
    }}
  ],
  "30_day_outlook": "specific prediction",
  "savings_opportunity": "specific cost saving opportunity with rupee amount"
}}"""

    print("🏗️ Construction Agent: Analyzing JCR...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            if "{" in part:
                raw = part
                break
    if raw.startswith("json"):
        raw = raw[4:]
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    raw   = raw[start:end]

    analysis = json.loads(raw)

    log_audit(
        "ConstructionAgent",
        f"JCR Analysis complete. Health: {analysis['project_health']}",
        f"Predicted overrun: Rs {summary['predicted_overrun_inr']:,}"
    )

    print(f"✅ Construction Agent done! CPI: {project_cpi} | SPI: {project_spi}")

    return {
        **state,
        "anomalies":   boq_df.to_dict("records"),
        "diagnosis":   [{
            "root_cause": analysis["overrun_forecast"],
            "confidence": "High",
            "evidence":   analysis["top_risks"],
            "risk_level": analysis["project_health"]
        }],
        "action_plan": {
            "actions": [{
                "priority":             a["priority"],
                "action":               a["action"],
                "owner":                a["owner"],
                "estimated_saving_inr": a["impact_inr"],
                "timeline_days":        a["deadline_days"],
                "requires_approval":    True
            } for a in analysis["immediate_actions"]],
            "total_estimated_saving_inr": sum(
                a["impact_inr"] for a in analysis["immediate_actions"]
            ),
            "payback_period_days": 30
        },
        "construction_summary":  summary,
        "construction_analysis": analysis,
        "jcr_df":    jcr_df.to_dict("records"),
        "scurve_df": scurve_df.to_dict("records"),
        "awaiting_approval": True
    }