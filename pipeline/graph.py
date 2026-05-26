from langgraph.graph import StateGraph, END

from pipeline.state import AIAState
from pipeline.nodes import (
    parse_node,
    workflow_entity_node,
    entity_role_node,
    event_verify_node,
    sim_node,
    impact_node,
)


def build_graph() -> StateGraph:
    graph = StateGraph(AIAState)

    graph.add_node("parse",           parse_node)
    graph.add_node("workflow_entity", workflow_entity_node)
    graph.add_node("entity_role",     entity_role_node)
    graph.add_node("event_verify",    event_verify_node)
    graph.add_node("sim",             sim_node)
    graph.add_node("impact",          impact_node)

    graph.set_entry_point("parse")
    graph.add_edge("parse",           "workflow_entity")
    graph.add_edge("workflow_entity", "entity_role")
    graph.add_edge("entity_role",     "event_verify")
    graph.add_edge("event_verify",    "sim")
    graph.add_edge("sim",             "impact")
    graph.add_edge("impact",          END)

    return graph


def compile_graph():
    return build_graph().compile()
