import hashlib
import json

from sqlalchemy import text

from src.core.db import get_db_conn


def generate_document_hash(
    content: str,
    metadata: dict,
) -> str:

    content_type = metadata.get("content_type")

    if content_type == "image":
        image_base64 = metadata.get("image_base64")

        if image_base64:
            return hashlib.sha256(image_base64.encode("utf-8")).hexdigest()

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_vector_table(embedding_dimension: int):
    """
    Create the pgvector extension and the knowledge_documents table.
    """

    db = get_db_conn()

    try:
        # Enable pgvector
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create vector table
        db.execute(
            text(f"""
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    content_hash VARCHAR(64) UNIQUE NOT NULL,
                    embedding VECTOR({embedding_dimension}),
                    metadata JSONB
                )
                """)
        )

        db.commit()

    finally:
        db.close()


def insert_documents(
    embedded_documents: list[dict],
) -> int:
    """
    Insert embedded KB chunks into PostgreSQL/pgvector.

    Duplicate chunks are ignored using content_hash.

    Each document should contain:
        content
        embedding
        metadata
    """

    if not embedded_documents:
        return 0

    # Determine embedding dimension
    embedding_dimension = len(embedded_documents[0]["embedding"])

    # Make sure table exists
    create_vector_table(embedding_dimension)

    db = get_db_conn()

    try:
        inserted_count = 0

        for document in embedded_documents:
            content = document["content"]

            embedding = document["embedding"]

            metadata = document.get(
                "metadata",
                {},
            )

            content_hash = generate_document_hash(content, metadata,)

            embedding_string = "[" + ",".join(str(value) for value in embedding) + "]"

            result = db.execute(
                text("""
                    INSERT INTO knowledge_documents
                    (
                        content,
                        content_hash,
                        embedding,
                        metadata
                    )
                    VALUES
                    (
                        :content,
                        :content_hash,
                        CAST(:embedding AS vector),
                        CAST(:metadata AS jsonb)
                    )
                    ON CONFLICT (content_hash)
                    DO NOTHING
                    RETURNING id
                    """),
                {
                    "content": content,
                    "content_hash": content_hash,
                    "embedding": embedding_string,
                    "metadata": json.dumps(metadata),
                },
            )

            inserted_id = result.scalar_one_or_none()

            if inserted_id is not None:
                inserted_count += 1


        db.commit()

        return inserted_count

    except Exception:
        db.rollback()

        raise

    finally:
        db.close()


def get_document_count() -> int:
    """
    Return the number of documents currently
    stored in the vector table.
    """

    db = get_db_conn()

    try:
        result = db.execute(
            text("""
                SELECT COUNT(*)
                FROM knowledge_documents
                """)
        )

        return result.scalar_one()

    finally:
        db.close()
