from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any
from agents.ingestion import ingestion_agent
from agents.anomaly import anomaly_agent
from agents.diagnosis import diagnosis_agent
from agents.action import action_agent
from agents.construction import construction_agent

class AgentState(TypedDict):
    scenario: str
    raw_data: Any
    anomalies: List[Any]
    diagnosis: List[Any]
    action_plan: Any
    awaiting_approval: bool
    construction_summary: Any
    construction_analysis: Any
    jcr_df: Any
    scurve_df: Any

def route_scenario(state):
    if state["scenario"] == "construction":
        return "construction"
    return "ingest"

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("ingest",       ingestion_agent)
    graph.add_node("detect",       anomaly_agent)
    graph.add_node("diagnose",     diagnosis_agent)
    graph.add_node("act",          action_agent)
    graph.add_node("construction", construction_agent)
    graph.set_conditional_entry_point(
        route_scenario,
        {"construction": "construction", "ingest": "ingest"}
    )
    graph.add_edge("ingest",       "detect")
    graph.add_edge("detect",       "diagnose")
    graph.add_edge("diagnose",     "act")
    graph.add_edge("act",          END)
    graph.add_edge("construction", END)
    return graph.compile()