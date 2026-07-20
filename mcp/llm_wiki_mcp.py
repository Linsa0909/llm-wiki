#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP bridge for the local llm-wiki knowledge base.

This server intentionally uses only the Python standard library and speaks MCP
over stdio directly. It imports the existing llm-wiki kb_server module so the
MCP path reuses the same smart import, graph rebuild, search and doc APIs as the
web UI.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "2024-11-05"


def json_text(payload: Any) -> dict[str, Any]:
    # Keep the tool result shape conservative for MCP clients that validate the
    # base protocol strictly and do not accept newer structuredContent fields.
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ]
    }


def slug_filename(title: str) -> str:
    name = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fff]+", "-", title.strip())[:120].strip(".-")
    return (name or "codex-note") + ".md"


def normalize_csv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(str(x).strip() for x in value if str(x).strip())
    return str(value).strip()


class WikiRuntime:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.kb = self._load_kb()

    def _load_kb(self):
        script = self.root / "scripts" / "kb_server.py"
        if not script.exists():
            raise FileNotFoundError(f"kb_server.py not found: {script}")
        sys.path.insert(0, str(self.root / "scripts"))
        spec = importlib.util.spec_from_file_location("llm_wiki_kb_server", script)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import kb_server.py from {script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def graph_summary(self) -> dict[str, Any]:
        graph = self.kb.load_graph()
        links = graph.get("links", [])
        visible = [x for x in links if x.get("visible", True) is not False]
        return {
            "nodes": len(graph.get("nodes", [])),
            "links": len(links),
            "visible_links": len(visible),
            "hidden_links": len(links) - len(visible),
        }

    def health(self, _: dict[str, Any]) -> dict[str, Any]:
        docs = self.kb.list_docs()
        summary = self.graph_summary()
        return {
            "ok": True,
            "root": str(self.root),
            "docs": len(docs),
            "graph": summary,
            "deepseek_configured": bool(getattr(self.kb, "DEEPSEEK_API_KEY", "")),
            "model": getattr(self.kb, "DEEPSEEK_MODEL", ""),
        }

    def ingest_markdown(self, args: dict[str, Any]) -> dict[str, Any]:
        title = str(args.get("title") or "Codex 知识沉淀").strip()
        content = str(args.get("content") or "").strip()
        if not content:
            raise ValueError("content 不能为空")
        mode = str(args.get("mode") or "smart_import")
        payload = {
            "mode": mode,
            "title": title,
            "type": str(args.get("type") or args.get("node_type") or "concept"),
            "tags": normalize_csv(args.get("tags") or ["codex", "mcp"]),
            "links": normalize_csv(args.get("links")),
            "files": [{"name": str(args.get("filename") or slug_filename(title)), "content": content}],
        }
        result = self.kb.import_markdown(payload)
        result["graph"] = self.graph_summary()
        return result

    def ingest_project_notes(self, args: dict[str, Any]) -> dict[str, Any]:
        project = str(args.get("project") or args.get("title") or "Codex 项目沉淀").strip()
        files = args.get("files")
        prepared_files: list[dict[str, str]] = []
        if isinstance(files, list):
            for idx, item in enumerate(files, 1):
                if not isinstance(item, dict):
                    continue
                content = str(item.get("content") or "").strip()
                if content:
                    name = str(item.get("name") or f"{project}-{idx}.md")
                    prepared_files.append({"name": name if name.lower().endswith(".md") else name + ".md", "content": content})
        content = str(args.get("content") or "").strip()
        if content:
            prepared_files.insert(0, {"name": slug_filename(project), "content": content})
        if not prepared_files:
            raise ValueError("content 或 files 至少提供一个")
        payload = {
            "mode": "project_package",
            "title": project,
            "type": "project",
            "tags": normalize_csv(args.get("tags") or ["codex", "mcp", "项目沉淀"]),
            "links": normalize_csv(args.get("links")),
            "files": prepared_files,
        }
        result = self.kb.import_markdown(payload)
        result["graph"] = self.graph_summary()
        return result

    def search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "").strip().lower()
        node_type = str(args.get("type") or "").strip()
        limit = int(args.get("limit") or 12)
        if not query:
            raise ValueError("query 不能为空")
        docs = []
        for doc in self.kb.list_docs():
            hay = " ".join(str(doc.get(k, "")) for k in ("title", "summary", "path", "type")).lower()
            if node_type and doc.get("type") != node_type:
                continue
            if query in hay:
                docs.append(doc)
        graph = self.kb.load_graph()
        nodes = []
        for node in graph.get("nodes", []):
            hay = " ".join([
                str(node.get("label", "")),
                str(node.get("summary", "")),
                str(node.get("type", "")),
                " ".join(str(x) for x in node.get("tags", [])),
            ]).lower()
            if node_type and node.get("type") != node_type:
                continue
            if query in hay:
                nodes.append(node)
        return {"ok": True, "query": query, "docs": docs[:limit], "nodes": nodes[:limit]}

    def rebuild_graph(self, _: dict[str, Any]) -> dict[str, Any]:
        self.kb.rebuild()
        return {"ok": True, "graph": self.graph_summary()}

    def get_node(self, args: dict[str, Any]) -> dict[str, Any]:
        node_id = str(args.get("id") or "").strip()
        if not node_id:
            raise ValueError("id 不能为空")
        graph = self.kb.load_graph()
        node = self.kb.find_node(graph, node_id)
        if not node:
            raise KeyError(f"node not found: {node_id}")
        neighbors = self.kb.node_neighbors(graph, node_id) if hasattr(self.kb, "node_neighbors") else []
        doc = None
        if node.get("doc"):
            try:
                doc = self.kb.read_doc_payload(node["doc"])
            except Exception as exc:
                doc = {"ok": False, "message": str(exc)}
        return {"ok": True, "node": node, "neighbors": neighbors, "doc": doc}

    def append_doc(self, args: dict[str, Any]) -> dict[str, Any]:
        doc_ref = str(args.get("path") or args.get("doc") or "").strip()
        content = str(args.get("content") or "").strip()
        heading = str(args.get("heading") or "Codex 追加沉淀").strip()
        if not doc_ref:
            raise ValueError("path/doc 不能为空")
        if not content:
            raise ValueError("content 不能为空")
        path = self.kb.resolve_doc_ref(doc_ref)
        if not path:
            raise FileNotFoundError(f"doc not found: {doc_ref}")
        current = path.read_text(encoding="utf-8-sig", errors="ignore")
        block = f"\n\n## {heading}\n\n{content.rstrip()}\n"
        path.write_text(current.rstrip() + block, encoding="utf-8")
        self.kb.rebuild()
        return {"ok": True, "path": path.relative_to(self.root).as_posix(), "graph": self.graph_summary()}


