from langgraph.graph import StateGraph, START, END
import os

from src.agents.state import CreditCardAgentState

from src.agents.nodes import (
    router_node,
    knowledge_node,
    rdbms_node,
    generate_answer_node,
    greeting_node,
    hybrid_node,
)


def initial_route(
    state: CreditCardAgentState,
):
    question = state["question"].strip().lower()

    greetings = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    ]

    if any(question.startswith(greeting) for greeting in greetings):
        return "greeting"

    return "router"


def route_decision(
    state: CreditCardAgentState,
):
    """
    Decide next node based on router output.
    """

    return state["route"]


def build_credit_card_graph():

    workflow = StateGraph(CreditCardAgentState)

    # -----------------------------
    # Register Nodes
    # -----------------------------
    workflow.add_node(
        "greeting",
        greeting_node,
    )
    workflow.add_node(
        "router",
        router_node,
    )

    workflow.add_node(
        "knowledge",
        knowledge_node,
    )

    workflow.add_node(
        "rdbms",
        rdbms_node,
    )
    workflow.add_node(
        "hybrid",
        hybrid_node,
    )

    workflow.add_node(
        "generate_answer",
        generate_answer_node,
    )

    # -----------------------------
    # Define Workflow
    # -----------------------------

    # workflow.add_edge(
    #     START,
    #     "router",
    # )

    workflow.add_conditional_edges(
        START,
        initial_route,
        {
            "greeting": "greeting",
            "router": "router",
        },
    )

    # Router decides path
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "knowledge_base": "knowledge",
            "rdbms": "rdbms",
            "hybrid": "hybrid",
        },
    )

    # Both retrieval paths
    # go to answer generation

    workflow.add_edge(
        "knowledge",
        "generate_answer",
    )

    workflow.add_edge(
        "rdbms",
        "generate_answer",
    )
    workflow.add_edge(
        "hybrid",
        "generate_answer",
    )

    # Final node
    workflow.add_edge(
        "generate_answer",
        END,
    )

    workflow.add_edge(
        "greeting",
        END,
    )

    return workflow.compile()


# Compiled LangGraph application
credit_card_graph = build_credit_card_graph()


os.makedirs("graph_visuals", exist_ok=True)

graph_image = credit_card_graph.get_graph().draw_mermaid_png()

with open("graph_visuals/credit_card_graph.png", "wb") as f:
    f.write(graph_image)
