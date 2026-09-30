"""指定版本下載入口的回歸測試；使用原始案例網址，不呼叫模型或網路。"""
import unittest
from nodes import RAGNodes


class DownloadSourceTests(unittest.TestCase):
    def setUp(self):
        self.nodes = object.__new__(RAGNodes)
        self.release = "https://nodejs.org/en/blog/release/v22.11.0"
        self.archive = "https://nodejs.org/en/download/archive/v22.11.0"
        self.state = {
            "route": "hybrid",
            "original_question": "公司要求哪版 node.js？給我官方下載網址。",
            "internal_context": "[it-01] 公司要求使用 Node.js 22.11.0，CI 以 22 為基準。",
            "web_error": "",
            "web_urls": [
                "https://nodejs.org/en/blog/announcements/v22-release-announce",
                self.release,
                "https://nodejs.org/en/blog/release/v22.22.0",
                "https://nodejs.org/en/download/archive/v22",
                "https://nodejs.org/es/download/archive/v22.22.0",
            ],
            "trace": [],
        }

    def answer(self):
        return self.nodes.generate_node(self.state)["final_answer"]

    def test_search_preserves_patch_version_and_case_insensitive_question(self):
        result = self.nodes.build_web_query_node(self.state)
        self.assertEqual(result["web_query"], "Node.js 22.11.0 official download site:nodejs.org")

    def test_reported_case_selects_only_exact_release_page(self):
        answer = self.answer()
        self.assertIn("官方發行頁（含下載連結）", answer)
        self.assertIn(self.release, answer)
        self.assertIn("[it-01]", answer)
        self.assertIn("v22.11.0", answer)
        self.assertNotIn("請見下方外部來源", answer)
        for url in self.state["web_urls"]:
            if url != self.release:
                self.assertNotIn(url, answer)

    def test_download_archive_is_preferred_and_sources_are_deduplicated(self):
        self.state["web_urls"] += [self.archive, self.archive]
        answer = self.answer()
        self.assertIn(f"[官方版本下載頁]({self.archive})", answer)
        self.assertNotIn(self.release, answer)
        self.assertEqual(answer.split("外部來源：")[1], f"<{self.archive}>")

    def test_no_match_does_not_recommend_another_version(self):
        self.state["web_urls"].remove(self.release)
        answer = self.answer()
        self.assertIn("本次搜尋未找到版本完全相符", answer)
        self.assertNotIn("https://", answer)

    def test_rejects_spoofed_domains_and_version_prefixes(self):
        self.state["web_urls"] = [
            "https://nodejs.org.evil.example/en/blog/release/v22.11.0",
            "https://evil.example/en/download/archive/v22.11.0",
            "https://nodejs.org/en/blog/release/v22.11.01",
            "https://nodejs.org/en/blog/release/v22.11.0-rc.1",
        ]
        self.assertIn("本次搜尋未找到版本完全相符", self.answer())
        self.assertNotIn("https://", self.answer())

    def test_conflicting_internal_versions_require_confirmation(self):
        self.state["internal_context"] += "\n[it-02] 公司要求 Node.js 22.22.0。"
        self.assertIn("請先向 IT 確認", self.answer())
        self.assertNotIn("https://", self.answer())
