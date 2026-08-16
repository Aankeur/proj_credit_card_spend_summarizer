from sqlalchemy import text

<<<<<<< HEAD
from src.core.db import get_db_conn
=======
from src.core.vector_db import get_db_conn
>>>>>>> feature/Ingestion_fix

REQUIRED_TABLES = [
    "customers",
    "credit_cards",
    "card_transactions",
    "reward_transactions",
    "billing_statements",
]

<<<<<<< HEAD
=======

>>>>>>> feature/Ingestion_fix
def check_transaction_database():

    db = get_db_conn()

    try:
        existing_tables = []

        for table in REQUIRED_TABLES:
<<<<<<< HEAD
            query = text(
                """
=======
            query = text("""
>>>>>>> feature/Ingestion_fix
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
<<<<<<< HEAD
                """
            )
=======
                """)
>>>>>>> feature/Ingestion_fix

            exists = db.execute(query, {"table_name": table}).scalar()

            if exists:
                existing_tables.append(table)

        return {
            "status": (
                "success" if len(existing_tables) == len(REQUIRED_TABLES) else "failed"
            ),
            "tables_found": existing_tables,
            "tables_expected": REQUIRED_TABLES,
        }

    finally:
        db.close()
