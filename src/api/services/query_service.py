from src.agents.rag_agent import credit_card_spent_agent


def process_query(request: dict):

    question = request["question"]

    response = credit_card_spent_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": str(request),
                }
            ]
        }
    )

    structured_response = response["structured_response"]

    print("========== ALL MESSAGES ==========")

    for message in response["messages"]:
        for tool_call in getattr(message, "tool_calls", []):
            print("Tool:", tool_call["name"])

    print("========== RESPONSE ==========")
    print(structured_response.response)

    result = {
        "question": question,
        "response": structured_response.response,
    }

    if structured_response.citations:
        result["citations"] = structured_response.citations

    return result
