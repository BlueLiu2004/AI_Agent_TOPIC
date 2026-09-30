"""TechCore 的虛構示範政策；每次啟動重建記憶體內 Chroma。"""

import json
import os
from pathlib import Path

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

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


class NVIDIAEmbeddingFunction(EmbeddingFunction[Documents]):
    """將 Chroma 文件／查詢分別交給 NVIDIA passage／query embedding。"""

    def __init__(self, model: str):
        key = os.getenv("NVIDIA_API_KEY")
        if not key:
            raise ValueError("使用 NVIDIA embedding 請設定 NVIDIA_API_KEY。")
        self.model = model
        self.client = NVIDIAEmbeddings(model=model, api_key=key)

    def __call__(self, input: Documents) -> Embeddings:
        return self.client.embed_documents(list(input))

    def embed_query(self, input: Documents) -> Embeddings:
        return [self.client.embed_query(text) for text in input]

    @staticmethod
    def name() -> str:
        return "onboardbot_nvidia"

    def get_config(self) -> dict:
        return {"model": self.model}

    @staticmethod
    def build_from_config(config: dict) -> "NVIDIAEmbeddingFunction":
        return NVIDIAEmbeddingFunction(model=config["model"])


def build_vectorstore() -> chromadb.Collection:
    embed_fn = NVIDIAEmbeddingFunction(model=Config.EMBEDDING_MODEL)
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
