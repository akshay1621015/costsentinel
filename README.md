# 🔍 CostSentinel — Enterprise Cost Intelligence Agent

> ET AI Hackathon 2026 | Track 3: AI for Enterprise Cost Intelligence & Autonomous Action

## 🎯 Problem Statement
Enterprise cost leakage costs Indian companies crores annually. At L&T Construction, procurement anomalies were caught manually — weeks late. CostSentinel closes that loop autonomously in minutes.

## 🚀 What It Does
CostSentinel is a **4-agent AI system** that:
- 🔍 **Detects** cost anomalies, duplicate vendors, SLA risks & construction overruns
- 🧠 **Diagnoses** root causes using LLM reasoning with cited evidence
- ⚡ **Acts** with specific, prioritized action plans
- 📋 **Logs** every decision with full audit trail

## 🏗️ Architecture
4 Specialized Agents orchestrated via LangGraph:
1. **Ingestion Agent** — Loads & normalizes data
2. **Anomaly Agent** — Detects problems (rapidfuzz, EVM, % change)
3. **Diagnosis Agent** — LLM root cause analysis (Llama 3.3-70B)
4. **Action Agent** — Generates action plan (Llama 3.1-8B)

## ✨ Unique Features
- 🌐 **Live Vendor Rate Search** — Tavily web search for real market rates
- 🤝 **Auto Negotiation Email** — Drafts emails for overpriced vendors
- 📊 **Resource Heatmap** — Visual team utilization analysis
- 🔮 **Predictive Overrun Alerts** — 30-day forward breach prediction
- 💬 **Chat with Data** — Ask questions about your project
- 🏗️ **Construction JCR** — L&T-style Job Cost Report with EVM & S-Curve

## 📊 4 Scenarios Covered
| Scenario | What Agent Finds | Savings |
|---|---|---|
| 🏢 Duplicate Vendors | 20 duplicate vendor pairs | ₹6,00,000 |
| ☁️ Cloud Spend Anomaly | Auto-scaling misconfiguration | ₹10,50,000 |
| ⚠️ SLA Breach Prevention | 9 tasks at risk, 43.8% shortfall | ₹5,00,000 |
| 🏗️ Construction Overrun | EVM-based 30-day prediction | ₹22,00,000 |

**Total Identifiable Savings: ₹43,50,000**

## 🛠️ Tech Stack
- **Orchestration:** LangGraph
- **LLM (Reasoning):** Llama 3.3-70B via Groq
- **LLM (Structured):** Llama 3.1-8B via Groq (cost efficiency)
- **Web Search:** Tavily API
- **Frontend:** Streamlit
- **Backend:** FastAPI
- **Data:** Pandas + SQLite
- **Charts:** Plotly

## ⚙️ Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/costsentinel.git
cd costsentinel
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add API keys
Create a `.env` file:
```
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
```

### 5. Generate datasets
```bash
python data/generate_data.py
python data/generate_construction_data.py
```

### 6. Run the app
```bash
streamlit run app.py
```

## 📁 Project Structure
```
costsentinel/
├── agents/
│   ├── ingestion.py      # Agent 1: Data loading
│   ├── anomaly.py        # Agent 2: Anomaly detection
│   ├── diagnosis.py      # Agent 3: Root cause analysis
│   ├── action.py         # Agent 4: Action planning
│   ├── construction.py   # Construction EVM agent
│   ├── advanced.py       # Vendor intel + resources
│   └── chat_agent.py     # Chat with data
├── data/
│   ├── generate_data.py
│   └── generate_construction_data.py
├── graph.py              # LangGraph orchestration
├── app.py                # Streamlit UI
├── .env                  # API keys (not committed)
└── README.md
```

## 💰 Impact Model
- **Duplicate Vendor Detection:** ₹6,00,000/month savings
- **Cloud Anomaly Fix:** ₹10,50,000 one-time recovery
- **SLA Breach Prevention:** ₹5,00,000 penalty avoided
- **Construction Overrun:** ₹22,00,000 predicted savings
- **Total:** ₹43,50,000 across demo scenarios

At enterprise scale (500+ vendors, 10+ projects):
Estimated **₹2-5 Cr annual savings** per large construction company

## 👤 Built By
Akshay Tyagi | MBA (Business Analytics) | IIM Sambalpur
Abhay Singh Jamwal | MBA (Business Analytics) | IIM Sambalpur
Parth Kodape | MBA (Business Analytics) | IIM Sambalpur