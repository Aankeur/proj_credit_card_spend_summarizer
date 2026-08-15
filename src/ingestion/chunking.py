from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Text is split into smaller chunks.
# Tables and images are kept as individual semantic units initially.
TEXT_CHUNK_SIZE = 800
TEXT_CHUNK_OVERLAP = 100

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=TEXT_CHUNK_SIZE,
    chunk_overlap=TEXT_CHUNK_OVERLAP,
)


def create_chunks(parsed_elements: list[dict]) -> list[Document]:
    """
    Convert Docling output into LangChain Documents.

    Text:
        Split into smaller chunks.

    Tables:
        Keep as one semantic unit.

    Images:
        Keep as one semantic unit.
        The content should already contain the VLM description
        generated during Docling ingestion.
    """

    chunks = []

    for element in parsed_elements:
        content = element.get("content", "").strip()

        if not content:
            continue

        content_type = element.get(
            "content_type",
            "text",
        )

        metadata = element.get(
            "metadata",
            {},
        )

        # ---------------------------------------------------------
        # Normal text
        # ---------------------------------------------------------

        if content_type == "text":
            split_documents = text_splitter.create_documents(
                [content],
                metadatas=[metadata],
            )

            for document in split_documents:
                document.metadata["content_type"] = "text"

                chunks.append(document)

        # ---------------------------------------------------------
        # Tables
        # ---------------------------------------------------------

        elif content_type == "table":
            chunks.append(
                Document(
                    page_content=content,
                    metadata={
                        **metadata,
                        "content_type": "table",
                    },
                )
            )

        # ---------------------------------------------------------
        # Images
        # ---------------------------------------------------------

        elif content_type == "image":
            chunks.append(
                Document(
                    page_content=content,
                    metadata={
                        **metadata,
                        "content_type": "image",
                    },
                )
            )

    return chunks
