from src.ingestion.kb_ingestion import ingest_knowledge_base
from src.ingestion.sql_ingestion import check_transaction_database


def run_ingestion():

    print("1. Checking transaction database...")

    db_result = check_transaction_database()

    print("Database check completed:", db_result)

    if db_result["status"] != "success":
        return {
            "status": "failed",
            "database": db_result,
        }

    print("2. Starting knowledge base ingestion...")

    kb_result = ingest_knowledge_base()

    print("Knowledge base ingestion completed.")

    return {
        "status": "success",
        "database": db_result,
        "knowledge_base": kb_result,
    }


if __name__ == "__main__":

    print("========== STARTING INGESTION ==========")

    result = run_ingestion()

    print("\n========== INGESTION RESULT ==========")
    print(result)