from pathlib import Path
from fastapi import UploadFile
from src.ingestion.ingestion import ingest_knowledge_base


async def upload_document(file: UploadFile):
    Data = Path("data")
    Data.mkdir(exist_ok=True)
    file_path = Data / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    ingestion_result = ingest_knowledge_base(file_path)
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "ingestion": ingestion_result,
    }
