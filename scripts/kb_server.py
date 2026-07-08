#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local LLM wiki server with graph rebuild, node-note cache and DeepSeek generation."""
from __future__ import annotations

import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("KB_PORT", "8765"))
REBUILD = ROOT / "scripts" / "rebuild_graph.py"
GRAPH = ROOT / "graph" / "graph.json"
DOC_DIRS = [ROOT / x for x in ["00_入口", "01_项目复盘", "02_技术地图", "03_问题库", "04_设备与部署"]]
CACHE_DIR = ROOT / "graph" / "node_notes"
ENV_FILE = ROOT / ".env.local"


def load_env_file() -> None:
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"\''))


load_env_file()
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/chat/completions")

TYPE_DIR = {
    "project": "01_项目复盘",
    "concept": "02_技术地图",
    "library": "02_技术地图",
    "acceleration": "02_技术地图",
    "service": "02_技术地图",
    "device": "02_技术地图",
    "tool": "02_技术地图",
    "issue": "03_问题库",
    "deployment": "04_设备与部署",
}

TYPE_LABEL = {
    "project": "项目",
    "concept": "概念",
    "library": "库",
    "acceleration": "硬件加速",
    "service": "服务",
    "device": "设备",
    "tool": "工具",
    "issue": "问题",
    "deployment": "部署",
}



def safe_id(value: str) -> str:
    value = value.strip()[:160]
    value = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fff]+", "-", value)
    return value.strip(".-") or "node"


def cache_path(node_id: str) -> Path:
    return CACHE_DIR / f"{safe_id(node_id)}.json"


