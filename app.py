"""最小 Gradio 介面，顯示回答與 LangGraph State 摘要。"""

import gradio as gr

from onboarding_runner import OnboardingRunner


class OnboardingApp:
    def __init__(self):
        self.runner = OnboardingRunner()

    async def respond(self, question: str):
        if not question.strip():
            return "請輸入問題。", {}
        try:
            result = await self.runner.ask_with_trace(question.strip())
        except Exception as exc:
            return f"目前模型服務無法完成問答（{type(exc).__name__}），請稍後重試。", {}
        debug = {
            "route": result["route"],
            "retrieved_documents": [
                {"title": d.metadata.get("title"), "source": d.metadata.get("source")}
                for d in result["documents"]
            ],
            "doc_grade": result["doc_grade"],
            "retry_count": result["retry_count"],
            "retrieval_question": result["question"],
            "web_query": result["web_query"],
            "tavily_mcp_called": result["web_called"],
            "web_urls": result["web_urls"],
            "web_error": result["web_error"],
            "trace": result["trace"],
        }
        return result["final_answer"], debug

    def launch(self):
        with gr.Blocks(title="TechCore OnboardBot") as demo:
            gr.Markdown("# TechCore OnboardBot\n虛構公司新人助理：內部知識庫、公開搜尋與混合問答。")
            question = gr.Textbox(label="問題", lines=2, value="公司要求使用哪一版的 Node.js？給我該版 Node.js 的官方下載網址。")
            submit = gr.Button("查詢")
            answer = gr.Markdown(label="回答")
            debug = gr.JSON(label="Debug / Agent Trace")
            submit.click(self.respond, inputs=question, outputs=[answer, debug])
        demo.launch()


if __name__ == "__main__":
    OnboardingApp().launch()
