import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg
from psycopg.rows import dict_row

load_dotenv()


COLLECTION_NAME = os.getenv(
    "PGVECTOR_COLLECTION_NAME",
    "credit_card_knowledgebase",
)

PG_CONNECTION_STRING = os.getenv("PG_DATABASE_URL")
PG_CONNECTION_STRING_FTS = os.getenv("PG_CONNECTION_STRING_FTS")


if not PG_CONNECTION_STRING:
    raise ValueError("PG_DATABASE_URL is not configured.")


engine = create_engine(
    PG_CONNECTION_STRING,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db_conn():
    return SessionLocal()


def create_embedding_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        ),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def get_vector_store() -> PGVector:
    return PGVector(
        embeddings=create_embedding_model(),
        collection_name=COLLECTION_NAME,
        connection=PG_CONNECTION_STRING,
        use_jsonb=True,
    )


def get_rdbms_connection():
    return psycopg.connect(PG_CONNECTION_STRING_FTS, row_factory=dict_row)


def insert_documents(
    documents: list[Document],
) -> int:
    if not documents:
        return 0

    vector_store = get_vector_store()
    vector_store.add_documents(documents)

    return len(documents)


def get_document_count() -> int:
    vector_store = get_vector_store()

    with vector_store._make_sync_session() as session:
        result = session.execute(
            """
            SELECT COUNT(*)
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c
              ON e.collection_id = c.uuid
            WHERE c.name = :collection_name
            """,
            {
                "collection_name": COLLECTION_NAME,
            },
        )

        return result.scalar_one()
