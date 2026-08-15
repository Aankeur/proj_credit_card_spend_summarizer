from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import psycopg
from psycopg.rows import dict_row

import os

load_dotenv()

PG_CONNECTION = os.getenv("PG_CONNECTION_STRING")


def get_embeddings():
    return OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL"), dimensions=1536)


def get_vector_store(collection_name: str, pre_delete_collection: bool = False):
    try:
        return PGVector(
            collection_name=collection_name,
            connection=PG_CONNECTION,
            embeddings=get_embeddings(),
            use_jsonb=True,  # for better querying during retrieval
            pre_delete_collection=pre_delete_collection,
        )
    except Exception as e:
        print(f"error while connectinmg to pg vector db : {e}")
        raise RuntimeError("failed to connect to db") from e


def get_rdbms_connection():
    return psycopg.connect(PG_CONNECTION, row_factory=dict_row)