import re
import psycopg
import os
from src.core.vector_db import get_vector_store, get_rdbms_connection
from psycopg.rows import dict_row
from langchain_core.tools import tool

_raw_conn = os.getenv("PG_CONNECTION_STRING_FTS")


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

    vector_store = get_vector_store()
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
    operation: str,
    card_id: str = "",
    billing_month: str = "",
    start_date: str = "",
    end_date: str = "",
    customer_id: str = "",
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
    - customer_details
    - card_details

    """
    print("===== RDBMS TOOL CALLED =====")

    queries = {
        "monthly_spend": """
        SELECT
            SUM(amount) AS total_spend,
            COUNT(*) AS total_transactions
        FROM card_transactions
       WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
           AND (%(start_date)s = '' OR txn_date >= %(start_date)s::date)
      AND (%(end_date)s = '' OR txn_date < %(end_date)s::date)
    """,
        "category_breakdown": """
        SELECT
            category_name,
            SUM(amount) AS total_spend
        FROM card_transactions
        WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
          AND (%(start_date)s = '' OR txn_date >= %(start_date)s::date)
      AND (%(end_date)s = '' OR txn_date < %(end_date)s::date)
        GROUP BY category_name
        ORDER BY total_spend DESC;
    """,
        "top_merchants": """
        SELECT
            merchant_name,
            SUM(amount) AS amount,
            COUNT(*) AS transaction_count
        FROM card_transactions
        WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
          AND (%(start_date)s = '' OR txn_date >= %(start_date)s::date)
      AND (%(end_date)s = '' OR txn_date < %(end_date)s::date)
        GROUP BY merchant_name
        ORDER BY amount DESC
        LIMIT 5;
    """,
        "international_spend": """
    SELECT
        SUM(amount) AS international_spend,
        COUNT(*) AS international_transactions
    FROM card_transactions
    WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
      AND is_international = true
      AND (%(start_date)s = '' OR txn_date >= %(start_date)s::date)
      AND (%(end_date)s = '' OR txn_date < %(end_date)s::date);
""",
        "reward_points": """
    SELECT
        COALESCE(SUM(reward_pts_earned), 0) AS total_reward_points
    FROM card_transactions
    WHERE txn_date >= %(start_date)s
      AND txn_date < %(end_date)s
      AND (%(card_id)s = '' OR card_id = %(card_id)s)
""",
        "mom_comparison": """
        SELECT
            DATE_TRUNC('month', txn_date) AS month,
            SUM(amount) AS total_spend
        FROM card_transactions
        WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
          AND (%(start_date)s = '' OR txn_date >= %(start_date)s::date)
      AND (%(end_date)s = '' OR txn_date < %(end_date)s::date)
        GROUP BY DATE_TRUNC('month', txn_date)
        ORDER BY month;
    """,
        "fee_waiver": """
        SELECT
            SUM(amount) AS yearly_spend
        FROM card_transactions
       WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
           AND (%(start_date)s = '' OR txn_date >= %(start_date)s::date)
      AND (%(end_date)s = '' OR txn_date < %(end_date)s::date)
    """,
        "customer_details": """
    SELECT
        customer_id,
        full_name,
        email,
        mobile,
        dob,
        kyc_status,
        created_at
    FROM customers
    WHERE customer_id = %(customer_id)s;
""",
        "card_details": """
    SELECT
        card_id,
        card_variant,
        status,
        credit_limit,
        available_limit,
        cash_limit,
        outstanding_amt,
        min_due,
        statement_date,
        due_date,
        issued_date,
        reward_points,
        created_at,
        customer_id
    FROM credit_cards
       WHERE (%(card_id)s = '' OR card_id = %(card_id)s)
""",
    }

    if operation not in queries:
        return {"error": f"Unsupported operation: {operation}"}

    params = {
        "customer_id": customer_id,
        "card_id": card_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    print("OPERATION:", operation)
    print("CARD ID:", card_id)
    print("START DATE:", start_date)
    print("END DATE:", end_date)

    with get_rdbms_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(queries[operation], params)
            result = cursor.fetchall()

    print("RESULT:")
    print(result)
    return result

    # if __name__ == "__main__":
    #     result = search_rdbms.invoke(
    #         {
    #             "operation": "monthly_spend",
    #             "card_id": "CC001",
    #             "billing_month": "2026-04",
    #             "start_date": "2026-03-26",
    #             "end_date": "2026-04-25",
    #         }
    #     )
