import os

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()


COLLECTION_NAME = os.getenv(
    "PGVECTOR_COLLECTION_NAME",
    "credit_card_knowledgebase",
)

PG_CONNECTION_STRING = os.getenv(
    "PG_DATABASE_URL",
)


def create_embedding_model() -> OpenAIEmbeddings:
    """
    Create the embedding model used by the PGVector store.
    """

    return OpenAIEmbeddings(
        model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        ),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def get_vector_store() -> PGVector:
    """
    Return the LangChain PGVector store.

    The PGVector integration creates and manages the required
    LangChain vector-store tables in PostgreSQL.
    """

    if not PG_CONNECTION_STRING:
        raise ValueError(
            "PG_DATABASE_URL is not configured."
        )

    return PGVector(
        embeddings=create_embedding_model(),
        collection_name=COLLECTION_NAME,
        connection=PG_CONNECTION_STRING,
        use_jsonb=True,
    )


def insert_documents(
    documents: list[Document],
) -> int:
    """
    Insert LangChain Documents into PGVector.

    PGVector manages the vector-store tables and embeddings.
    """

    if not documents:
        return 0

    vector_store = get_vector_store()

    vector_store.add_documents(documents)

    return len(documents)


def get_document_count() -> int:
    """
    Return the number of documents stored in the
    current PGVector collection.
    """

    vector_store = get_vector_store()

    result = vector_store._make_sync_session().execute(
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