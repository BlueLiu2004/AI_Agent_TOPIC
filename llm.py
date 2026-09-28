"""保留原版 LLM 包裝位置，依現有金鑰選 Gemini 或 NVIDIA。"""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import Config


class ProjectLLM:
    def get_llm(self):
        if Config.LLM_PROVIDER == "nvidia":
            key = os.getenv("NVIDIA_API_KEY")
            if not key:
                raise ValueError("請設定 NVIDIA_API_KEY。")
            return ChatNVIDIA(model=Config.NVIDIA_MODEL, api_key=key, temperature=1.0).bind(thinking_mode=False)
        if Config.LLM_PROVIDER == "gemini":
            if not os.getenv("GOOGLE_API_KEY"):
                raise ValueError("請設定 GOOGLE_API_KEY。")
            return ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                max_retries=Config.MAX_RETRIES,
            )
        raise ValueError("LLM_PROVIDER 只能是 nvidia 或 gemini。")

    def structured(self, llm, schema):
        if Config.LLM_PROVIDER == "nvidia":
            # 目前託管端點支援 json_object，但拒絕 guided_json/json_schema。
            return llm.bind(response_format={"type": "json_object"}) | PydanticOutputParser(pydantic_object=schema)
        return llm.with_structured_output(schema)
