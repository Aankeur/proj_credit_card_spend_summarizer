from sqlalchemy import text

from src.core.db import get_db_conn


EXPECTED_TABLES = {
    "customers": 6,
    "credit_cards": 6,
    "card_transactions": 47,
    "reward_transactions": 5,
    "billing_statements": 4,
}


def validate_ingestion():

    result = {}

    db = get_db_conn()

    try:

        for table, expected in EXPECTED_TABLES.items():

            query = text(
                f"SELECT COUNT(*) FROM {table}"
            )

            actual = db.execute(query).scalar()

            result[table] = {
                "expected": expected,
                "actual": actual,
                "valid": expected == actual,
            }

        return result

    finally:

        db.close()