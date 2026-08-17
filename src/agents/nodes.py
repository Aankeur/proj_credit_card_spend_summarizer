from src.agents.state import CreditCardAgentState
from src.agents.rag_agent import (
    llm,
    create_answer_prompt,
)

from src.tools.tools import (
    search_hybrid,
    search_rdbms,
)


def router_node(
    state: CreditCardAgentState,
):
    """
    Decide whether the query needs:
    - Knowledge base retrieval
    - Customer database retrieval
    """

    question = state["question"].lower()

    rdbms_keywords = [
        "spend",
        "spent",
        "transaction",
        "merchant",
        "billing",
        "statement",
        "reward",
        "category",
        "payment",
    ]

    if any(
        keyword in question
        for keyword in rdbms_keywords
    ):
        return {
            "route": "rdbms"
        }

    return {
        "route": "knowledge_base"
    }



def knowledge_node(
    state: CreditCardAgentState,
):
    """
    Retrieve card/product information
    using hybrid search.
    """

    documents = search_hybrid.invoke(
        {
            "query": state["question"]
        }
    )

    return {
        "retrieved_documents": documents
    }



def rdbms_node(
    state: CreditCardAgentState,
):
    """
    Retrieve customer-specific information
    from PostgreSQL.
    """

    result = search_rdbms.invoke(
        {
            "query": state["question"]
        }
    )

    return {
        "sql_result": result
    }



def generate_answer_node(
    state: CreditCardAgentState,
):
    """
    Generate final answer from retrieved information.
    """

    context = ""

    # Knowledge base documents
    if state.get("retrieved_documents"):

        for document in state["retrieved_documents"]:

            if hasattr(
                document,
                "page_content",
            ):
                context += (
                    document.page_content
                    + "\n"
                )

            else:
                context += (
                    str(document)
                    + "\n"
                )


    # Database result
    if state.get("sql_result"):

        context += (
            "\n"
            + str(state["sql_result"])
        )


    prompt = create_answer_prompt(
        question=state["question"],
        context=context,
    )


    response = llm.invoke(prompt)


    return {
        "answer": response.content
    }