def read_json_body(handler: http.server.BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
    return json.loads(raw or "{}")


def snapshot() -> dict[str, float]:
    result: dict[str, float] = {}
    for base in DOC_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            try:
                result[str(path)] = path.stat().st_mtime
            except OSError:
                pass
    return result


def rebuild() -> None:
    subprocess.run([sys.executable, str(REBUILD)], cwd=str(ROOT), check=False)


def watcher() -> None:
    last = snapshot()
    while True:
        time.sleep(2)
        current = snapshot()
        if current != last:
            print("\n检测到 Markdown 变化，正在重建知识图谱...")
            rebuild()
            last = current


def load_graph() -> dict:
    if not GRAPH.exists():
        rebuild()
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def find_node(graph: dict, node_id: str) -> dict | None:
    for node in graph.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


def node_neighbors(graph: dict, node_id: str) -> list[dict]:
    nodes = {n.get("id"): n for n in graph.get("nodes", [])}
    result = []
    for link in graph.get("links", []):
        if link.get("source") == node_id:
            other = nodes.get(link.get("target"))
        elif link.get("target") == node_id:
            other = nodes.get(link.get("source"))
        else:
            continue
        if other:
            result.append({"label": other.get("label"), "type": other.get("type"), "relation": link.get("label")})
    return result[:12]


def read_doc_excerpt(doc_ref: str) -> str:
    if not doc_ref:
        return ""
    clean = doc_ref.replace("\\", "/").lstrip("./")
    while clean.startswith("../"):
        clean = clean[3:]
    path = (ROOT / clean).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return ""
    if not path.exists() or path.suffix.lower() != ".md":
        return ""
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    return text[:5000]


def prompt_profile(node_type: str) -> str:
    if node_type == "project":
        return (
            "这是项目节点。输出更偏项目汇报和个人复盘：\n"
            "- 用 Markdown 小标题组织，建议包含 `### 项目定位`、`### 核心流程`、`### 关键结论`。\n"
            "- 说明项目目标、整体架构、关键流程、当前跑通结果。\n"
            "- 可以提到架构链路，但不要输出 Mermaid 代码块；前端会单独展示架构图。\n"
            "- 正文控制在 180 到 300 个中文字符。"
        )
    if node_type == "issue":
        return (
            "这是问题节点。输出更偏排障卡片：\n"
            "- 用 Markdown 小标题组织，建议包含 `### 现象`、`### 原因`、`### 解决`、`### 效果`。\n"
            "- 重点说明 bug/报错如何出现、根因是什么、如何修复、修复后如何验证。\n"
            "- 正文控制在 160 到 280 个中文字符。"
        )
    if node_type in {"concept", "library", "acceleration", "device", "service", "tool", "deployment"}:
        return (
            "这是技术节点。输出更偏原理和用法：\n"
            "- 用 Markdown 小标题组织，建议包含 `### 是什么`、`### 项目中怎么用`、`### 关键点`。\n"
            "- 说明概念/库/工具本身是什么，在本项目中的调用位置、上下游关系，可给一个短代码名或命令名示例。\n"
            "- 正文控制在 160 到 300 个中文字符。"
        )
    return (
        "这是普通知识节点。请用 Markdown 小标题组织，说明它是什么、为什么重要、和当前项目的关系。"
        "正文控制在 160 到 260 个中文字符。"
    )


def build_prompt(node: dict, neighbors: list[dict], excerpt: str) -> list[dict]:
    context = {
        "node": node,
        "neighbors": neighbors,
        "doc_excerpt": excerpt,
    }
    return [
        {
            "role": "system",
            "content": (
                "你是一个个人工程知识库助手。只根据给定上下文解释节点，语言简洁、准确、偏工程实践。"
                "不要编造没有依据的项目事实。输出 Markdown，但只使用小标题、加粗、行内代码、短列表。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请为知识图谱节点生成可直接展示在右侧卡片里的中文解释。\n"
                "通用要求：\n"
                "1. 必须结合上下文里的本地项目事实，不要泛泛科普。\n"
                "2. Markdown 会被前端渲染，请合理使用 `### 小标题`、`**重点**`、行内代码。\n"
                "3. 不要输出外链，不要输出长代码块，不要重复上下文 JSON。\n"
                f"4. 类型策略：\n{prompt_profile(str(node.get('type') or ''))}\n\n"
                f"上下文 JSON：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def note_complete(note: str) -> bool:
    text = note.strip()
    if len(text) < 80:
        return False
    return bool(re.search(r"[。！？.!?）)]$", text))


def call_deepseek(messages: list[dict]) -> str:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API key 未配置。请在 .env.local 中设置 DEEPSEEK_API_KEY。")
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 900,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_API_BASE,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:800]
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail}") from exc
    result = json.loads(body)
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"DeepSeek 返回格式异常: {body[:800]}") from exc


def save_note(node_id: str, note: str, source: str) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    record = {"ok": True, "id": node_id, "note": note, "source": source, "model": DEEPSEEK_MODEL if source.startswith("deepseek") else "", "updated_at": int(time.time())}
    cache_path(node_id).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def list_docs() -> list[dict]:
    docs: list[dict] = []
    for base in DOC_DIRS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            title = path.stem
            summary = ""
            node_type = TYPE_DIR.get(path.relative_to(ROOT).parts[0], "note")
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].splitlines():
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip('"\'') or title
                        elif line.startswith("summary:"):
                            summary = line.split(":", 1)[1].strip().strip('"\'')
                        elif line.startswith("type:"):
                            node_type = line.split(":", 1)[1].strip().strip('"\'') or node_type
            if not summary:
                for line in text.splitlines():
                    line = line.strip()
                    if line and not line.startswith(("---", "#", "title:", "type:", "summary:", "tags:", "links:")):
                        summary = line[:140]
                        break
            docs.append({
                "title": title,
                "type": node_type,
                "type_label": TYPE_LABEL.get(node_type, node_type),
                "summary": summary,
                "path": path.relative_to(ROOT).as_posix(),
                "url": "../" + path.relative_to(ROOT).as_posix(),
            })
    return docs


