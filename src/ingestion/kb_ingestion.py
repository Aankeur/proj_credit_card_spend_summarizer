import base64
import io
import os
import re
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.core.vector_db import insert_documents
from src.ingestion.chunking import create_chunks

# from src.ingestion.embedding import generate_embeddings

load_dotenv()


def _describe_image_with_openai(img_b64: str) -> str:
    """
    Generate a searchable description of an image using a vision model.

    The generated description becomes the searchable text for
    the image content.
    """

    vision_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

    vision_llm = ChatOpenAI(
        model=vision_model,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Describe this image in detail for document search "
                    "indexing. Include chart titles, axis labels, legend "
                    "entries, key data points, trends, numbers, and any "
                    "visible text. Be specific. The description is for "
                    "a RAG application."
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            },
        ]
    )

    try:
        response = vision_llm.invoke([message])

        content = response.content

        if isinstance(content, list):
            return " ".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ).strip()

        return str(content).strip()

    except Exception as exc:  # noqa: BLE001
        print(f"Image description failed: {exc}")

        return ""


def _create_metadata(
    content_type: str,
    element_type: str,
    section: str | None,
    page_number,
    source_file: str,
    position: dict | None = None,
    image_base64: str | None = None,
):
    """
    Create metadata associated with an extracted document element.
    """

    return {
        "content_type": content_type,
        "element_type": element_type,
        "section": section,
        "page_number": page_number,
        "source_file": source_file,
        "position": position,
        "image_base64": image_base64,
    }


