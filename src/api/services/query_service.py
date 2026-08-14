from src.agents.rag_agent import credit_card_spent_agent


def process_query(request: dict):

    question = request["question"]

    response = credit_card_spent_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        }
    )

    print(
        "****************** Response returned by agent *************************",
        response,
    )

    return {
        "question": question,
        "message": "Query received successfully.",
        "response": response,
    }
