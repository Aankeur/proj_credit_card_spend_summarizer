from src.agents.graph import credit_card_graph
from src.core.guardrails import guard_output

def process_query(request: dict):
    """
    Normal non-streaming execution.

    Used by:
    POST /api/v1/spend-summary/
    """

    question = request["question"]

    try:
        response = credit_card_graph.invoke(
            {
                "question": question,
                "route": "",
                "retrieved_documents": [],
                "sql_result": "",
                "answer": "",
                "citations": [],
                "retry_count": 0,
                "chat_history": request.get("chat_history", []),
            }
        )

        answer = response.get("answer", "",)

        answer = guard_output(answer)

        result = {
            "question": question,
            "response": answer,
        }

        if response.get("citations"):
            result["citations"] = response["citations"]

        return result

    except Exception as e:
        print("ERROR in processing query:", str(e))
        raise e
        print("========== QUERY SERVICE ERROR ==========")
        print(e)

    return {
        "question": question,
        "response": "I am unable to process your request at the moment. Please try again later.",
    }


async def process_query_stream(request: dict):
    """
    Streaming execution.

    Used by:
    POST /api/v1/spend-summary/stream
    """

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

        if event_name == "on_chat_model_stream":

            chunk = event["data"]["chunk"]

            content = getattr(
                chunk,
                "content",
                None,
            )

            if content:
                yield f"data: {content}\n\n"
