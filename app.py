import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from graph import build_graph
from agents.advanced import (
    advanced_vendor_agent,
    generate_resource_heatmap,
    predict_overrun_30days,
    chat_with_project
)
from agents.chat_agent import chat_with_data

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CostSentinel",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── MCKINSEY STYLE CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main font */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* Top header bar */
    .main-header {
        background: linear-gradient(135deg, #003366 0%, #0066CC 100%);
        padding: 24px 32px;
        border-radius: 8px;
        margin-bottom: 24px;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.75) !important;
        font-size: 13px !important;
        margin: 4px 0 0 0 !important;
    }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #111827;
        line-height: 1.2;
    }
    .kpi-delta-bad  { color: #DC2626; font-size: 12px; font-weight: 600; }
    .kpi-delta-good { color: #16A34A; font-size: 12px; font-weight: 600; }

    /* Status badges */
    .badge-critical { background:#FEE2E2; color:#991B1B; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-warning  { background:#FEF3C7; color:#92400E; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-good     { background:#D1FAE5; color:#065F46; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }

    /* Section headers */
    .section-header {
        font-size: 16px;
        font-weight: 700;
        color: #111827;
        border-left: 4px solid #0066CC;
        padding-left: 12px;
        margin: 24px 0 16px 0;
    }

    /* Sidebar */
    .css-1d391kg { background: #F8FAFC; }

    /* Chat bubbles */
    .chat-user {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 12px 12px 4px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1E3A5F;
        font-size: 14px;
    }
    .chat-ai {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 12px 12px 12px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #14532D;
        font-size: 14px;
    }

    /* Email card */
    .email-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        font-family: monospace;
        font-size: 13px;
        white-space: pre-wrap;
        color: #1E293B;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Run button */
    .stButton > button {
        background: linear-gradient(135deg, #003366, #0066CC);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.3px;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #002244, #0055AA);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,102,204,0.3);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 13px;
        color: #6B7280;
    }
    .stTabs [aria-selected="true"] {
        color: #003366 !important;
        border-bottom: 2px solid #003366 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔍 CostSentinel</h1>
    <p>Enterprise Cost Intelligence Agent &nbsp;|&nbsp; ET AI Hackathon 2026 &nbsp;|&nbsp; Track 3 &nbsp;|&nbsp; Powered by LangGraph + Groq</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.markdown("---")
    scenario = st.selectbox(
        "Select Scenario",
        ["vendor", "cloud", "sla", "construction"],
        format_func=lambda x: {
            "vendor":       "🏢 Duplicate Vendor Detection",
            "cloud":        "☁️ Cloud Spend Anomaly",
            "sla":          "⚠️ SLA Breach Prevention",
            "construction": "🏗️ Construction Overrun Predictor"
        }[x]
    )
    st.markdown("---")
    run_clicked = st.button("▶ Run CostSentinel Agent")
    st.markdown("---")
    st.markdown("### 📊 About")
    st.markdown("""
    **CostSentinel** uses 4 specialized AI agents:
    - 📥 Ingestion Agent
    - 🔎 Anomaly Detector
    - 🧠 Diagnosis Agent
    - ⚡ Action Agent

    **Extra Features:**
    - 🌐 Live Vendor Rate Search
    - 🤝 Auto Negotiation Email
    - 📊 Resource Heatmap
    - 🔮 Predictive Overrun
    - 💬 Chat with Data
    """)
    st.markdown("---")
    st.caption("Built with LangGraph + Groq + Streamlit")

# ── RUN AGENT ─────────────────────────────────────────────────────────────────
if run_clicked:
    with st.spinner("🤖 Agents are working... please wait!"):
        graph  = build_graph()
        result = graph.invoke({
            "scenario":              scenario,
            "raw_data":              {},
            "anomalies":             [],
            "diagnosis":             [],
            "action_plan":           {},
            "awaiting_approval":     False,
            "construction_summary":  {},
            "construction_analysis": {},
            "jcr_df":                [],
            "scurve_df":             []
        })
    st.session_state["result"]   = result
    st.session_state["scenario"] = scenario
    if "chat_history" in st.session_state:
        del st.session_state["chat_history"]
    for key in list(st.session_state.keys()):
        if key.startswith(("approved_","rejected_","escalated_")):
            del st.session_state[key]

# ── RESULTS ───────────────────────────────────────────────────────────────────
if "result" in st.session_state:
    result   = st.session_state["result"]
    scenario = st.session_state["scenario"]

    st.success("✅ All agents completed successfully!")

    # ════════════════════════════════════════════════════════════════════════════
    # CONSTRUCTION SCENARIO
    # ════════════════════════════════════════════════════════════════════════════
    if scenario == "construction":
        summary  = result.get("construction_summary",  {})
        analysis = result.get("construction_analysis", {})
        boq_df   = pd.DataFrame(result["anomalies"])
        jcr_df   = pd.DataFrame(result["jcr_df"])
        scurve_df= pd.DataFrame(result["scurve_df"])

        # Project header
        st.markdown(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px;margin:16px 0;">
            <b>📋 {summary.get('project_name','')}</b><br>
            <span style="color:#6B7280;font-size:13px;">
            Client: {summary.get('client','')} &nbsp;|&nbsp;
            Job Code: {summary.get('job_code','')} &nbsp;|&nbsp;
            Report Month: {summary.get('report_month','')} &nbsp;|&nbsp;
            Expected Completion: {summary.get('expected_completion','')}
            </span>
        </div>
        """, unsafe_allow_html=True)

        # KPI Row
        health       = analysis.get("project_health","—")
        health_color = {"Critical":"#DC2626","At Risk":"#D97706","Healthy":"#16A34A"}.get(health,"#6B7280")
        health_badge = {"Critical":"badge-critical","At Risk":"badge-warning","Healthy":"badge-good"}.get(health,"badge-good")

        k1,k2,k3,k4,k5,k6 = st.columns(6)
        k1.markdown(f'<div class="kpi-card"><div class="kpi-label">Project Health</div><div class="kpi-value" style="color:{health_color};font-size:18px;">{health}</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><div class="kpi-label">Approved Budget</div><div class="kpi-value">₹{summary.get("total_budget_inr",0)/10000000:.1f} Cr</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><div class="kpi-label">Cost to Date</div><div class="kpi-value">₹{summary.get("cost_to_date_inr",0)/10000000:.1f} Cr</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-card"><div class="kpi-label">Predicted Overrun</div><div class="kpi-value" style="color:#DC2626;">₹{summary.get("predicted_overrun_inr",0)/10000000:.1f} Cr</div><div class="kpi-delta-bad">▲ {summary.get("predicted_overrun_pct",0)}%</div></div>', unsafe_allow_html=True)
        k5.markdown(f'<div class="kpi-card"><div class="kpi-label">CPI</div><div class="kpi-value" style="color:{"#16A34A" if summary.get("project_CPI",0)>=1 else "#DC2626"};">{summary.get("project_CPI","—")}</div></div>', unsafe_allow_html=True)
        k6.markdown(f'<div class="kpi-card"><div class="kpi-label">SPI</div><div class="kpi-value" style="color:{"#16A34A" if summary.get("project_SPI",0)>=1 else "#DC2626"};">{summary.get("project_SPI","—")}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs([
            "📊 JCR Summary",
            "📈 S-Curve",
            "🔍 BOQ EVM",
            "🔴 Critical Items",
            "🌐 Vendor Intel",
            "📊 Resource Heatmap",
            "🔮 Predictive Alerts",
            "💬 Chat with Data"
        ])

        # TAB 1: JCR
        with tab1:
            st.markdown('<div class="section-header">Job Cost Report — Item Wise Summary</div>', unsafe_allow_html=True)
            if not jcr_df.empty:
                display = jcr_df.copy()
                for col in ["approved_ace","oerq","cost_to_date","etc","revised_estimate","variance"]:
                    if col in display.columns:
                        display[col] = display[col].apply(lambda x: f"₹{x/10000000:.2f} Cr" if x!=0 else "—")
                st.dataframe(display, use_container_width=True, height=400)

                cat_summary = jcr_df.groupby("category")[["approved_ace","cost_to_date","revised_estimate"]].sum().reset_index()
                fig = px.bar(cat_summary, x="category",
                             y=["approved_ace","cost_to_date","revised_estimate"],
                             barmode="group",
                             color_discrete_sequence=["#003366","#0066CC","#DC2626"],
                             title="Budget vs Cost to Date vs Revised Estimate by Category")
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                  font=dict(family="Helvetica Neue"),
                                  legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig, use_container_width=True)

        # TAB 2: S-Curve
        with tab2:
            st.markdown('<div class="section-header">S-Curve: Planned vs Actual Cumulative Expenditure</div>', unsafe_allow_html=True)
            if not scurve_df.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=scurve_df["month"], y=scurve_df["cumulative_planned"],
                    mode="lines+markers", name="Planned",
                    line=dict(color="#003366", width=3),
                    marker=dict(size=6)
                ))
                fig2.add_trace(go.Scatter(
                    x=scurve_df["month"], y=scurve_df["cumulative_actual"],
                    mode="lines+markers", name="Actual",
                    line=dict(color="#DC2626", width=3, dash="dash"),
                    marker=dict(size=6)
                ))
                fig2.add_trace(go.Scatter(
                    x=scurve_df["month"],
                    y=scurve_df["cumulative_planned"],
                    fill="tonexty",
                    fillcolor="rgba(220,38,38,0.08)",
                    line=dict(width=0),
                    showlegend=False,
                    name="Variance"
                ))
                fig2.update_layout(
                    title="S-Curve Analysis",
                    xaxis_title="Month", yaxis_title="Cumulative Cost (₹)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    xaxis_tickangle=-45,
                    font=dict(family="Helvetica Neue"),
                    legend=dict(orientation="h", y=-0.25)
                )
                st.plotly_chart(fig2, use_container_width=True)

                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=scurve_df["month"], y=scurve_df["monthly_planned"],
                                      name="Planned", marker_color="#003366"))
                fig3.add_trace(go.Bar(x=scurve_df["month"], y=scurve_df["monthly_actual"],
                                      name="Actual", marker_color="#DC2626"))
                fig3.update_layout(barmode="group", title="Monthly Spend: Planned vs Actual",
                                   plot_bgcolor="white", paper_bgcolor="white",
                                   xaxis_tickangle=-45)
                st.plotly_chart(fig3, use_container_width=True)

        # TAB 3: BOQ EVM
        with tab3:
            st.markdown('<div class="section-header">BOQ Item-wise EVM Analysis</div>', unsafe_allow_html=True)
            if not boq_df.empty:
                display_boq = boq_df[["description","category","budgeted_cost",
                                       "planned_value","earned_value","actual_cost",
                                       "CPI","SPI","overrun_predicted_inr","overrun_pct","status"]].copy()
                for col in ["budgeted_cost","planned_value","earned_value","actual_cost","overrun_predicted_inr"]:
                    display_boq[col] = display_boq[col].apply(lambda x: f"₹{x/10000000:.2f} Cr")
                display_boq["overrun_pct"] = display_boq["overrun_pct"].apply(lambda x: f"{x}%")
                st.dataframe(display_boq, use_container_width=True, height=400)

                fig4 = go.Figure()
                fig4.add_trace(go.Bar(name="Planned Value", x=boq_df["description"],
                                      y=boq_df["planned_value"], marker_color="#003366"))
                fig4.add_trace(go.Bar(name="Earned Value",  x=boq_df["description"],
                                      y=boq_df["earned_value"],  marker_color="#16A34A"))
                fig4.add_trace(go.Bar(name="Actual Cost",   x=boq_df["description"],
                                      y=boq_df["actual_cost"],   marker_color="#DC2626"))
                fig4.update_layout(barmode="group", title="EVM Chart: PV vs EV vs AC",
                                   xaxis_tickangle=-45, plot_bgcolor="white",
                                   paper_bgcolor="white")
                st.plotly_chart(fig4, use_container_width=True)

                fig5 = px.scatter(boq_df, x="CPI", y="SPI",
                                  text="description", color="status",
                                  color_discrete_map={"🔴 CRITICAL":"red","🟡 WARNING":"orange","🟢 ON TRACK":"green"},
                                  title="CPI vs SPI Quadrant Analysis",
                                  size="budgeted_cost")
                fig5.add_hline(y=1.0, line_dash="dash", line_color="#6B7280", annotation_text="SPI=1.0")
                fig5.add_vline(x=1.0, line_dash="dash", line_color="#6B7280", annotation_text="CPI=1.0")
                fig5.update_traces(textposition="top center")
                fig5.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig5, use_container_width=True)

        # TAB 4: Critical Items + AI Forecast
        with tab4:
            critical = boq_df[boq_df["CPI"] < 0.85] if "CPI" in boq_df.columns else pd.DataFrame()
            warning  = boq_df[(boq_df["CPI"] >= 0.85) & (boq_df["CPI"] < 0.95)] if "CPI" in boq_df.columns else pd.DataFrame()

            if analysis:
                st.error(f"🔮 **AI Forecast:** {analysis.get('overrun_forecast','—')}")
                c1,c2 = st.columns(2)
                with c1:
                    st.write("**🔸 Top Risks:**")
                    for r in analysis.get("top_risks",[]): st.write(f"• {r}")
                with c2:
                    st.info(f"**30-Day Outlook:** {analysis.get('30_day_outlook','—')}")
                    st.success(f"**Savings Opportunity:** {analysis.get('savings_opportunity','—')}")

            st.markdown('<div class="section-header">🔴 Critical BOQ Items (CPI < 0.85)</div>', unsafe_allow_html=True)
            if not critical.empty:
                for _, row in critical.iterrows():
                    with st.expander(f"🔴 {row['description']} — CPI: {row['CPI']} | SPI: {row['SPI']}"):
                        cc1,cc2,cc3,cc4 = st.columns(4)
                        cc1.metric("Budget",            f"₹{row['budgeted_cost']/10000000:.2f} Cr")
                        cc2.metric("Actual Cost",        f"₹{row['actual_cost']/10000000:.2f} Cr")
                        cc3.metric("Predicted Overrun",  f"₹{row['overrun_predicted_inr']/10000000:.2f} Cr",
                                   delta=f"{row['overrun_pct']}%", delta_color="inverse")
                        cc4.metric("EAC",                f"₹{row['EAC']/10000000:.2f} Cr")

            st.markdown('<div class="section-header">🟡 Warning Items (0.85 ≤ CPI < 0.95)</div>', unsafe_allow_html=True)
            if not warning.empty:
                for _, row in warning.iterrows():
                    with st.expander(f"🟡 {row['description']} — CPI: {row['CPI']}"):
                        cc1,cc2,cc3 = st.columns(3)
                        cc1.metric("Budget",       f"₹{row['budgeted_cost']/10000000:.2f} Cr")
                        cc2.metric("Actual Cost",   f"₹{row['actual_cost']/10000000:.2f} Cr")
                        cc3.metric("Overrun",       f"₹{row['overrun_predicted_inr']/10000000:.2f} Cr",
                                   delta=f"{row['overrun_pct']}%", delta_color="inverse")

            # Action Plan
            st.markdown('<div class="section-header">💡 AI Recommended Actions</div>', unsafe_allow_html=True)
            if result["action_plan"]:
                plan = result["action_plan"]
                col1,col2 = st.columns(2)
                col1.metric("💰 Total Impact",    f"₹{plan['total_estimated_saving_inr']/10000000:.2f} Cr")
                col2.metric("⏱ Payback Period",   f"{plan['payback_period_days']} days")
                for a in plan["actions"]:
                    with st.expander(f"Priority {a['priority']}: {a['action'][:70]}..."):
                        cc1,cc2,cc3 = st.columns(3)
                        cc1.metric("Impact",   f"₹{a['estimated_saving_inr']/10000000:.2f} Cr")
                        cc2.metric("Owner",    a["owner"])
                        cc3.metric("Deadline", f"{a['timeline_days']} days")
                        if a["requires_approval"]:
                            st.warning("⚠️ Requires Approval!")
                            key = f"con_{a['priority']}"
                            if st.session_state.get(f"approved_{key}"):
                                st.success("✅ Approved!")
                            elif st.session_state.get(f"rejected_{key}"):
                                st.error("❌ Rejected!")
                            elif st.session_state.get(f"escalated_{key}"):
                                st.info("🔼 Escalated!")
                            else:
                                ca,cb,cc = st.columns(3)
                                if ca.button("✅ Approve",  key=f"app_{key}"):
                                    st.session_state[f"approved_{key}"] = True; st.rerun()
                                if cb.button("❌ Reject",   key=f"rej_{key}"):
                                    st.session_state[f"rejected_{key}"] = True; st.rerun()
                                if cc.button("🔼 Escalate", key=f"esc_{key}"):
                                    st.session_state[f"escalated_{key}"] = True; st.rerun()

        # TAB 5: VENDOR INTEL
        with tab5:
            st.markdown('<div class="section-header">🌐 Live Vendor Market Rate Intelligence</div>', unsafe_allow_html=True)
            st.info("🔍 Agent is searching real market rates from the web and comparing with current vendor spends...")

            if st.button("🌐 Run Vendor Intelligence Analysis", key="vendor_intel"):
                vendors_df = pd.read_csv("data/vendors.csv")
                with st.spinner("Searching live market rates..."):
                    vendor_results = advanced_vendor_agent(vendors_df)
                    st.session_state["vendor_results"] = vendor_results

            if "vendor_results" in st.session_state:
                vr = st.session_state["vendor_results"]
                for v in vr:
                    status_color = {"overpriced":"🔴","fair":"🟢","underpriced":"🟡"}.get(v["status"],"⚪")
                    with st.expander(f"{status_color} {v['vendor_name']} — {v['service_category']} | Overcharge: {v['overcharge_pct']}%"):
                        c1,c2,c3 = st.columns(3)
                        c1.metric("Current Spend",    f"₹{v['current_spend']:,}")
                        c2.metric("Market Rate Low",   f"₹{v['market_rate_low']:,}")
                        c3.metric("Market Rate High",  f"₹{v['market_rate_high']:,}")
                        st.write(f"**Recommendation:** {v['recommendation']}")

                        if v.get("negotiation_email"):
                            st.markdown("**📧 Auto-Drafted Negotiation Email:**")
                            email = v["negotiation_email"]
                            st.markdown(f"**Subject:** {email.get('subject','')}")
                            st.markdown(f'<div class="email-card">{email.get("body","")}</div>',
                                        unsafe_allow_html=True)
                            if st.button(f"📋 Copy Email", key=f"copy_{v['vendor_name']}"):
                                st.success("Email copied to clipboard!")

        # TAB 6: RESOURCE HEATMAP
        with tab6:
            st.markdown('<div class="section-header">📊 Resource Utilization Heatmap</div>', unsafe_allow_html=True)
            resource_df = generate_resource_heatmap()
            week_cols   = [c for c in resource_df.columns if c.startswith("Week")]

            fig6 = go.Figure(data=go.Heatmap(
                z=resource_df[week_cols].values,
                x=week_cols,
                y=resource_df["team"].tolist(),
                colorscale=[
                    [0.0,  "#D1FAE5"],
                    [0.6,  "#FEF3C7"],
                    [0.85, "#FED7AA"],
                    [1.0,  "#FEE2E2"]
                ],
                zmin=50, zmax=130,
                text=resource_df[week_cols].values,
                texttemplate="%{text}%",
                showscale=True,
                colorbar=dict(title="Utilization %",
                              tickvals=[50,70,85,100,115,130],
                              ticktext=["50%","70%","85%","100%","115%","130%"])
            ))
            fig6.update_layout(
                title="Team Resource Utilization by Week (%)",
                xaxis_title="Week",
                yaxis_title="Team",
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Helvetica Neue"),
                height=450
            )
            st.plotly_chart(fig6, use_container_width=True)

            st.markdown('<div class="section-header">Team Status Summary</div>', unsafe_allow_html=True)
            status_cols = st.columns(len(resource_df))
            for i, (_, row) in enumerate(resource_df.iterrows()):
                badge = "badge-critical" if "Overloaded" in row["status"] else \
                        "badge-warning"  if "High"       in row["status"] else \
                        "badge-good"
                status_cols[i].markdown(
                    f'<div style="text-align:center"><b style="font-size:11px">{row["team"]}</b><br>'
                    f'<span class="{badge}">{row["avg_utilization"]}%</span></div>',
                    unsafe_allow_html=True
                )

        # TAB 7: PREDICTIVE OVERRUN
        with tab7:
            st.markdown('<div class="section-header">🔮 30-Day Predictive Overrun Alerts</div>', unsafe_allow_html=True)
            if not boq_df.empty and "CPI" in boq_df.columns:
                predictions = predict_overrun_30days(boq_df)
                pred_df     = pd.DataFrame(predictions)

                # Summary metrics
                will_breach = pred_df[pred_df["will_breach_budget"]=="🔴 YES"]
                p1,p2,p3   = st.columns(3)
                p1.metric("🔴 Items Will Breach",   len(will_breach))
                p2.metric("🟢 Items On Track",       len(pred_df) - len(will_breach))
                p3.metric("💰 30-Day Projected Spend",
                          f"₹{pred_df['projected_30d_spend'].sum()/10000000:.1f} Cr")

                # Breach probability chart
                fig7 = px.bar(
                    pred_df.head(10),
                    x="description",
                    y="breach_probability_pct",
                    color="will_breach_budget",
                    color_discrete_map={"🔴 YES":"#DC2626","🟢 NO":"#16A34A"},
                    title="Breach Probability by BOQ Item (Next 30 Days)",
                    labels={"breach_probability_pct":"Breach Probability (%)","description":"BOQ Item"}
                )
                fig7.update_layout(xaxis_tickangle=-45,plot_bgcolor="white",paper_bgcolor="white")
                st.plotly_chart(fig7, use_container_width=True)

                st.markdown('<div class="section-header">Item-wise Predictions</div>', unsafe_allow_html=True)
                display_pred = pred_df[[
                    "description","current_CPI","current_SPI",
                    "will_breach_budget","breach_probability_pct",
                    "projected_30d_spend","risk_trend"
                ]].copy()
                display_pred["projected_30d_spend"] = display_pred["projected_30d_spend"].apply(
                    lambda x: f"₹{x/10000000:.2f} Cr"
                )
                st.dataframe(display_pred, use_container_width=True, height=400)

        # TAB 8: CHAT
        with tab8:
            st.markdown('<div class="section-header">💬 Chat with Your Project Data</div>', unsafe_allow_html=True)
            st.markdown("Ask anything about your project — CPI, riskiest vendor, overrun forecast, etc.")

            # Quick questions
            st.markdown("**Quick Questions:**")
            q1,q2,q3,q4 = st.columns(4)
            quick_q = None
            if q1.button("Which item has worst CPI?"):   quick_q = "Which BOQ item has the worst CPI?"
            if q2.button("What is overrun forecast?"):   quick_q = "What is the total overrun forecast?"
            if q3.button("Which category overruns?"):    quick_q = "Which category is overrunning the most?"
            if q4.button("Top 3 risks?"):                quick_q = "What are the top 3 project risks?"

            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = []

            if quick_q:
                context = f"""
Summary: {json.dumps(summary, indent=2)}
BOQ: {boq_df[['description','category','CPI','SPI','overrun_predicted_inr','status']].to_string()}
"""
                answer  = chat_with_data(quick_q, context)
                st.session_state["chat_history"].append(("user", quick_q))
                st.session_state["chat_history"].append(("ai",   answer))

            user_q = st.text_input("Or type your own question:", placeholder="e.g. Which vendor is riskiest?")
            if st.button("💬 Ask", key="chat_btn") and user_q:
                context = f"""
Summary: {json.dumps(summary, indent=2)}
BOQ: {boq_df[['description','category','CPI','SPI','overrun_predicted_inr','status']].to_string()}
"""
                answer  = chat_with_data(user_q, context)
                st.session_state["chat_history"].append(("user", user_q))
                st.session_state["chat_history"].append(("ai",   answer))

            # Display chat
            for role, msg in st.session_state.get("chat_history",[]):
                if role == "user":
                    st.markdown(f'<div class="chat-user">🧑 {msg}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-ai">🤖 {msg}</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════════
    # OTHER SCENARIOS
    # ════════════════════════════════════════════════════════════════════════════
    else:
        tab1,tab2,tab3,tab4 = st.tabs([
            "🚨 Anomalies","🧠 Diagnosis","💡 Action Plan","📋 Audit Log"
        ])

        with tab1:
            st.markdown('<div class="section-header">Anomalies Detected</div>', unsafe_allow_html=True)
            if result["anomalies"]:
                st.dataframe(pd.DataFrame(result["anomalies"]), use_container_width=True)
            else:
                st.info("No anomalies found!")

        with tab2:
            st.markdown('<div class="section-header">Root Cause Diagnosis</div>', unsafe_allow_html=True)
            if result["diagnosis"]:
                d = result["diagnosis"][0]
                col1,col2 = st.columns(2)
                col1.metric("Risk Level", d["risk_level"])
                col2.metric("Confidence", d["confidence"])
                st.info(d["root_cause"])
                for e in d["evidence"]: st.write(f"• {e}")

        with tab3:
            st.markdown('<div class="section-header">Recommended Action Plan</div>', unsafe_allow_html=True)
            if result["action_plan"]:
                plan = result["action_plan"]
                col1,col2 = st.columns(2)
                col1.metric("💰 Total Savings", f"₹{plan['total_estimated_saving_inr']:,}")
                col2.metric("⏱ Payback",        f"{plan['payback_period_days']} days")
                for a in plan["actions"]:
                    with st.expander(f"Priority {a['priority']}: {a['action'][:70]}..."):
                        c1,c2,c3 = st.columns(3)
                        c1.metric("Saving",   f"₹{a['estimated_saving_inr']:,}")
                        c2.metric("Owner",    a["owner"])
                        c3.metric("Timeline", f"{a['timeline_days']} days")
                        if a["requires_approval"]:
                            st.warning("⚠️ Requires Approval!")
                            key = f"{a['priority']}"
                            if st.session_state.get(f"approved_{key}"):
                                st.success("✅ Approved!")
                            elif st.session_state.get(f"rejected_{key}"):
                                st.error("❌ Rejected!")
                            elif st.session_state.get(f"escalated_{key}"):
                                st.info("🔼 Escalated!")
                            else:
                                ca,cb,cc = st.columns(3)
                                if ca.button("✅ Approve",  key=f"app_{key}"):
                                    st.session_state[f"approved_{key}"] = True; st.rerun()
                                if cb.button("❌ Reject",   key=f"rej_{key}"):
                                    st.session_state[f"rejected_{key}"] = True; st.rerun()
                                if cc.button("🔼 Escalate", key=f"esc_{key}"):
                                    st.session_state[f"escalated_{key}"] = True; st.rerun()

        with tab4:
            st.markdown('<div class="section-header">Agent Audit Log</div>', unsafe_allow_html=True)
            try:
                conn = sqlite3.connect("audit_log.db")
                logs = pd.read_sql("SELECT * FROM audit ORDER BY ts DESC LIMIT 50", conn)
                conn.close()
                st.dataframe(logs, use_container_width=True)
            except:
                st.info("No audit logs yet!")