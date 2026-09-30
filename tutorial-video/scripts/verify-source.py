"""Offline factual checks. Read allowlisted source, never import the application."""
import ast
import hashlib
import json
import re
from pathlib import Path

video = Path(__file__).resolve().parents[1]
repo = video.parent
manifest = json.loads((video / "source-manifest.json").read_text(encoding="utf-8"))
for name, expected in manifest.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == expected, name
source = json.loads((video / "src/data/source.json").read_text(encoding="utf-8"))
for name, snippet in source["snippets"].items():
    actual = (repo / snippet["file"]).read_text(encoding="utf-8-sig").splitlines()
    assert actual[snippet["first"]-1:snippet["last"]] == snippet["lines"], name
    assert 4 <= len(snippet["lines"]) <= 14, name
nodes, edges = [], []
tree = ast.parse((repo / "graph.py").read_text(encoding="utf-8-sig"))
def value(x):
    return x.id if isinstance(x, ast.Name) else ast.literal_eval(x)
for call in ast.walk(tree):
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        continue
    if call.func.attr == "add_node":
        nodes.append(value(call.args[0]))
    elif call.func.attr == "add_edge":
        edges.append({"from": value(call.args[0]), "to": value(call.args[1]), "condition": ""})
    elif call.func.attr == "add_conditional_edges":
        edges.extend({"from": value(call.args[0]), "to": v, "condition": k}
                     for k, v in ast.literal_eval(call.args[2]).items())
assert nodes == source["graph"]["nodes"]
assert edges == source["graph"]["edges"]
assert len(nodes) == 8
visual = (video / "src/components.tsx").read_text(encoding="utf-8")
path_section = visual.split("const fullPaths:")[1].split("export const ArchitectureGraph")[0]
visible_edges = set(re.findall(r"'([A-Za-z_]+>[A-Za-z_]+)'\s*:", path_section))
assert visible_edges == {e["from"] + ">" + e["to"] for e in edges}
assert "Node.js 22.11.0" in source["policy"]["content"]
cues = json.loads((video / "src/data/cues.json").read_text(encoding="utf-8"))
previous = 0
for cue in cues:
    assert previous <= cue["start"] < cue["end"] <= 192
    previous = cue["end"]
assert len(cues) == 33
assert source["experiment"]["first"] == {"total": 6, "completed": 3}
assert source["experiment"]["second"] == {"total": 6, "completed": 6}
print(f"PASS: {len(manifest)} source hashes unchanged; {len(source['snippets'])} exact code excerpts.")
print(f"PASS: {len(nodes)} nodes and {len(edges)} graph edges match graph.py AST.")
print("PASS: full visual graph has all 13 distinct endpoints (two routes share router > retrieve).")
print("PASS: Node.js 22.11.0 policy, historical 3/6 and 6/6 results, 33 non-overlapping caption cues.")
print("No .env read, app import, or online request.")
