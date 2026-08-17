from src.agents.graph import credit_card_graph


def process_query(request: dict):
    """
    Normal non-streaming execution.

    Used by:
    POST /api/v1/spend-summary/
    """

    question = request["question"]

    response = credit_card_graph.invoke(
        {
            "question": question,
            "route": "",
            "retrieved_documents": [],
            "sql_result": "",
            "answer": "",
            "citations": [],
            "retry_count": 0,
        }
    )

    print("========== GRAPH RESPONSE ==========")
    print(response)

    print("========== FINAL ANSWER ==========")
    print(response.get("answer"))

    result = {
        "question": question,
        "response": response.get(
            "answer",
            "",
        ),
    }

    if response.get("citations"):
        result["citations"] = response["citations"]

    return result



async def process_query_stream(request: dict):
    """
    Streaming execution.

    Used by:
    POST /api/v1/spend-summary/stream
    """

    print("=== STREAM START ===")

    question = request["question"]

    async for event in credit_card_graph.astream_events(
        {
            "question": question,
            "route": "",
            "retrieved_documents": [],
            "sql_result": "",
            "answer": "",
            "citations": [],
            "retry_count": 0,
        },
        version="v2",
    ):

        event_name = event["event"]

        print("EVENT:", event_name)

        if event_name == "on_chat_model_stream":

            chunk = event["data"]["chunk"]

            content = getattr(
                chunk,
                "content",
                None,
            )

            if content:

                print(
                    "STREAM CHUNK:",
                    content,
                )

                yield f"data: {content}\n\n"