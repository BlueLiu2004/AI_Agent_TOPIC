import os

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.getenv("ONBOARDBOT_ENV_FILE", os.path.join(os.path.dirname(__file__), ".env")))


class Config:
    LLM_PROVIDER     = os.getenv("LLM_PROVIDER", "nvidia" if os.getenv("NVIDIA_API_KEY") else "gemini").lower()
    NVIDIA_MODEL     = os.getenv("CHAT_MODEL", "nvidia/nemotron-3-super-120b-a12b")
    MODEL_NAME        = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
    TEMPERATURE       = float(os.getenv("GEMINI_TEMPERATURE", 0.2))
    MAX_RETRIES       = int(os.getenv("GEMINI_MAX_RETRIES", 2))
    EMBEDDING_MODEL   = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    RETRIEVER_K       = int(os.getenv("RAG_RETRIEVER_K", 4))
    MAX_QUERY_RETRIES = int(os.getenv("RAG_MAX_QUERY_RETRIES", 2))
