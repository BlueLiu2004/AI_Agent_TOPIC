"""Read only allowlisted source and saved evidence; never import the app or dotenv."""
import ast
import hashlib
import json
from pathlib import Path

VIDEO = Path(__file__).resolve().parents[1]
REPO = VIDEO.parent
FILES = ["README.md", "state.py", "graph.py", "nodes.py", "knowledge_base.py",
         "llm.py", "config.py", "onboarding_runner.py", "tests/test_workflow.py",
         "knowledge.json", "OnboardBot_中文實驗報告.md"]
FILES += [str(p.relative_to(REPO)).replace("\\", "/") for p in (REPO / "prompts").glob("*.txt")]
FILES += [str(p.relative_to(REPO)).replace("\\", "/") for p in (REPO / "experiments").glob("*.json")]

def snippet(file, first, last):
    lines = (REPO / file).read_text(encoding="utf-8-sig").splitlines()
    return {"file": file, "first": first, "last": last, "lines": lines[first-1:last]}

graph = ast.parse((REPO / "graph.py").read_text(encoding="utf-8-sig"))
nodes, edges = [], []
for call in ast.walk(graph):
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        continue
    def val(x):
        return x.id if isinstance(x, ast.Name) else ast.literal_eval(x)
    if call.func.attr == "add_node":
        nodes.append(val(call.args[0]))
    elif call.func.attr == "add_edge":
        edges.append({"from": val(call.args[0]), "to": val(call.args[1]), "condition": ""})
    elif call.func.attr == "add_conditional_edges":
        for k, v in ast.literal_eval(call.args[2]).items():
            edges.append({"from": val(call.args[0]), "to": v, "condition": k})

data = json.loads((REPO / "knowledge.json").read_text(encoding="utf-8-sig"))
policy = next(x for x in data if x["source"] == "it-01")
assert "Node.js 22" in policy["content"], "Revisit the storyboard: policy version changed"
old = json.loads((REPO / "experiments/live_demo_results.json").read_text(encoding="utf-8-sig"))
recent = json.loads((REPO / "experiments/live_demo_2026-09-25.json").read_text(encoding="utf-8-sig"))
source = {
    "snippets": {
        "state": snippet("state.py", 11, 21),
        "routing": snippet("graph.py", 13, 22),
        "edges": snippet("graph.py", 44, 48),
        "urls": snippet("nodes.py", 251, 256),
        "retryTest": snippet("tests/test_workflow.py", 171, 178),
    },
    "graph": {"nodes": nodes, "edges": edges},
    "policy": policy,
    "datasetSize": len(data),
    "experiment": {
        "first": {"total": len(old["questions"]), "completed": sum(q["status"] == "completed" for q in old["questions"])},
        "second": {"total": len(recent["questions"]), "completed": sum(q["status"] == "completed" for q in recent["questions"])},
        "hybrid": {k: recent["questions"][2][k] for k in ["route", "doc_grade", "web_query", "web_urls", "trace"]},
        "correctiveActual": {k: recent["questions"][5][k] for k in ["route", "retry_count", "trace"]},
    },
}
(VIDEO / "src/data").mkdir(parents=True, exist_ok=True)
(VIDEO / "src/data/source.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
manifest = {f: hashlib.sha256((REPO / f).read_bytes()).hexdigest() for f in FILES}
(VIDEO / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Snapshot: {len(FILES)} sources; {len(nodes)} nodes; {len(edges)} edges; no app imports.")
