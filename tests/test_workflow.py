"""以可控 LLM、向量庫與 MCP 工具測試真正的節點和圖連線。"""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import AIMessage

from graph import OnboardingGraph
from knowledge_base import POLICY_DOCUMENTS
from nodes import RAGNodes
from onboarding_runner import OnboardingRunner


class FakeRouter:
    def invoke(self, messages):
        question = messages[-1].content
        internal = "公司" in question
        external = any(word in question for word in ("官方", "目前", "法規", "最新"))
        route = "hybrid" if internal and external else ("internal" if internal else "external")
        return SimpleNamespace(route=route)


class FakeGrader:
    def invoke(self, messages):
        text = messages[-1].content
        if "查無此項" in text or ("telecommuting" in text and "檢索問題：公司允許 telecommuting" in text):
            return SimpleNamespace(score="not_relevant")
        return SimpleNamespace(score="relevant")


class FakeQuery:
    def invoke(self, messages):
        return SimpleNamespace(query="官方資訊 site:example.org")


class FakeLLM:
    def invoke(self, messages):
        if "目前查詢：" in messages[-1].content:
            if "量子傳送門" in messages[-1].content:
                return AIMessage(content="量子傳送門規範")
            return AIMessage(content="遠端工作政策")
        return AIMessage(content="根據提供的資料回答。")


class FakeVector:
    def query(self, query_texts, n_results, include):
        question = query_texts[0]
        if "Node.js" in question:
            title, content = "Node.js 標準版本", "公司標準開發環境要求使用 Node.js 22。"
        elif "Docker" in question:
            title, content = "到職第一週清單", "新人第一週學 Docker image、container、Dockerfile。"
        elif "加班" in question:
            title, content = "加班政策", "公司加班須事前主管核准。"
        elif "遠端工作" in question:
            title, content = "遠端工作政策", "完成適應期者每週可遠端工作三天。"
        else:
            title, content = "其他文件", "查無此項規範。"
        return {"documents": [[f"{title}：{content}"]], "metadatas": [[{"source": "test-01", "title": title}]]}


class FakeSearch:
    name = "tavily_search"

    def __init__(self):
        self.args = []

    async def ainvoke(self, args):
        self.args.append(args)
        domain = args.get("include_domains", ["nodejs.org"])[0]
        url = {
            "nodejs.org": "https://nodejs.org/en/download",
            "docker.com": "https://docs.docker.com/get-started/",
            "mol.gov.tw": "https://www.mol.gov.tw/",
        }[domain]
        return [{"type": "text", "text": f'{{"results":[{{"title":"官方文件","url":"{url}","content":"官方資訊"}}]}}'}]


class FakeClient:
    def __init__(self, search):
        self.search = search

    async def get_tools(self):
        return [self.search]


