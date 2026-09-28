"""逐題記錄真實服務實測結果，輸出不含憑證的 JSON 證據。"""

import asyncio
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from onboarding_runner import DEMO_QUESTIONS, OnboardingRunner  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indices", nargs="*", type=int, default=list(range(1, len(DEMO_QUESTIONS) + 1)))
    parser.add_argument("--output", default="live_demo_results.json")
    args = parser.parse_args()
    output = ROOT / "experiments" / args.output
    report = {
        "run_started_at": datetime.now(ZoneInfo("Asia/Taipei")).isoformat(),
        "questions": [],
    }
    runner = OnboardingRunner()
    for index in args.indices:
        question = DEMO_QUESTIONS[index - 1]
        print(f"[{index}/{len(DEMO_QUESTIONS)}] {question}", flush=True)
        started = time.perf_counter()
        row = {"index": index, "question": question}
        try:
            state = await runner.ask_with_trace(question)
            row.update({
                "status": "completed",
                "route": state["route"],
                "doc_grade": state["doc_grade"],
                "retry_count": state["retry_count"],
                "retrieved_sources": [d.metadata.get("source", "") for d in state["documents"]],
                "web_query": state["web_query"],
                "web_called": state["web_called"],
                "web_urls": state["web_urls"],
                "web_error": state["web_error"],
                "final_answer": state["final_answer"],
                "trace": state["trace"],
            })
        except Exception as exc:
            row.update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)[:300]})
        row["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        report["questions"].append(row)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {row['status']} {row['elapsed_seconds']}s {row.get('route', row.get('error_type', ''))}", flush=True)
    report["run_finished_at"] = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"結果：{output}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
