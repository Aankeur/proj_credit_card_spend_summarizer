from app.core.db import get_vector_store
from langchain_core.tools import tool
from psycopg.rows import dict_row
import psycopg
import os


@tool
def search_vector(
    query: str, k: int = 5, collection_name: str = "credit_card_knowledgebase"
):
    """this function is used to find the similar text using the similarity_Search method"""

    vector_store = get_vector_store(collection_name)
    docs = vector_store.similarity_search(query, k)
    output = [
        {
            "content": doc.page_content,
            "metadata": doc.metadat,
        }
        for doc in docs
    ]
    return output


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
def search_hybrid(
    query: str, k: int = 5, collection_name: str = "credit_card_knowledgebase"
):
    """Merge vector and fts results using RRF (Reciprocal Rank Fusion)
    Chunks appearing in both search results will rank higher than those in only one
    The constant 60 prevents top-ranked outputs from dominating
    How RRF scores for a chunk = sum of 1/(rank + 60)"""

    vector_search_results = search_vector.fun(query, 5, collection_name)
    fts_results = search_fts.fun(query, 5, collection_name)

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