TOOLS: dict[str, dict[str, Any]] = {
    "health": {
        "description": "检查 llm-wiki 知识库路径、文档数量、图谱状态和 DeepSeek 配置。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "ingest_markdown": {
        "description": "把 Codex 整理好的一篇 Markdown 送进 llm-wiki，走智能导入并重建图谱。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "enum": ["smart_import", "merge_by_title", "split_headings", "merge_all"]},
                "type": {"type": "string"},
                "tags": {"type": "string", "description": "逗号分隔标签，例如 codex,mcp,项目沉淀"},
                "links": {"type": "string", "description": "逗号分隔的已有节点标题，用于建立候选关系"},
                "filename": {"type": "string"},
            },
            "required": ["title", "content"],
            "additionalProperties": False,
        },
    },
    "ingest_project_notes": {
        "description": "沉淀一次项目/排障/部署过程，自动按项目资料包拆成项目、技术、问题、部署、命令节点。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "content": {"type": "string"},
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "content": {"type": "string"}},
                        "required": ["content"],
                    },
                },
                "tags": {"type": "string", "description": "逗号分隔标签，例如 codex,mcp,项目沉淀"},
                "links": {"type": "string", "description": "逗号分隔的已有节点标题，用于建立候选关系"},
            },
            "required": ["project"],
            "additionalProperties": False,
        },
    },
    "search": {
        "description": "搜索 llm-wiki 中已有文档和图谱节点，写入前可用于避免重复节点。",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "type": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    "rebuild_graph": {
        "description": "手动重建 graph/graph.json 并返回节点/关系数量。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "get_node": {
        "description": "读取某个图谱节点的详情、邻居节点和对应 Markdown 文档。",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    "append_doc": {
        "description": "把 Codex 整理好的内容直接追加到已有 Markdown 文档，并重建图谱。",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "doc": {"type": "string"}, "heading": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
}


class MCPServer:
    def __init__(self, wiki: WikiRuntime) -> None:
        self.wiki = wiki
        self.handlers = {
            "health": self.wiki.health,
            "ingest_markdown": self.wiki.ingest_markdown,
            "ingest_project_notes": self.wiki.ingest_project_notes,
            "search": self.wiki.search,
            "rebuild_graph": self.wiki.rebuild_graph,
            "get_node": self.wiki.get_node,
            "append_doc": self.wiki.append_doc,
        }

    def read_message(self) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            line = line.decode("ascii", errors="ignore").strip()
            if not line:
                break
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.lower()] = v.strip()
        length = int(headers.get("content-length", "0"))
        if length <= 0:
            return None
        raw = sys.stdin.buffer.read(length)
        return json.loads(raw.decode("utf-8"))

    def send(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        sys.stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data)
        sys.stdout.buffer.flush()

    def respond(self, msg_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": msg_id}
        if error is not None:
            payload["error"] = error
        else:
            payload["result"] = result if result is not None else {}
        self.send(payload)

    def handle(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        msg_id = msg.get("id")
        if method == "initialize":
            self.respond(msg_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "llm-wiki", "version": "0.1.0"},
            })
            return
        if method == "notifications/initialized":
            return
        if method == "tools/list":
            tools = []
            for name, spec in TOOLS.items():
                tools.append({"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]})
            self.respond(msg_id, {"tools": tools})
            return
        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            if name not in self.handlers:
                self.respond(msg_id, error={"code": -32602, "message": f"unknown tool: {name}"})
                return
            try:
                result = self.handlers[name](args)
                self.respond(msg_id, json_text(result))
            except Exception as exc:
                self.respond(msg_id, {
                    "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                    "isError": True,
                })
            return
        if msg_id is not None:
            self.respond(msg_id, error={"code": -32601, "message": f"method not found: {method}"})

    def serve(self) -> None:
        while True:
            msg = self.read_message()
            if msg is None:
                break
            try:
                self.handle(msg)
            except Exception as exc:
                if msg.get("id") is not None:
                    self.respond(msg.get("id"), error={"code": -32603, "message": str(exc), "data": traceback.format_exc()})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.environ.get("LLM_WIKI_ROOT", str(Path(__file__).resolve().parents[1])))
    args = parser.parse_args()
    server = MCPServer(WikiRuntime(Path(args.root)))
    server.serve()


if __name__ == "__main__":
    main()

