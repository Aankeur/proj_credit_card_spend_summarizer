from typing import TypedDict, List, Any


class CreditCardAgentState(TypedDict):
    """
    State passed between LangGraph nodes.

    Each node reads required information from this state
    and returns updates for the next node.
    """

    # Original user query
    question: str

    # Routing decision:
    # knowledge_base or rdbms
    route: str

    # Documents returned from vector/FTS/hybrid retrieval
    retrieved_documents: List[Any]

    # Customer-specific database result
    sql_result: str

    # Final generated answer
    answer: str

    # Knowledge base citations
    citations: List[Any]

    # Retry counter for future query rewrite flow
    retry_count: int