def make_runner():
    nodes = object.__new__(RAGNodes)
    nodes.vectorstore = FakeVector()
    nodes.llm = FakeLLM()
    nodes.router_llm = FakeRouter()
    nodes.grader_llm = FakeGrader()
    nodes.query_llm = FakeQuery()
    nodes.router_prompt = "router"
    nodes.grade_prompt = "grade"
    nodes.rewrite_prompt = "rewrite"
    nodes.generate_prompt = "{context}"
    nodes.fallback_prompt = "未找到公司內部規範。"
    nodes.web_prompt = "{route} {internal_context} {web_results} {web_error}"
    wrapper = object.__new__(OnboardingGraph)
    wrapper.nodes = nodes
    runner = object.__new__(OnboardingRunner)
    runner.app = wrapper._build()
    return runner, nodes


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_dataset_size_and_categories(self):
        self.assertEqual(len(POLICY_DOCUMENTS), 50)
        self.assertEqual(len({d.metadata["category"] for d in POLICY_DOCUMENTS}), 5)
        self.assertEqual(len({d.metadata["source"] for d in POLICY_DOCUMENTS}), 50)

    async def test_internal_only(self):
        runner, _ = make_runner()
        result = await runner.ask_with_trace("公司的遠端工作政策是什麼？")
        self.assertEqual(result["route"], "internal")
        self.assertEqual(result["doc_grade"], "relevant")
        self.assertFalse(result["web_called"])
        self.assertFalse(result["web_query"])

    async def test_external_only(self):
        runner, _ = make_runner()
        search = FakeSearch()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}), patch(
            "nodes.MultiServerMCPClient", return_value=FakeClient(search)
        ):
            result = await runner.ask_with_trace("目前 Node.js 官方最新 LTS 是哪一版？")
        self.assertEqual(result["route"], "external")
        self.assertTrue(result["web_called"])
        self.assertEqual(result["documents"], [])
        self.assertEqual(search.args[0]["include_domains"], ["nodejs.org"])

    async def test_hybrid_query_uses_rag_version(self):
        runner, _ = make_runner()
        search = FakeSearch()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}), patch(
            "nodes.MultiServerMCPClient", return_value=FakeClient(search)
        ):
            result = await runner.ask_with_trace("公司要求使用哪一版的 Node.js？給我該版 Node.js 的官方下載網址。")
        self.assertEqual(result["route"], "hybrid")
        self.assertEqual(result["web_query"], "Node.js 22 official download site:nodejs.org")
        self.assertEqual(search.args[0]["query"], result["web_query"])
        self.assertIn("Node.js 22", result["internal_context"])
        self.assertEqual(result["web_urls"], ["https://nodejs.org/en/download"])

    async def test_docker_training_hybrid(self):
        runner, _ = make_runner()
        search = FakeSearch()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}), patch(
            "nodes.MultiServerMCPClient", return_value=FakeClient(search)
        ):
            result = await runner.ask_with_trace("公司要求新人第一週學 Docker，請告訴我需要學哪些內容，並幫我找最新的 Docker 官方入門教學。")
        self.assertEqual(result["route"], "hybrid")
        self.assertIn("Docker official", result["web_query"])
        self.assertEqual(search.args[0]["include_domains"], ["docker.com"])
        self.assertEqual(result["web_urls"], ["https://docs.docker.com/get-started/"])

    async def test_overtime_regulation_hybrid(self):
        runner, _ = make_runner()
        search = FakeSearch()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}), patch(
            "nodes.MultiServerMCPClient", return_value=FakeClient(search)
        ):
            result = await runner.ask_with_trace("公司的加班規定是什麼？目前台灣公開法規對加班有哪些規範？")
        self.assertEqual(result["route"], "hybrid")
        self.assertIn("加班政策", result["internal_context"])
        self.assertEqual(result["web_domains"], ["mol.gov.tw", "law.moj.gov.tw"])
        self.assertEqual(result["web_urls"], ["https://www.mol.gov.tw/"])

    async def test_corrective_retry(self):
        runner, _ = make_runner()
        result = await runner.ask_with_trace("公司允許 telecommuting 嗎？")
        self.assertEqual(result["route"], "internal")
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(result["question"], "遠端工作政策")
        self.assertEqual(result["doc_grade"], "relevant")
        self.assertTrue(any("rewrite:" in step for step in result["trace"]))

    async def test_fallback(self):
        runner, _ = make_runner()
        result = await runner.ask_with_trace("公司有量子傳送門政策嗎？")
        self.assertEqual(result["retry_count"], 2)
        self.assertIn("未找到", result["final_answer"])
        self.assertEqual(result["trace"][-1], "fallback_generate")

    async def test_missing_tavily_key(self):
        runner, _ = make_runner()
        with patch.dict(os.environ, {"TAVILY_API_KEY": ""}):
            result = await runner.ask_with_trace("目前 Node.js 官方最新 LTS 是哪一版？")
        self.assertIn("TAVILY_API_KEY", result["web_error"])
        self.assertFalse(result["web_called"])

    async def test_tavily_connection_failure(self):
        runner, _ = make_runner()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}), patch(
            "nodes.MultiServerMCPClient", side_effect=ConnectionError("offline")
        ):
            result = await runner.ask_with_trace("目前 Node.js 官方最新 LTS 是哪一版？")
        self.assertTrue(result["web_called"])
        self.assertIn("Tavily MCP", result["web_error"])
        self.assertEqual(result["web_urls"], [])

    async def test_malformed_router_output(self):
        runner, nodes = make_runner()
        nodes.router_llm = SimpleNamespace(invoke=lambda _: SimpleNamespace(route="unknown"))
        result = await runner.ask_with_trace("公司的遠端工作政策是什麼？")
        self.assertEqual(result["route"], "internal")
        self.assertIn("輸出格式錯誤", result["trace"][0])

    async def test_obvious_hybrid_corrects_router_misclassification(self):
        runner, nodes = make_runner()
        nodes.router_llm = SimpleNamespace(invoke=lambda _: SimpleNamespace(route="external"))
        with patch.dict(os.environ, {"TAVILY_API_KEY": ""}):
            result = await runner.ask_with_trace("公司要求使用哪一版的 Node.js？給我該版 Node.js 的官方下載網址。")
        self.assertEqual(result["route"], "hybrid")
        self.assertIn("Node.js 22", result["internal_context"])

    async def test_verified_url_before_chinese_punctuation_is_kept(self):
        _, nodes = make_runner()
        url = "https://nodejs.org/en/download/archive/v22.11.0"
        nodes.llm = SimpleNamespace(invoke=lambda _: AIMessage(content=f"官方網址：{url}（來源：搜尋結果）"))
        state = {
            "route": "hybrid",
            "internal_context": "Node.js 22",
            "web_results": f"URL: {url}",
            "web_error": "",
            "original_question": "官方網址？",
            "web_urls": [url],
            "trace": [],
        }
        answer = nodes.generate_node(state)["final_answer"]
        self.assertIn(url, answer)
        self.assertNotIn("未經搜尋驗證", answer)

    async def test_unverified_url_is_replaced_by_source_reference(self):
        _, nodes = make_runner()
        nodes.llm = SimpleNamespace(invoke=lambda _: AIMessage(content="下載網址：https://nodejs.org/en/download"))
        state = {
            "route": "hybrid",
            "internal_context": "Node.js 22",
            "web_results": "URL: https://nodejs.org/en/download/archive/v22.11.0",
            "web_error": "",
            "original_question": "官方網址？",
            "web_urls": ["https://nodejs.org/en/download/archive/v22.11.0"],
            "trace": [],
        }
        answer = nodes.generate_node(state)["final_answer"]
        self.assertIn("請見下方外部來源", answer)
        self.assertNotIn("下載網址：https://nodejs.org/en/download\n", answer)


if __name__ == "__main__":
    unittest.main()