def parse_document(file_path: str) -> list[dict]:
    """
    Parse the Knowledge Base document using Docling.

    Returns a list containing:
        content
        content_type
        metadata

    content_type:
        text
        table
        image
    """

    converter = DocumentConverter(allowed_formats=[InputFormat.DOCX, InputFormat.PDF])

    result = converter.convert(file_path)

    document = result.document

    parsed_chunks = []

    current_section = None

    source_file = os.path.basename(file_path)

    for item in document.iterate_items():
        if isinstance(item, tuple):
            node, _level = item

        else:
            node = item

        label = str(getattr(node, "label", "")).lower()

        # ---------------------------------------------------------
        # Skip repeated page headers and footers
        # ---------------------------------------------------------

        if label in (
            "page_header",
            "page_footer",
        ):
            continue

        # ---------------------------------------------------------
        # Page number / position
        # ---------------------------------------------------------

        prov = getattr(node, "prov", None)

        page_number = prov[0].page_no if prov else None

        print(
            "DEBUG:",
            label,
            "page_number=",
            page_number,
        )

        position = None

        if prov and hasattr(prov[0], "bbox") and prov[0].bbox is not None:
            bbox = prov[0].bbox

            position = {
                "l": bbox.l,
                "t": bbox.t,
                "r": bbox.r,
                "b": bbox.b,
            }

        # ---------------------------------------------------------
        # Section headers / title
        # ---------------------------------------------------------

        if "section_header" in label or label == "title":
            text = getattr(node, "text", "").strip()

            if text:
                current_section = text

                parsed_chunks.append(
                    {
                        "content": text,
                        "content_type": "text",
                        "metadata": _create_metadata(
                            content_type="text",
                            element_type=label,
                            section=current_section,
                            page_number=page_number,
                            source_file=source_file,
                            position=position,
                        ),
                    }
                )

        # ---------------------------------------------------------
        # Tables
        # ---------------------------------------------------------

        elif "table" in label:
            table_text = ""

            # Preferred approach:
            # Docling -> pandas DataFrame
            if hasattr(node, "export_to_dataframe"):
                try:
                    dataframe = node.export_to_dataframe()

                    if dataframe is not None and not dataframe.empty:
                        rows = []

                        headers = [str(column).strip() for column in dataframe.columns]

                        for _, row in dataframe.iterrows():
                            pairs = []

                            for header, value in zip(headers, row):
                                value = str(value).strip()

                                if value not in (
                                    "",
                                    "nan",
                                    "None",
                                ):
                                    pairs.append(f"{header}: {value}")

                            if pairs:
                                rows.append(" | ".join(pairs))

                        table_text = "\n".join(rows)

                except Exception as exc:  # noqa: BLE001
                    print(f"DataFrame extraction failed: {exc}")

            # -----------------------------------------------------
            # Fallback: HTML -> plain text
            # -----------------------------------------------------

            if not table_text and hasattr(node, "export_to_html"):
                try:
                    raw_html = node.export_to_html(document)

                    table_text = re.sub(r"<[^>]+>", " ", raw_html or "")

                    table_text = re.sub(r"\s+", " ", table_text).strip()

                except Exception as exc:  # noqa: BLE001
                    print(f"HTML table extraction failed: {exc}")

            # -----------------------------------------------------
            # Final fallback
            # -----------------------------------------------------

            if not table_text:
                table_text = getattr(node, "text", "")

            if table_text.strip():

                print(
                    "DEBUG TEXT:",
                    text[:50],
                    "| section=",
                    current_section,
                    "| page=",
                    page_number,
                )
                parsed_chunks.append(
                    {
                        "content": table_text.strip(),
                        "content_type": "table",
                        "metadata": _create_metadata(
                            content_type="table",
                            element_type="table",
                            section=current_section,
                            page_number=page_number,
                            source_file=source_file,
                            position=position,
                        ),
                    }
                )

        # ---------------------------------------------------------
        # Pictures / figures / charts
        # ---------------------------------------------------------

        elif "picture" in label or "figure" in label or label == "chart":
            image_base64 = None

            caption = getattr(node, "text", "") or ""

            # -----------------------------------------------------
            # Extract image
            # -----------------------------------------------------

            try:
                if hasattr(node, "get_image"):
                    pil_image = node.get_image(document)

                    if pil_image:
                        buffer = io.BytesIO()

                        pil_image.save(buffer, format="PNG")

                        image_base64 = base64.b64encode(buffer.getvalue()).decode()

                # Fallback for older Docling versions
                elif hasattr(node, "image") and node.image:
                    pil_image = getattr(node.image, "pil_image", None)

                    if pil_image:
                        buffer = io.BytesIO()

                        pil_image.save(buffer, format="PNG")

                        image_base64 = base64.b64encode(buffer.getvalue()).decode()

            except Exception as exc:  # noqa: BLE001
                print(f"Image extraction failed: {exc}")

            # -----------------------------------------------------
            # Generate searchable image description
            # -----------------------------------------------------

            if image_base64:
                description = _describe_image_with_openai(image_base64)

                content = (
                    description or caption.strip() or f"[Image on page {page_number}]"
                )

            else:
                content = caption.strip() or f"[Image on page {page_number}]"

            parsed_chunks.append(
                {
                    "content": content,
                    "content_type": "image",
                    "metadata": _create_metadata(
                        content_type="image",
                        element_type=label,
                        section=current_section,
                        page_number=page_number,
                        source_file=source_file,
                        position=position,
                        image_base64=image_base64,
                    ),
                }
            )

        # ---------------------------------------------------------
        # Normal text / paragraphs / lists / captions
        # ---------------------------------------------------------

        else:
            text = getattr(node, "text", "")

            if text and text.strip():
                parsed_chunks.append(
                    {
                        "content": text.strip(),
                        "content_type": "text",
                        "metadata": _create_metadata(
                            content_type="text",
                            element_type=label,
                            section=current_section,
                            page_number=page_number,
                            source_file=source_file,
                            position=position,
                        ),
                    }
                )

    return parsed_chunks


def ingest_knowledge_base(file_path):

    parsed_elements = parse_document(str(file_path))

    chunks = create_chunks(parsed_elements)

    inserted_count = insert_documents(chunks)

    return {
        "status": "success",
        "source": str(file_path),
        "parsed_elements": len(parsed_elements),
        "chunks": len(chunks),
        "embedded_documents": len(chunks),
        "inserted_documents": inserted_count,
    }


# if __name__ == "__main__":
#     files = list(Path("data").glob("*.pdf"))

#     if not files:
#         raise FileNotFoundError("No PDF found in data directory")

#     file_path = files[0]

#     result = ingest_knowledge_base(file_path)

#     print("\n========== INGESTION RESULT ==========")
#     print(f"Status: {result['status']}")
#     print(f"Parsed elements: {result['parsed_elements']}")
#     print(f"Chunks created: {result['chunks']}")
#     print(f"Embeddings generated: {result['embedded_documents']}")
#     print(f"Documents inserted into vector DB: {result['inserted_documents']}")

## run as uv run python -m src.ingestion.kb_ingestion
