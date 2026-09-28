"""命令列入口；每個問題建立一份可檢視的 State。"""

import asyncio

from langchain_core.messages import HumanMessage

from graph import OnboardingGraph


DEMO_QUESTIONS = [
    "公司的遠端工作政策是什麼？",
    "目前 Node.js 官方最新 LTS 是哪一版？",
    "公司要求使用哪一版的 Node.js？給我該版 Node.js 的官方下載網址。",
    "公司要求新人第一週學 Docker，請告訴我需要學哪些內容，並幫我找最新的 Docker 官方入門教學。",
    "公司的加班規定是什麼？目前台灣公開法規對加班有哪些規範？",
    "公司允許 telecommuting 嗎？",
]


class OnboardingRunner:
    def __init__(self):
        self.onboarding_graph = OnboardingGraph()
        self.app = self.onboarding_graph.get_compiled_graph()

    def save_figure(self):
        self.onboarding_graph.save_figure()

    async def ask_with_trace(self, question: str) -> dict:
        return await self.app.ainvoke({
            "messages": [HumanMessage(content=question)],
            "original_question": question,
            "question": question,
            "route": "internal",
            "documents": [],
            "doc_grade": "",
            "retry_count": 0,
            "internal_context": "",
            "web_query": "",
            "web_domains": [],
            "web_results": "",
            "web_urls": [],
            "web_error": "",
            "web_called": False,
            "final_answer": "",
            "trace": [],
        })

    async def ask(self, question: str) -> str:
        return (await self.ask_with_trace(question))["final_answer"]


async def main():
    runner = OnboardingRunner()
    runner.save_figure()
    for index, question in enumerate(DEMO_QUESTIONS, 1):
        print(f"\nDemo {index}：{question}")
        try:
            result = await runner.ask_with_trace(question)
        except Exception as exc:
            print(f"模型服務暫時無法完成這題（{type(exc).__name__}），繼續下一題。")
            continue
        print(f"路由：{result['route']}")
        print("流程：" + " → ".join(result["trace"]))
        print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
