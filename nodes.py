"""每個方法對應一個 LangGraph 節點；Tavily 僅在 tavily_search_node 呼叫。"""

import json
import os
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import chromadb
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel

from config import Config
from llm import ProjectLLM
from state import OnboardingState

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)


class RouteDecision(BaseModel):
    route: Literal["internal", "external", "hybrid"]


class GradeDecision(BaseModel):
    score: Literal["relevant", "not_relevant"]
    reasoning: str


class WebQueryDecision(BaseModel):
    query: str


def _official_domains(question: str) -> list[str]:
    if "Node.js" in question or "node.js" in question.lower():
        return ["nodejs.org"]
    if "Docker" in question or "docker" in question.lower():
        return ["docker.com"]
    if "Python" in question:
        return ["python.org"]
    if "LangGraph" in question:
        return ["docs.langchain.com"]
    if "加班" in question and ("法規" in question or "勞基法" in question):
        return ["mol.gov.tw", "law.moj.gov.tw"]
    return []


class RAGNodes:
    def __init__(self, vectorstore: chromadb.Collection):
        provider = ProjectLLM()
        base_llm = provider.get_llm()
        self.llm = base_llm.with_retry(stop_after_attempt=2)
        self.vectorstore = vectorstore
        self.router_llm = provider.structured(base_llm, RouteDecision).with_retry(stop_after_attempt=2)
        self.grader_llm = provider.structured(base_llm, GradeDecision).with_retry(stop_after_attempt=2)
        self.query_llm = provider.structured(base_llm, WebQueryDecision).with_retry(stop_after_attempt=2)
        self.router_prompt = _load_prompt("route.txt")
        self.grade_prompt = _load_prompt("grade_documents.txt")
        self.rewrite_prompt = _load_prompt("rewrite_query.txt")
        self.generate_prompt = _load_prompt("generate_with_rag.txt")
        self.fallback_prompt = _load_prompt("generate_fallback.txt")
        self.web_prompt = _load_prompt("generate_with_web.txt")

    def router_node(self, state: OnboardingState) -> dict:
        try:
            decision = self.router_llm.invoke([
                SystemMessage(content=self.router_prompt),
                HumanMessage(content=state["original_question"]),
            ])
            route = decision.route
            if route not in ("internal", "external", "hybrid"):
                raise ValueError("無效的路由分類")
            note = f"router: {route}"
            if "公司" in state["original_question"] and any(
                term in state["original_question"] for term in ("官方", "公開法規", "目前台灣", "最新")
            ):
                route = "hybrid"
                note = "router: hybrid（內部規範與外部資訊並問）"
        except (ValueError, AttributeError, TypeError) as exc:
            route = "internal"
            note = f"router: 輸出格式錯誤，暫以 internal 處理（{type(exc).__name__}）"
        return {"route": route, "trace": state["trace"] + [note]}

    def retrieve_node(self, state: OnboardingState) -> dict:
        result = self.vectorstore.query(
            query_texts=[state["question"]],
            n_results=Config.RETRIEVER_K,
            include=["documents", "metadatas"],
        )
        texts = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        docs = [Document(page_content=text, metadata=meta or {})
                for text, meta in zip(texts, metas)]
        titles = [d.metadata.get("title", d.metadata.get("source", "?")) for d in docs]
        return {"documents": docs, "trace": state["trace"] + [f"retrieve: {', '.join(titles) or '無結果'}"]}

    def grade_documents_node(self, state: OnboardingState) -> dict:
        if not state["documents"]:
            return {"doc_grade": "not_relevant", "trace": state["trace"] + ["grade: 無文件"]}
        docs_text = "\n\n".join(
            f"[{d.metadata.get('source', '?')}] {d.page_content}"
            for d in state["documents"]
        )
        decision = self.grader_llm.invoke([
            SystemMessage(content=self.grade_prompt),
            HumanMessage(content=f"原始問題：{state['original_question']}\n檢索問題：{state['question']}\n文件：\n{docs_text}"),
        ])
        return {
            "doc_grade": decision.score,
            "internal_context": docs_text if decision.score == "relevant" else "",
            "trace": state["trace"] + [f"grade: {decision.score}"],
        }

    def rewrite_query_node(self, state: OnboardingState) -> dict:
        response = self.llm.invoke([
            SystemMessage(content=self.rewrite_prompt),
            HumanMessage(content=f"原始問題：{state['original_question']}\n目前查詢：{state['question']}"),
        ])
        query = _extract_text(response.content).strip() or state["question"]
        return {
            "question": query,
            "retry_count": state["retry_count"] + 1,
            "trace": state["trace"] + [f"rewrite: {query}"],
        }

    def build_web_query_node(self, state: OnboardingState) -> dict:
        original = state["original_question"]
        context = state["internal_context"]
        domains = _official_domains(original)
        version = re.search(r"Node\.js\s*(\d+)", context, re.IGNORECASE)
        if state["route"] == "hybrid" and version and "Node.js" in original:
            query = f"Node.js {version.group(1)} official download site:nodejs.org"
        elif "Docker" in original and "教學" in original:
            query = "Docker official get started tutorial site:docs.docker.com"
        elif "加班" in original and ("法規" in original or "勞基法" in original):
            query = "臺灣 勞動基準法 延長工時 加班費 勞動部 最新規定"
        else:
            decision = self.query_llm.invoke([
                SystemMessage(content=_load_prompt("build_web_query.txt")),
                HumanMessage(content=f"原始問題：{original}\n已查證內部資料：\n{context or '無'}"),
            ])
            query = decision.query.strip()
        return {
            "web_query": query,
            "web_domains": domains,
            "trace": state["trace"] + [f"build_web_query: {query}"],
        }

    async def tavily_search_node(self, state: OnboardingState) -> dict:
        key = os.getenv("TAVILY_API_KEY", "").strip()
        if not key:
            error = "未設定 TAVILY_API_KEY，無法呼叫 Tavily MCP。"
            return {"web_error": error, "trace": state["trace"] + [f"tavily: {error}"]}
        try:
            client = MultiServerMCPClient({
                "tavily": {
                    "transport": "streamable_http",
                    "url": "https://mcp.tavily.com/mcp/",
                    "headers": {"Authorization": f"Bearer {key}"},
                }
            })
            tools = await client.get_tools()
            search = next((tool for tool in tools if tool.name in ("tavily_search", "tavily-search")), None)
            if search is None:
                raise RuntimeError("MCP 伺服器沒有提供 tavily_search")
            args = {"query": state["web_query"], "search_depth": "basic", "max_results": 5}
            if state["web_domains"]:
                args["include_domains"] = state["web_domains"]
            result = await search.ainvoke(args)
            raw = _extract_text(result.content) if hasattr(result, "content") else _extract_text(result)
            if getattr(result, "status", None) == "error" or "Tavily API error:" in raw:
                raise RuntimeError("Tavily 搜尋回報錯誤")
            try:
                payload = json.loads(raw)
                items = payload.get("results", [])
                if state["web_domains"]:
                    items = [
                        item for item in items
                        if any(
                            (urlparse(item.get("url", "")).hostname or "") == domain
                            or (urlparse(item.get("url", "")).hostname or "").endswith("." + domain)
                            for domain in state["web_domains"]
                        )
                    ]
                urls = [item["url"] for item in items if item.get("url")]
                web_results = "\n\n".join(
                    f"Title: {item.get('title', '')}\nURL: {item['url']}\nContent: {item.get('content', '')[:1000]}"
                    for item in items if item.get("url")
                )
            except (ValueError, AttributeError, TypeError):
                web_results = raw
                urls = re.findall(r"(?m)^URL:\s*(https?://\S+)", raw)
            urls = list(dict.fromkeys(urls))
            if not urls:
                raise RuntimeError("Tavily 未提供可引用的搜尋結果")
            return {
                "web_results": web_results,
                "web_urls": urls,
                "web_called": True,
                "trace": state["trace"] + [f"tavily_search: {len(urls)} 個網址"],
            }
        except RuntimeError as exc:
            error = f"目前無法取得 Tavily MCP 搜尋結果：{exc}。"
            return {
                "web_error": error,
                "web_called": True,
                "trace": state["trace"] + [f"tavily_search: {error}"],
            }
        except Exception as exc:
            error = f"目前無法取得 Tavily MCP 搜尋結果（{type(exc).__name__}）。"
            return {
                "web_error": error,
                "web_called": True,
                "trace": state["trace"] + [f"tavily_search: {error}"],
            }

    def generate_node(self, state: OnboardingState) -> dict:
        route = state["route"]
        if route == "internal":
            system = self.generate_prompt.format(context=state["internal_context"])
        else:
            system = self.web_prompt.format(
                route=route,
                internal_context=state["internal_context"] or "無已查證內部資料",
                web_results=state["web_results"] or "無外部搜尋結果",
                web_error=state["web_error"] or "無",
            )
        response = self.llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=state["original_question"]),
        ])
        answer = _extract_text(response.content).strip()
        for url in re.findall(r"https?://[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+", answer):
            if url.rstrip(".,;:)]") not in state["web_urls"]:
                answer = answer.replace(url, "（請見下方外部來源）")
        if state["web_error"]:
            answer += f"\n\n外部資訊狀態：{state['web_error']}"
        if state["web_urls"]:
            answer += "\n\n外部來源：\n" + "\n".join(state["web_urls"])
        return {
            "messages": [response],
            "final_answer": answer,
            "trace": state["trace"] + ["generate"],
        }

    def fallback_generate_node(self, state: OnboardingState) -> dict:
        if state["route"] == "hybrid":
            answer = "內部知識庫未找到足以查證公司規範的文件，因此不會推測公司要求的版本或用該版本搜尋。請先向人資、IT 或文件負責人確認內部規定。"
        else:
            answer = self.fallback_prompt
        return {"final_answer": answer, "trace": state["trace"] + ["fallback_generate"]}
