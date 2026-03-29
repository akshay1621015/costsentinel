import os
import json
import pandas as pd
import numpy as np
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from agents.ingestion import log_audit

load_dotenv()
groq_client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── 1. LIVE VENDOR RATE SEARCH ───────────────────────────────────────────────
def search_vendor_market_rates(vendor_name, service_category, current_spend):
    try:
        query    = f"{service_category} vendor rates India 2024 market price benchmark"
        results  = tavily_client.search(query=query, search_depth="basic", max_results=3)
        snippets = " ".join([r.get("content","") for r in results.get("results",[])])

        prompt = f"""You are a procurement analyst.
Vendor: {vendor_name}
Category: {service_category}
Current monthly spend: Rs {current_spend:,}

Based on this market research:
{snippets[:1000]}

Return ONLY JSON:
{{
  "market_rate_low":  500000,
  "market_rate_high": 800000,
  "current_vs_market": "overpriced or fair or underpriced",
  "overcharge_pct": 15,
  "recommendation": "one specific action"
}}"""

        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}],
            temperature=0.1
        )
        raw = resp.choices[0].message.content.strip()
        if "```" in raw:
            parts = raw.split("```")
            for p in parts:
                if "{" in p:
                    raw = p
                    break
        if raw.startswith("json"):
            raw = raw[4:]
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        raw   = raw[start:end]
        return json.loads(raw)
    except Exception as e:
        return {
            "market_rate_low":   int(current_spend * 0.80),
            "market_rate_high":  int(current_spend * 0.95),
            "current_vs_market": "overpriced",
            "overcharge_pct":    12,
            "recommendation":    "Renegotiate contract based on market benchmarks"
        }

# ─── 2. AUTO NEGOTIATION EMAIL ────────────────────────────────────────────────
def draft_negotiation_email(vendor_name, service, current_spend, market_rate, overcharge_pct):
    prompt = f"""Write a professional vendor negotiation email.
Vendor: {vendor_name}
Service: {service}
Current spend: Rs {current_spend:,}/month
Market benchmark: Rs {market_rate:,}/month
Overcharge: {overcharge_pct}%

Write a firm but professional email requesting rate revision.
Return ONLY JSON:
{{
  "subject": "email subject",
  "body": "full email body with proper formatting"
}}"""

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2
    )
    raw = resp.choices[0].message.content.strip()
    if "```" in raw:
        parts = raw.split("```")
        for p in parts:
            if "{" in p:
                raw = p
                break
    if raw.startswith("json"):
        raw = raw[4:]
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    raw   = raw[start:end]
    return json.loads(raw)

# ─── 3. RESOURCE UTILIZATION HEATMAP ─────────────────────────────────────────
def generate_resource_heatmap():
    teams = ["Civil Team A","Civil Team B","Steel Team","MEP Team",
             "Electrical Team","Labor Team A","Labor Team B","Equipment Team"]
    weeks = ["Week 1","Week 2","Week 3","Week 4",
             "Week 5","Week 6","Week 7","Week 8"]

    np.random.seed(42)
    data = []
    for team in teams:
        row = {"team": team}
        for week in weeks:
            # Simulate realistic utilization
            base = np.random.randint(60, 110)
            row[week] = min(base, 130)
        data.append(row)

    df = pd.DataFrame(data)

    # Flag overloaded teams
    week_cols = [c for c in df.columns if c != "team"]
    df["avg_utilization"] = df[week_cols].mean(axis=1).round(1)
    df["status"] = df["avg_utilization"].apply(
        lambda x: "🔴 Overloaded" if x > 100 else
                  "🟡 High"       if x > 85  else
                  "🟢 Normal"
    )
    return df

# ─── 4. PREDICTIVE OVERRUN ALERT ─────────────────────────────────────────────
def predict_overrun_30days(boq_df):
    predictions = []
    for _, row in boq_df.iterrows():
        cpi = row.get("CPI", 1.0)
        spi = row.get("SPI", 1.0)

        # Burn rate projection
        remaining_budget = row["budgeted_cost"] - row["earned_value"]
        if cpi > 0:
            projected_cost_to_complete = remaining_budget / cpi
        else:
            projected_cost_to_complete = remaining_budget * 1.5

        # 30-day spend projection
        monthly_burn      = row["actual_cost"] * 0.15
        projected_30d     = monthly_burn * (1 + (1 - cpi))
        will_breach       = cpi < 0.90 or spi < 0.85
        breach_probability= min(100, int((1 - cpi) * 200)) if cpi < 1 else 0

        predictions.append({
            "description":           row["description"],
            "category":              row["category"],
            "current_CPI":           cpi,
            "current_SPI":           spi,
            "projected_30d_spend":   int(projected_30d),
            "will_breach_budget":    "🔴 YES" if will_breach else "🟢 NO",
            "breach_probability_pct": breach_probability,
            "projected_cost_to_complete": int(projected_cost_to_complete),
            "risk_trend":            "📈 Worsening" if cpi < 0.90 else
                                     "➡️ Stable"    if cpi < 0.98 else
                                     "📉 Improving"
        })

    return sorted(predictions, key=lambda x: -x["breach_probability_pct"])

# ─── 5. CHAT WITH PROJECT DATA ────────────────────────────────────────────────
def chat_with_project(question, boq_df, summary):
    context = f"""
Project Summary:
{json.dumps(summary, indent=2)}

BOQ Data (top items):
{boq_df[["description","category","CPI","SPI","overrun_predicted_inr","status"]].head(10).to_string()}
"""

    prompt = f"""You are a construction cost expert AI assistant.
Answer this question about the project data concisely and specifically.

PROJECT DATA:
{context}

QUESTION: {question}

Give a specific, data-backed answer in 2-3 sentences maximum.
Mention specific numbers, item names, or percentages from the data."""

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

# ─── MAIN ADVANCED AGENT ──────────────────────────────────────────────────────
def advanced_vendor_agent(vendors_df):
    results = []
    for _, vendor in vendors_df.head(5).iterrows():
        spend    = vendor.get("monthly_spend_inr", 200000)
        name     = vendor.get("vendor_name", "Unknown")
        category = vendor.get("service_category", "General")

        # Search market rates
        market   = search_vendor_market_rates(name, category, spend)

        # Draft email if overpriced
        email    = None
        if market.get("current_vs_market") == "overpriced":
            email = draft_negotiation_email(
                name, category, spend,
                market.get("market_rate_low", spend),
                market.get("overcharge_pct", 10)
            )

        results.append({
            "vendor_name":       name,
            "service_category":  category,
            "current_spend":     spend,
            "market_rate_low":   market.get("market_rate_low"),
            "market_rate_high":  market.get("market_rate_high"),
            "status":            market.get("current_vs_market"),
            "overcharge_pct":    market.get("overcharge_pct", 0),
            "recommendation":    market.get("recommendation"),
            "negotiation_email": email
        })

        log_audit(
            "AdvancedVendorAgent",
            f"Market rate check: {name}",
            f"Status: {market.get('current_vs_market')} | Overcharge: {market.get('overcharge_pct',0)}%"
        )

    return results