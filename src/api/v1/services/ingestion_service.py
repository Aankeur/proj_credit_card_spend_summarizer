# we already ingested rdbms data so function: ingest transaction data is not required....but we have to implement it
# from src.ingestion.sql_ingestion import ingest_transaction_data


from src.ingestion.kb_ingestion import ingest_knowledge_base
from src.ingestion.sql_ingestion import check_transaction_database


def run_ingestion():

    db_result = check_transaction_database()

    if db_result["status"] != "success":
        return {
            "status": "failed",
            "database": db_result,
        }

    kb_result = ingest_knowledge_base()

    return {
        "status": "success",
        "database": db_result,
        "knowledge_base": kb_result,
    }
