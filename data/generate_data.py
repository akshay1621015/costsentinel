import pandas as pd
import random

random.seed(42)

# --- DATASET 1: Vendors ---
legit = [
    ("Infosys Ltd", "IT Services"),
    ("Tata Consultancy", "IT Services"),
    ("Wipro Technologies", "Cloud Infra"),
    ("HCL Tech", "Cloud Infra"),
    ("Deloitte India", "Consulting"),
    ("KPMG Advisory", "Consulting"),
    ("Accenture Pvt Ltd", "Consulting"),
    ("Capgemini", "IT Services"),
]
dupes = [
    ("Infosys Limited", "IT Services"),
    ("TCS India", "IT Services"),
    ("Wipro Tech Pvt", "Cloud Infra"),
    ("HCL Technologies Ltd", "Cloud Infra"),
    ("Deloitte Consulting", "Consulting"),
    ("KPMG India", "Consulting"),
    ("Accenture India", "Consulting"),
    ("Cap Gemini India", "IT Services"),
]

vendors = []
for i in range(420):
    v = random.choice(legit)
    vendors.append({
        "vendor_id": f"V{1000+i}",
        "vendor_name": v[0],
        "service_category": v[1],
        "monthly_spend_inr": random.randint(50000, 500000),
        "contract_start": "2023-01-01"
    })
for i, d in enumerate(dupes * 10):
    vendors.append({
        "vendor_id": f"D{2000+i}",
        "vendor_name": d[0],
        "service_category": d[1],
        "monthly_spend_inr": random.randint(50000, 500000),
        "contract_start": "2023-06-01"
    })
pd.DataFrame(vendors).to_csv("data/vendors.csv", index=False)
print("vendors.csv created!")

# --- DATASET 2: Cloud Costs ---
months = ["2024-08","2024-09","2024-10","2024-11","2024-12",
          "2025-01","2025-02","2025-03"]
costs  = [820000,  835000,  841000,  829000,  855000,
          848000,  861000,  1206000]
services = ["EC2","S3","RDS","Lambda","Auto-Scaling"]
rows = []
for m, c in zip(months, costs):
    for s in services:
        spike = (s == "Auto-Scaling" and m == "2025-03")
        rows.append({
            "month": m,
            "service": s,
            "cost_inr": int(c / 5 * (2.0 if spike else 1))
        })
pd.DataFrame(rows).to_csv("data/cloud_costs.csv", index=False)
print("cloud_costs.csv created!")

# --- DATASET 3: SLA Tracker ---
completions = [90,85,40,30,20,70,60,10,95,80,
               50,45,15,88,72,33,66,5,92,78]
tasks = []
for i, pct in enumerate(completions):
    tasks.append({
        "task_id": f"T{i+1}",
        "task_name": f"Delivery Task {i+1}",
        "required_by": "2025-04-01",
        "completion_pct": pct,
        "assignee": f"Team {chr(65 + i % 4)}",
        "priority": "High" if i < 5 else "Medium"
    })
pd.DataFrame(tasks).to_csv("data/sla_tracker.csv", index=False)
print("sla_tracker.csv created!")

print("\nAll 3 datasets created successfully!")