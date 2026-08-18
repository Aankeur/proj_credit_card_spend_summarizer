from langgraph.graph import StateGraph, START, END

from src.agents.state import CreditCardAgentState

from src.agents.nodes import (
    router_node,
    knowledge_node,
    rdbms_node,
    generate_answer_node,
)


def route_decision(
    state: CreditCardAgentState,
):
    """
    Decide next node based on router output.
    """

    return state["route"]



def build_credit_card_graph():

    workflow = StateGraph(
        CreditCardAgentState
    )

    # -----------------------------
    # Register Nodes
    # -----------------------------

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
        "generate_answer",
        generate_answer_node,
    )


    # -----------------------------
    # Define Workflow
    # -----------------------------

    workflow.add_edge(
        START,
        "router",
    )


    # Router decides path
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "knowledge_base": "knowledge",
            "rdbms": "rdbms",
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


    # Final node
    workflow.add_edge(
        "generate_answer",
        END,
    )


    return workflow.compile()



# Compiled LangGraph application
credit_card_graph = build_credit_card_graph()