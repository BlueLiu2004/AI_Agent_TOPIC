"""原版 Corrective RAG 的分支與回圈，加上三路 Router 和 MCP。"""

from pathlib import Path

from langgraph.graph import END, START, StateGraph

from config import Config
from knowledge_base import POLICY_DOCUMENTS, build_vectorstore
from nodes import RAGNodes
from state import OnboardingState


def route_by_source(state: OnboardingState) -> str:
    return state["route"]


def route_by_relevance(state: OnboardingState) -> str:
    if state["doc_grade"] == "relevant":
        return "build_web_query" if state["route"] == "hybrid" else "generate"
    if state["retry_count"] >= Config.MAX_QUERY_RETRIES:
        return "fallback_generate"
    return "rewrite_query"


class OnboardingGraph:
    def __init__(self):
        print("建立公司知識庫索引...")
        self.vectorstore = build_vectorstore()
        print(f"已建立 {len(POLICY_DOCUMENTS)} 筆文件索引。")
        self.nodes = RAGNodes(self.vectorstore)
        self.compiled_graph = self._build()

    def _build(self):
        graph = StateGraph(OnboardingState)
        graph.add_node("router", self.nodes.router_node)
        graph.add_node("retrieve", self.nodes.retrieve_node)
        graph.add_node("grade_documents", self.nodes.grade_documents_node)
        graph.add_node("rewrite_query", self.nodes.rewrite_query_node)
        graph.add_node("build_web_query", self.nodes.build_web_query_node)
        graph.add_node("tavily_search", self.nodes.tavily_search_node)
        graph.add_node("generate", self.nodes.generate_node)
        graph.add_node("fallback_generate", self.nodes.fallback_generate_node)

        graph.add_edge(START, "router")
        graph.add_conditional_edges("router", route_by_source, {
            "internal": "retrieve",
            "external": "build_web_query",
            "hybrid": "retrieve",
        })
        graph.add_edge("retrieve", "grade_documents")
        graph.add_conditional_edges("grade_documents", route_by_relevance, {
            "generate": "generate",
            "build_web_query": "build_web_query",
            "rewrite_query": "rewrite_query",
            "fallback_generate": "fallback_generate",
        })
        graph.add_edge("rewrite_query", "retrieve")
        graph.add_edge("build_web_query", "tavily_search")
        graph.add_edge("tavily_search", "generate")
        graph.add_edge("generate", END)
        graph.add_edge("fallback_generate", END)
        return graph.compile()

    def save_figure(self):
        figure_dir = Path(__file__).parent / "figure"
        figure_dir.mkdir(exist_ok=True)
        (figure_dir / "graph.mmd").write_text(
            self.compiled_graph.get_graph().draw_mermaid(), encoding="utf-8"
        )

    def get_compiled_graph(self):
        return self.compiled_graph
