from typing import Annotated, Literal

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class OnboardingState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    original_question: str
    question: str
    route: Literal["internal", "external", "hybrid"]
    documents: list[Document]
    doc_grade: str
    retry_count: int
    internal_context: str
    web_query: str
    web_domains: list[str]
    web_results: str
    web_urls: list[str]
    web_error: str
    web_called: bool
    final_answer: str
    trace: list[str]
