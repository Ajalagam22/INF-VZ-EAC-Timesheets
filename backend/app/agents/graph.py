from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.agents.state import EACAgentState
from app.agents.nodes.harvesting import harvesting_node
from app.agents.nodes.context import context_node
from app.agents.nodes.retrieval import retrieval_node
from app.agents.nodes.policy import policy_node
from app.agents.nodes.classification import classification_node
from app.agents.nodes.routing import routing_node
from app.agents.nodes.reconciliation import reconciliation_node


def _build_graph() -> StateGraph:
    builder = StateGraph(EACAgentState)

    builder.add_node("harvesting", harvesting_node)
    builder.add_node("context", context_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("policy", policy_node)
    builder.add_node("classification", classification_node)
    builder.add_node("routing", routing_node)
    builder.add_node("reconciliation", reconciliation_node)

    builder.set_entry_point("harvesting")
    builder.add_edge("harvesting", "context")
    builder.add_edge("context", "retrieval")
    builder.add_edge("retrieval", "policy")
    builder.add_edge("policy", "classification")
    builder.add_edge("classification", "routing")
    builder.add_edge("routing", "reconciliation")
    builder.add_edge("reconciliation", END)

    return builder.compile()


# Module-level compiled graph — reused across all requests
eac_graph = _build_graph()
