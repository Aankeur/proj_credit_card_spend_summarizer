from src.agents.state import CreditCardAgentState
from src.tools.nl2sql import generate_sql

from src.agents.rag_agent import (
    llm,
    structured_llm,
    create_answer_prompt,
)

from src.tools.tools import (
    search_hybrid,
    search_rdbms,
    search_fts,
    search_vector,
)

# def greeting_node(
#     state: CreditCardAgentState,
# ):
#     """
#     Handles greetings without retrieval.
#     """

#     return {
#         "answer": "Hi! How can I help you today?",
#     }


def greeting_node(
    state: CreditCardAgentState,
):
    """
    Handles greetings without retrieval.
    """

    response = llm.invoke(f"""
Respond to this greeting naturally.
If the user introduces themselves, acknowledge their name.
Do not use retrieval.

User message:
{state["question"]}
""")

    return {
        "answer": response.content,
    }


def router_node(
    state: CreditCardAgentState,
):
    """
    Decide whether the query needs:
    - Knowledge base retrieval
    - Customer database retrieval
    """

    question = state["question"]

    router_prompt = f"""
You are a query classifier for a credit card assistant.

Classify the user question into exactly one category:

- rdbms:
  Use when the question requires customer-specific or card-specific data from PostgreSQL.
  Examples:
  - spending
  - transactions
  - merchants
  - billing statements
  - rewards earned
  - card details
  - customer details
  - credit limit
  - outstanding amount
  - available limit

- knowledge_base:
  Use when the question asks about general credit card information.
  Examples:
  - benefits
  - features
  - eligibility rules
  - fee waiver policy
  - reward program explanation

  - hybrid:
  Use when the question requires BOTH:
  1. General card information from knowledge base
  2. Customer/card specific information from PostgreSQL

  Examples:
  - What are the benefits of my NorthStar Gold card and my available limit for CC-881001?
  - Explain Gold card features and tell me my outstanding balance.
  - What reward benefits are available and how many reward points do I have?

User question:
{question}

Return only one word:
rdbms
or
knowledge_base
or
hybrid
"""

    response = llm.invoke(router_prompt)

    route = response.content.strip().lower()

    if route not in ["rdbms", "knowledge_base", "hybrid"]:
        route = "knowledge_base"

    print("========== ROUTER DECISION ==========")
    print(route)

    return {"route": route}


def knowledge_node(
    state: CreditCardAgentState,
):
    """
    Retrieve card/product information
    using hybrid search.
    """

    documents = search_hybrid.invoke({"query": state["question"]})

    return {"retrieved_documents": documents}


def rdbms_node(
    state: CreditCardAgentState,
):
    """
    Retrieve customer-specific information
    from PostgreSQL.
    """

    print("========== RDBMS NODE HIT ==========")
    print(state["question"])

    sql_query = generate_sql(
        state["question"],
        state.get("chat_history", []),
    )
    print("========== GENERATED SQL ==========")
    print(sql_query)

    result = search_rdbms.invoke({"sql_query": sql_query})

    print("========== SQL RESULT ==========")
    print(result)

    return {"sql_result": result}


def hybrid_node(state):
    print("========== HYBRID NODE HIT ==========")

    question = state["question"]

    # Call knowledge retrieval
    knowledge_result = knowledge_node(state)

    # Call rdbms retrieval
    rdbms_result = rdbms_node(state)

    return {
        **knowledge_result,
        **rdbms_result,
    }


# def generate_answer_node(
#     state: CreditCardAgentState,
# ):
#     """
#     Generate final answer from retrieved information.
#     """

#     context = ""

#     # Knowledge base documents
#     if state.get("retrieved_documents"):

#         for document in state["retrieved_documents"]:

#             if hasattr(
#                 document,
#                 "page_content",
#             ):
#                 context += document.page_content + "\n"

#             else:
#                 context += str(document) + "\n"

#     # Database result
#     if state.get("sql_result"):

#         print("========== SQL RESULT ==========")
#         print(state.get("sql_result"))

#         context += "\n" + str(state["sql_result"])

#     prompt = create_answer_prompt(
#         question=state["question"],
#         context=context,
#     )

#     print("========== FINAL PROMPT ==========")
#     print(prompt)
#     response = llm.invoke(prompt)

#     citations = []

#     for document in state.get("retrieved_documents", []):

#         metadata = document.get("metadata", {})

#         if metadata.get("source_file") and metadata.get("page_number"):
#             citations.append(
#                 f"{metadata['source_file']} - Page {metadata['page_number']}"
#             )
#     print("========== ANSWER MODEL RESPONSE ==========")
#     print(response.content)
#     return {
#         "answer": response.content,
#         "citations": citations,
#     }


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
                context += document.page_content + "\n"

            else:
                context += str(document) + "\n"

    # Database result
    if state.get("sql_result"):

        print("========== SQL RESULT ==========")
        print(state.get("sql_result"))

        context += "\n" + str(state["sql_result"])

    prompt = create_answer_prompt(
        question=state["question"],
        context=context,
        chat_history=state.get("chat_history", []),
    )

    print("========== FINAL PROMPT ==========")
    print(prompt)

    response = structured_llm.invoke(prompt)

    print("========== ANSWER MODEL RESPONSE ==========")
    print(response.response)

    citations = []

    for document in state.get("retrieved_documents", []):

        metadata = document.get(
            "metadata",
            {},
        )

        if metadata.get("source_file") and metadata.get("page_number"):
            citations.append(
                f"{metadata['source_file']} - Page {metadata['page_number']}"
            )

    return {
        "answer": response.response,
        "citations": citations,
    }
