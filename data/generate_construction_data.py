import pandas as pd
import numpy as np
import random

random.seed(42)
np.random.seed(42)

# --- PROJECT METADATA ---
project = {
    "project_name":     "Underground Cable Laying & Substation Construction Works at Greenfield Township, Phase II",
    "client":           "Rajasthan Vidyut Vitran Nigam Ltd (RVVNL)",
    "cluster":          "Jaipur North",
    "job_code":         "LE23M847",
    "duration_months":  24,
    "commence_date":    "15-03-2022",
    "contractual_completion": "14-03-2024",
    "expected_completion":    "30-06-2024",
    "report_month":     "Mar'24"
}

# --- JCR STYLE BOQ ---
# Columns: head, category, approved_ace, oerq, cost_to_date, etc_, revised_estimate, variance
heads = [
    # (description, category, approved_ace, oerq_factor, cost_pct, etc_factor)
    ("Supply ex-works",                "Supply",   9911942850, 0.934, 0.915, 0.085),
    ("Freight & Insurance",            "Supply",    621721100, 0.000, 0.000, 1.000),
    ("PV and Hedging",                 "Supply",    373103560, 0.000, 1.000, 0.000),
    ("BOCW - Supply",                  "Supply",    124553490, 1.022, 0.978, 0.022),
    ("Erection Cost (Sub-Contractor)", "Services", 3268764860, 0.853, 0.638, 0.182),
    ("PF Cost (SC)",                   "Services",   57013700, 0.000, 0.000, 1.000),
    ("BOCW - Erection",                "Services",   38444490, 1.021, 0.957, 0.043),
    ("Overheads (BG, Insurance etc.)", "Overhead",  778550430, 0.866, 0.879, 0.173),
    ("Professional Fees",              "Overhead",   19874180, 0.000, 1.000, 0.000),
    ("DLP/Contingency Provision",      "Overhead",  138827930, 0.000, 1.000, 0.000),
    ("Additional Escalation - Supply", "Provisions",113792280, 1.000, 0.000, 1.000),
    ("Incidental Expenses",            "Provisions", 99887500, 0.000, 1.000, 0.000),
    ("Supply GST (18%)",               "Taxes",    1784149710, 0.934, 0.915, 0.085),
    ("Erection GST (18%)",             "Taxes",     588377670, 0.853, 0.638, 0.182),
]

rows = []
for desc, cat, ace, oerq_f, cost_f, etc_f in heads:
    oerq     = round(ace * oerq_f)           if oerq_f  > 0 else 0
    ctd      = round(ace * cost_f)           if cost_f  > 0 else 0
    etc      = round(ace * etc_f * oerq_f)  if etc_f   > 0 and oerq_f > 0 else round(ace * etc_f * 0.9)
    rev_est  = ctd + etc
    variance = ace - rev_est
    rows.append({
        "head_description":  desc,
        "category":          cat,
        "approved_ace":      ace,
        "oerq":              oerq,
        "cost_to_date":      ctd,
        "etc":               etc,
        "revised_estimate":  rev_est,
        "variance":          variance,
    })

jcr_df = pd.DataFrame(rows)
jcr_df.to_csv("data/jcr_data.csv", index=False)
print("jcr_data.csv created!")

# --- MONTHLY S-CURVE DATA ---
months = ["Apr-22","May-22","Jun-22","Jul-22","Aug-22","Sep-22",
          "Oct-22","Nov-22","Dec-22","Jan-23","Feb-23","Mar-23",
          "Apr-23","May-23","Jun-23","Jul-23","Aug-23","Sep-23",
          "Oct-23","Nov-23","Dec-23","Jan-24","Feb-24","Mar-24"]

total_budget = jcr_df["approved_ace"].sum()

# S-curve follows a typical construction bell curve
planned_weights = [
    0.01,0.02,0.03,0.04,0.05,0.06,
    0.07,0.07,0.07,0.06,0.06,0.06,
    0.05,0.05,0.05,0.05,0.04,0.04,
    0.04,0.03,0.03,0.02,0.02,0.01
]

actual_weights = [
    0.01,0.01,0.02,0.03,0.04,0.05,
    0.06,0.06,0.07,0.07,0.07,0.06,
    0.06,0.06,0.05,0.05,0.05,0.05,
    0.05,0.04,0.03,0.02,0.01,0.00
]

scurve_rows = []
cum_planned = 0
cum_actual  = 0
for i, month in enumerate(months):
    monthly_planned = round(total_budget * planned_weights[i])
    monthly_actual  = round(total_budget * actual_weights[i])
    cum_planned    += monthly_planned
    cum_actual     += monthly_actual
    scurve_rows.append({
        "month":              month,
        "monthly_planned":    monthly_planned,
        "monthly_actual":     monthly_actual,
        "cumulative_planned": cum_planned,
        "cumulative_actual":  cum_actual,
    })

pd.DataFrame(scurve_rows).to_csv("data/scurve_data.csv", index=False)
print("scurve_data.csv created!")

# --- ITEM WISE BOQ WITH EVM ---
boq_items = [
    ("Civil Works - Foundation",       "Civil",    1500000000, 85, 72),
    ("Civil Works - Superstructure",   "Civil",    2800000000, 78, 65),
    ("Steel Reinforcement",            "Steel",    2200000000, 82, 60),
    ("Structural Steel Fabrication",   "Steel",    1800000000, 70, 55),
    ("HT Cable Supply & Laying",       "Electrical",1200000000,90, 75),
    ("LT Cable Supply & Laying",       "Electrical", 800000000, 88, 80),
    ("Distribution Transformers",      "Electrical", 600000000, 95, 90),
    ("Substation Construction",        "Civil",     900000000, 60, 45),
    ("HVAC Systems",                   "MEP",      1000000000, 75, 60),
    ("Plumbing & Drainage",            "MEP",       800000000, 80, 70),
    ("Finishing Works",                "Finishing", 700000000, 65, 55),
    ("Landscaping",                    "Civil",     400000000, 50, 40),
    ("Labor - Skilled",                "Labor",    1600000000, 88, 70),
    ("Labor - Unskilled",              "Labor",     800000000, 92, 75),
    ("Equipment Hire",                 "Equipment",1100000000, 78, 65),
]

evm_rows = []
for desc, cat, budget, planned_pct, earned_pct in boq_items:
    overrun = 1.25 if cat in ["Steel","Labor"] else 1.10 if cat in ["MEP","Electrical"] else 1.05
    pv      = round(budget * planned_pct / 100)
    ev      = round(budget * earned_pct  / 100)
    ac      = round(ev * overrun)
    cpi     = round(ev / ac,   3)
    spi     = round(ev / pv,   3)
    eac     = round(budget / cpi)
    overrun_inr = eac - budget
    evm_rows.append({
        "description":         desc,
        "category":            cat,
        "budgeted_cost":       budget,
        "planned_value":       pv,
        "earned_value":        ev,
        "actual_cost":         ac,
        "CPI":                 cpi,
        "SPI":                 spi,
        "EAC":                 eac,
        "overrun_predicted_inr": overrun_inr,
        "overrun_pct":         round(overrun_inr / budget * 100, 1),
        "status": "🔴 CRITICAL" if cpi < 0.85 else "🟡 WARNING" if cpi < 0.95 else "🟢 ON TRACK"
    })

pd.DataFrame(evm_rows).to_csv("data/boq_evm.csv", index=False)
print("boq_evm.csv created!")

# Save project metadata
import json
with open("data/project_meta.json","w") as f:
    json.dump(project, f, indent=2)
print("project_meta.json created!")

print("\nAll construction datasets created successfully!")