def create_node_doc(payload: dict) -> dict:
    title = str(payload.get("title") or "").strip()
    node_type = str(payload.get("type") or "concept").strip()
    summary = str(payload.get("summary") or "").strip()
    body = str(payload.get("body") or "").strip()
    tags_raw = str(payload.get("tags") or "").strip()
    links_raw = str(payload.get("links") or "").strip()
    if not title:
        raise ValueError("标题不能为空。")
    dirname = TYPE_DIR.get(node_type, "02_技术地图")
    base = ROOT / dirname
    base.mkdir(parents=True, exist_ok=True)
    filename = safe_id(title) + ".md"
    path = base / filename
    if path.exists():
        raise ValueError("同名节点文档已存在。")
    tags = [x.strip() for x in re.split(r"[,，]", tags_raw) if x.strip()]
    links = [x.strip() for x in re.split(r"[,，]", links_raw) if x.strip()]
    front = ["---", f"title: {title}", f"type: {node_type}", f"summary: {summary}", "tags:"]
    front += [f"  - {x}" for x in tags]
    front += ["links:"] + [f"  - {x}" for x in links] + ["---", ""]
    content = "\n".join(front) + f"# {title}\n\n" + (body or summary or "待补充。") + "\n"
    path.write_text(content, encoding="utf-8")
    rebuild()
    return {"ok": True, "title": title, "path": path.relative_to(ROOT).as_posix(), "type": node_type}


class KnowledgeHandler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/node-note":
            node_id = parse_qs(parsed.query).get("id", [""])[0]
            path = cache_path(node_id)
            if path.exists():
                self._send_json(200, json.loads(path.read_text(encoding="utf-8")))
            else:
                self._send_json(404, {"ok": False, "message": "这个节点还没有缓存解释。"})
            return
        if parsed.path == "/api/docs":
            self._send_json(200, {"ok": True, "docs": list_docs()})
            return
        if parsed.path == "/api/config":
            self._send_json(200, {"ok": True, "deepseek_configured": bool(DEEPSEEK_API_KEY), "model": DEEPSEEK_MODEL})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "message": "请求不是合法 JSON。"})
            return

        if parsed.path == "/api/node-note":
            node_id = str(payload.get("id") or "")
            note = str(payload.get("note") or "").strip()
            if not node_id or not note:
                self._send_json(400, {"ok": False, "message": "缺少节点 id 或解释内容。"})
                return
            self._send_json(200, save_note(node_id, note, payload.get("source") or "manual"))
            return

        if parsed.path == "/api/node-explain":
            node_id = str(payload.get("id") or "")
            force = bool(payload.get("force"))
            if not node_id:
                self._send_json(400, {"ok": False, "message": "缺少节点 id。"})
                return
            path = cache_path(node_id)
            if path.exists() and not force:
                record = json.loads(path.read_text(encoding="utf-8"))
                record["cached"] = True
                self._send_json(200, record)
                return
            try:
                graph = load_graph()
                node = find_node(graph, node_id)
                if not node:
                    self._send_json(404, {"ok": False, "message": "图谱中没有找到这个节点。"})
                    return
                messages = build_prompt(node, node_neighbors(graph, node_id), read_doc_excerpt(node.get("doc") or ""))
                note = call_deepseek(messages)
                if not note_complete(note):
                    retry_messages = messages + [
                        {"role": "assistant", "content": note or ""},
                        {"role": "user", "content": "上一次输出为空、太短或句子被截断。请重新输出完整的 Markdown 解释，必须以完整句子结束。"},
                    ]
                    note = call_deepseek(retry_messages)
                if not note_complete(note):
                    raise RuntimeError("DeepSeek 返回内容为空或不完整，未写入缓存。请稍后重试。")
                record = save_note(node_id, note, "deepseek")
                record["cached"] = False
                self._send_json(200, record)
            except Exception as exc:  # keep UI friendly; server is local and interactive
                self._send_json(500, {"ok": False, "message": str(exc)})
            return

        if parsed.path == "/api/node-create":
            try:
                self._send_json(200, create_node_doc(payload))
            except Exception as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
            return

        self._send_json(404, {"ok": False, "message": "未知接口。"})


def main() -> int:
    rebuild()
    os.chdir(ROOT)
    threading.Thread(target=watcher, daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), KnowledgeHandler) as httpd:
        url = f"http://127.0.0.1:{PORT}/graph/index.html"
        print(f"个人知识库已启动: {url}")
        print(f"DeepSeek: {'已配置' if DEEPSEEK_API_KEY else '未配置'}，model={DEEPSEEK_MODEL}")
        print("Markdown 修改后会自动重建 graph/graph.json；节点解释缓存在 graph/node_notes/。按 Ctrl+C 停止。")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n个人知识库服务已停止。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
