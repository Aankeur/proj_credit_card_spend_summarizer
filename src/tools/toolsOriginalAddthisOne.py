import re
import psycopg
import os
from app.core.db import get_vector_store, get_rdbms_connection
from psycopg.rows import dict_row
from langchain_core.tools import tool

_raw_conn = os.getenv("PG_CONNECTION_STRING_FTS")

USE_MOCK = True


@tool
def search_fts(
    query: str, k: int = 5, collection_name: str = "credit_card_knowledgebase"
):
    """Keyword search against the stored chunks using Postgres
    tsvector/tsquery/ts_rank"""

    sql = """
        SELECT
            e.document  AS content,
            e.cmetadata  AS metadata,
            ts_rank(
                to_tsvector('english', e.document),
                plainto_tsquery('english', %(query)s)
            )  AS fts_rank
        FROM  langchain_pg_embedding  e
        JOIN  langchain_pg_collection c ON c.uuid = e.collection_id
        WHERE c.name = %(collection)s
            AND to_tsvector('english', e.document)
                @@ plainto_tsquery('english', %(query)s)
        ORDER BY fts_rank DESC
        LIMIT %(k)s;
    """

    with psycopg.connect(_raw_conn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"query": query, "collection": collection_name, "k": k})
            rows = cur.fetchall()

    output = [
        {
            "content": row["content"],
            "metadata": row["metadata"],
            "fts_rank": round(float(row["fts_rank"]), 4),
        }
        for row in rows
    ]

    return output


@tool
def search_vector(
    query: str, k: int = 5, collection_name: str = "credit_card_knowledgebase"
):
    """
    this function is used to find the similar text using the similarity_Search method
    """

    if USE_MOCK:
        return [
            {
                "content": (
                    "NorthStar Gold is designed for salaried professionals. "
                    "The annual fee is Rs. 999 + GST and the annual fee waiver "
                    "threshold is Rs. 1,00,000 annual spend."
                ),
                "metadata": {
                    "category": "card_benefits",
                    "card_variant": "NorthStar Gold",
                },
            },
            {
                "content": (
                    "NorthStar Gold has a credit limit range of "
                    "Rs. 1,00,000 to Rs. 3,00,000."
                ),
                "metadata": {
                    "category": "card_details",
                    "card_variant": "NorthStar Gold",
                },
            },
        ][:k]

    vector_store = get_vector_store(collection_name)
    docs = vector_store.similarity_search(query, k)

    output = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in docs
    ]

    return output


@tool
def search_hybrid(
    query: str, k: int = 5, collection_name: str = "credit_card_knowledgebase"
):
    """Merge vector and fts results using RRF (Reciprocal Rank Fusion)
    Chunks appearing in both search results will rank higher than those in only one
    The constant 60 prevents top-ranked outputs from dominating
    How RRF scores for a chunk = sum of 1/(rank + 60)
    """

    vector_search_results = search_vector.func(query, 5, collection_name)
    fts_results = search_fts.func(query, 5, collection_name)

    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    for rank, doc in enumerate(vector_search_results):
        # Use the first 120 chars of the chunk text as an identity key.
        # Same chunk retrieved by both searches -> same key -> its scores add up.
        key = doc["content"][:120]
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (60 + rank + 1)
        chunk_map[key] = {"content": doc["content"], "metadata": doc["metadata"]}

    for rank, item in enumerate(fts_results):
        key = item["content"][:120]
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (60 + rank + 1)
        chunk_map[key] = {"content": item["content"], "metadata": item["metadata"]}
    # sort the results and higher scoring chunk appear at top of the final list
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return [chunk_map[key] for key, _ in ranked[:k]]


@tool
def search_rdbms(
    operation: str, card_id: str, billing_month: str, start_date: str, end_date: str
):
    """
    Read-only retrieval tool for credit card data stored in PostgreSQL.

    Supported operations:
    - monthly_spend
    - category_breakdown
    - top_merchants
    - international_spend
    - reward_points
    - mom_comparison
    - fee_waiver
    """

    queries = {
        "monthly_spend": """
            SELECT
                SUM(amount) AS total_spend,
                COUNT(*) AS total_transactions
            FROM card_transactions
            WHERE card_id = %(card_id)s
              AND txn_date >= %(start_date)s
              AND txn_date < %(end_date)s;
        """,
        "top_merchants": """
            SELECT
                merchant_name,
                SUM(amount) AS amount,
                COUNT(*) AS transaction_count
            FROM card_transactions
            WHERE card_id = %(card_id)s
              AND txn_date >= %(start_date)s
              AND txn_date < %(end_date)s
            GROUP BY merchant_name
            ORDER BY amount DESC
            LIMIT 5;
        """,
    }

    if operation not in queries:
        return {"error": f"Unsupported operation: {operation}"}

    params = {
        "card_id": card_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    with get_rdbms_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(queries[operation], params)
            result = cursor.fetchall()

    return result


if __name__ == "__main__":
    result = search_vector.invoke(
        {"query": "What are the benefits of NorthStar Gold?", "k": 2}
    )

    print(result)
