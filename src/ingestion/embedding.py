import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


load_dotenv()


def create_embedding_model() -> OpenAIEmbeddings:
    """
    Create the embedding model used for KB documents.
    """

    return OpenAIEmbeddings(
        model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        ),
        api_key=os.getenv(
            "OPENAI_API_KEY"
        ),
    )


def generate_embeddings(
    documents: list[Document],
) -> list[dict]:
    """
    Generate embeddings for all document chunks.

    Returns a list containing:
        content
        embedding
        metadata
    """

    if not documents:
        return []

    embedding_model = create_embedding_model()

    texts = [
        document.page_content
        for document in documents
    ]

    vectors = embedding_model.embed_documents(
        texts
    )

    embedded_documents = []

    for document, vector in zip(
        documents,
        vectors,
    ):

        embedded_documents.append(
            {
                "content": document.page_content,
                "embedding": vector,
                "metadata": document.metadata,
            }
        )

    return embedded_documents
