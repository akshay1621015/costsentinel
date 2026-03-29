import pandas as pd
import sqlite3
from datetime import datetime

def log_audit(agent, action, detail=""):
    conn = sqlite3.connect("audit_log.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS audit
                    (ts TEXT, agent TEXT, action TEXT, detail TEXT)""")
    conn.execute("INSERT INTO audit VALUES (?,?,?,?)",
                 (datetime.now().isoformat(), agent, action, detail))
    conn.commit()
    conn.close()

def ingestion_agent(state):
    scenario = state["scenario"]
    
    paths = {
        "vendor": "data/vendors.csv",
        "cloud":  "data/cloud_costs.csv",
        "sla":    "data/sla_tracker.csv"
    }
    
    df = pd.read_csv(paths[scenario])
    
    log_audit(
        "IngestionAgent",
        f"Loaded data for scenario: {scenario}",
        f"{len(df)} rows loaded"
    )
    
    print(f"✅ Ingestion Agent: Loaded {len(df)} rows for '{scenario}' scenario")
    
    return {**state, "raw_data": df.to_dict("records")}