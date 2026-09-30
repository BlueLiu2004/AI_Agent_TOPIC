"""驗證 NVIDIA passage/query payload 與真實 Chroma 的介接，不連線。"""

import os
import runpy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from knowledge_base import Config, NVIDIAEmbeddingFunction, POLICY_DOCUMENTS, build_vectorstore


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.payloads = []
        # 保留真正 SDK 的 payload、分批與 response 處理，只替換 HTTP transport。
        self.sdk = NVIDIAEmbeddings.model_construct(model="nvidia/nemotron-3-embed-1b")
        self.sdk._client = SimpleNamespace(get_req=self.respond)
        self.env = patch.dict(os.environ, {"NVIDIA_API_KEY": "unit-test-key"})
        self.factory = patch("knowledge_base.NVIDIAEmbeddings", return_value=self.sdk)
        self.env.start()
        self.mock_factory = self.factory.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.factory.stop)

    def respond(self, *, payload, extra_headers):
        self.payloads.append(payload)
        rows = [
            {"index": i, "embedding": [1.0, 0.0] if "Node.js" in text else [0.0, 1.0]}
            for i, text in enumerate(payload["input"])
        ]
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"data": rows[::-1]})

    def test_chroma_indexes_passages_and_searches_with_query_mode(self):
        collection = build_vectorstore()
        try:
            result = collection.query(query_texts=["公司要求哪版 Node.js？"], n_results=1)
            self.assertEqual(collection.count(), len(POLICY_DOCUMENTS))
            self.assertEqual(len(result["ids"][0]), 1)
            self.assertEqual(self.payloads[0]["input_type"], "passage")
            self.assertEqual(len(self.payloads[0]["input"]), 50)
            self.assertEqual(self.payloads[-1]["input_type"], "query")
            self.assertEqual(self.payloads[-1]["input"], ["公司要求哪版 Node.js？"])
            self.assertTrue(all(p["model"] == Config.EMBEDDING_MODEL for p in self.payloads))
        finally:
            collection._client.delete_collection(collection.name)

    def test_multiple_query_inputs_preserve_vector_shape_and_order(self):
        embedder = NVIDIAEmbeddingFunction(Config.EMBEDDING_MODEL)
        self.assertEqual(
            embedder.embed_query(input=["Node.js", "遠端工作"]),
            [[1.0, 0.0], [0.0, 1.0]],
        )
        self.assertTrue(all(p["input_type"] == "query" for p in self.payloads))

    def test_missing_key_fails_before_client_creation(self):
        with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "NVIDIA_API_KEY"):
                NVIDIAEmbeddingFunction(Config.EMBEDDING_MODEL)
        self.mock_factory.assert_not_called()

    def test_serialized_config_contains_no_credentials(self):
        embedder = NVIDIAEmbeddingFunction(Config.EMBEDDING_MODEL)
        self.assertEqual(embedder.get_config(), {"model": Config.EMBEDDING_MODEL})
        restored = NVIDIAEmbeddingFunction.build_from_config(embedder.get_config())
        self.assertEqual(restored.model, embedder.model)

    def test_config_reads_embedding_model_variable(self):
        with patch.dict(os.environ, {"EMBEDDING_MODEL": "nvidia/test-embed", "EMBEDDING_MODEL_NAME": "old-local-model"}), patch("dotenv.load_dotenv"):
            config = runpy.run_path(str(Path(__file__).parents[1] / "config.py"))["Config"]
        self.assertEqual(config.EMBEDDING_MODEL, "nvidia/test-embed")
