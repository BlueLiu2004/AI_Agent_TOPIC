"""TechCore 的虛構示範政策；每次啟動重建記憶體內 Chroma。"""

import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from langchain_core.documents import Document

from config import Config


def load_documents() -> list[Document]:
    records = json.loads((Path(__file__).parent / "knowledge.json").read_text(encoding="utf-8"))
    return [
        Document(
            page_content=f"{item['title']}：{item['content']}",
            metadata={
                "source": item["source"],
                "title": item["title"],
                "category": item["category"],
            },
        )
        for item in records
    ]


POLICY_DOCUMENTS = load_documents()


def build_vectorstore() -> chromadb.Collection:
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=Config.EMBEDDING_MODEL
    )
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="onboarding_policies",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(
        ids=[d.metadata["source"] for d in POLICY_DOCUMENTS],
        documents=[d.page_content for d in POLICY_DOCUMENTS],
        metadatas=[d.metadata for d in POLICY_DOCUMENTS],
    )
    return collection
