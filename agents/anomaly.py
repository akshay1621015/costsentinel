import pandas as pd
from rapidfuzz import fuzz
from agents.ingestion import log_audit

def anomaly_agent(state):
    scenario = state["scenario"]
    data = pd.DataFrame(state["raw_data"])
    anomalies = []

    if scenario == "vendor":
        anomalies = detect_duplicate_vendors(data)
    elif scenario == "cloud":
        anomalies = detect_cost_spike(data)
    elif scenario == "sla":
        anomalies = detect_sla_risk(data)

    log_audit(
        "AnomalyAgent",
        f"Anomaly detection complete for: {scenario}",
        f"{len(anomalies)} anomalies found"
    )

    print(f"✅ Anomaly Agent: Found {len(anomalies)} anomalies")

    return {**state, "anomalies": anomalies}


def detect_duplicate_vendors(df):
    dupes = []
    vendors = df.to_dict("records")
    for i, v1 in enumerate(vendors):
        for v2 in vendors[i+1:]:
            if (v1["service_category"] == v2["service_category"] and
                    fuzz.ratio(v1["vendor_name"], v2["vendor_name"]) > 70):
                dupes.append({
                    "type": "duplicate_vendor",
                    "vendor_1": v1["vendor_name"],
                    "id_1": v1["vendor_id"],
                    "vendor_2": v2["vendor_name"],
                    "id_2": v2["vendor_id"],
                    "service": v1["service_category"],
                    "combined_monthly_spend": v1["monthly_spend_inr"] + v2["monthly_spend_inr"],
                    "similarity_score": fuzz.ratio(v1["vendor_name"], v2["vendor_name"])
                })
    return sorted(dupes, key=lambda x: -x["combined_monthly_spend"])[:20]


def detect_cost_spike(df):
    monthly = df.groupby("month")["cost_inr"].sum().reset_index()
    monthly["pct_change"] = monthly["cost_inr"].pct_change() * 100
    spikes = monthly[monthly["pct_change"] > 20].to_dict("records")

    spike_causes = {
        "Auto-Scaling": "Misconfigured auto-scaling rule — immediate fix possible",
        "EC2":          "Provisioning error — requires infra review",
        "RDS":          "Seasonal traffic pattern — monitor only"
    }

    if spikes:
        last_month = spikes[-1]["month"]
        prev_month = monthly.iloc[-2]["month"]
        last = df[df["month"] == last_month]
        prev = df[df["month"] == prev_month]
        by_service = (
            last.groupby("service")["cost_inr"].sum() -
            prev.groupby("service")["cost_inr"].sum()
        ).reset_index()
        by_service.columns = ["service", "delta"]
        top_service = by_service.sort_values("delta", ascending=False).iloc[0]["service"]
        spikes[0]["service_breakdown"] = str(by_service[["service","delta"]].to_dict("records"))
        spikes[0]["likely_cause"]       = spike_causes.get(top_service, "Unknown")
        spikes[0]["recommended_response"] = (
            "AUTO-FIX"  if top_service == "Auto-Scaling" else
            "ESCALATE"  if top_service == "EC2"          else
            "MONITOR"
        )
    return spikes


def detect_sla_risk(df):
    at_risk = df[df["completion_pct"] < 60].to_dict("records")
    projected = round(df["completion_pct"].mean(), 1)
    critical = [t for t in at_risk if t["completion_pct"] < 30]
    critical_summary = ", ".join([
        f"{t['task_id']}({t['completion_pct']}%)" for t in critical
    ])
    return [{
        "type": "sla_risk",
        "tasks_at_risk": len(at_risk),
        "projected_completion_pct": projected,
        "shortfall": round(100 - projected, 1),
        "critical_tasks": critical_summary
    }]