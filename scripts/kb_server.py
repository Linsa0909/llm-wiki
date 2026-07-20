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
import shutil
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("KB_PORT", "8765"))
REBUILD = ROOT / "scripts" / "rebuild_graph.py"
GRAPH = ROOT / "graph" / "graph.json"
LAYOUT = ROOT / "graph" / "layout.json"
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


def read_layout_payload() -> dict:
    if not LAYOUT.exists():
        return {"ok": True, "positions": {}, "viewport": {}, "updated_at": 0}
    try:
        data = json.loads(LAYOUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": True, "positions": {}, "viewport": {}, "updated_at": 0, "warning": "layout.json is invalid"}
    if not isinstance(data, dict):
        data = {}
    positions = data.get("positions") if isinstance(data.get("positions"), dict) else {}
    viewport = data.get("viewport") if isinstance(data.get("viewport"), dict) else {}
    return {"ok": True, "positions": positions, "viewport": viewport, "updated_at": data.get("updated_at", 0)}


def save_layout_payload(payload: dict) -> dict:
    positions = payload.get("positions") if isinstance(payload.get("positions"), dict) else {}
    viewport = payload.get("viewport") if isinstance(payload.get("viewport"), dict) else {}
    clean_positions: dict[str, dict[str, float]] = {}
    for node_id, pos in positions.items():
        if not isinstance(pos, dict):
            continue
        try:
            x = float(pos.get("x"))
            y = float(pos.get("y"))
        except (TypeError, ValueError):
            continue
        clean_positions[str(node_id)] = {"x": round(x, 3), "y": round(y, 3)}

    clean_viewport: dict[str, float] = {}
    for key in ("scale", "ox", "oy"):
        if key not in viewport:
            continue
        try:
            clean_viewport[key] = round(float(viewport[key]), 4)
        except (TypeError, ValueError):
            pass

    LAYOUT.parent.mkdir(parents=True, exist_ok=True)
    record = {"positions": clean_positions, "viewport": clean_viewport, "updated_at": time.time()}
    tmp = LAYOUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(LAYOUT)
    return {"ok": True, "saved": len(clean_positions), "updated_at": record["updated_at"]}


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


def clean_doc_ref(doc_ref: str) -> str:
    clean = unquote(str(doc_ref or "")).replace("\\", "/").lstrip("./")
    while clean.startswith("../"):
        clean = clean[3:]
    return clean


def resolve_doc_ref(doc_ref: str) -> Path | None:
    clean = clean_doc_ref(doc_ref)
    if not clean:
        return None
    path = (ROOT / clean).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return None
    if not path.exists() or path.suffix.lower() != ".md":
        return None
    return path


def read_text_lossy(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            return text.replace("\r\n", "\n"), False
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n"), True


def read_doc_excerpt(doc_ref: str, limit: int = 5000) -> str:
    path = resolve_doc_ref(doc_ref)
    if not path:
        return ""
    text, _warning = read_text_lossy(path)
    return text[:limit]


def read_node_excerpts(node: dict, limit: int = 9000) -> dict:
    refs: list[str] = []
    for key in ("doc",):
        if node.get(key):
            refs.append(str(node.get(key)))
    for key in ("docs", "sources"):
        value = node.get(key)
        if isinstance(value, list):
            refs.extend(str(x) for x in value if x)
    seen: set[str] = set()
    parts: list[dict] = []
    used = 0
    for ref in refs:
        path = resolve_doc_ref(ref)
        if not path:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        text, warning = read_text_lossy(path)
        room = max(600, limit - used)
        excerpt = text[:room]
        used += len(excerpt)
        parts.append({"path": rel, "encoding_warning": warning or "?" in text, "excerpt": excerpt})
        if used >= limit:
            break
    return {"documents": parts, "combined_excerpt": "\n\n".join(f"# 来源：{x['path']}\n{x['excerpt']}" for x in parts)}


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


def build_prompt(node: dict, neighbors: list[dict], doc_context: dict) -> list[dict]:
    context = {
        "node": node,
        "neighbors": neighbors,
        "doc_sources": doc_context.get("documents", []),
        "doc_excerpt": doc_context.get("combined_excerpt", ""),
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
    created_at = time.strftime("%Y%m%d-%H%M%S")
    front = ["---", f"title: {title}", f"type: {node_type}", f"summary: {summary}", f"created_at: {created_at}", "tags:"]
    front += [f"  - {x}" for x in tags]
    front += ["links:"] + [f"  - {x}" for x in links] + ["---", ""]
    content = "\n".join(front) + f"# {title}\n\n" + (body or summary or "待补充。") + "\n"
    path.write_text(content, encoding="utf-8")
    rebuild()
    return {"ok": True, "title": title, "path": path.relative_to(ROOT).as_posix(), "type": node_type}


def parse_frontmatter_text(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5:]
    data: dict[str, object] = {}
    current_key = ""
    for line in raw.splitlines():
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(line[4:].strip().strip('"\''))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            data[key] = [x.strip().strip('"\'') for x in value[1:-1].split(",") if x.strip()]
        else:
            data[key] = value.strip('"\'')
    return data, body


def title_from_markdown(name: str, text: str) -> str:
    fm, body = parse_frontmatter_text(text)
    if fm.get("title"):
        return str(fm["title"]).strip()
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return Path(name).stem


def summary_from_markdown(text: str) -> str:
    _fm, body = parse_frontmatter_text(text)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "|", "-", ">", "---")):
            continue
        return line[:160]
    return ""


def split_markdown_h2(text: str) -> list[tuple[str, str]]:
    _fm, body = parse_frontmatter_text(text)
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", body, flags=re.M))
    if not matches:
        return []
    sections: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        title = match.group(1).strip()
        sections.append((title, body[start:end].strip()))
    return sections


def write_frontmatter(title: str, node_type: str, summary: str, tags: list[str], links: list[str], sources: list[str]) -> str:
    lines = ["---", f"title: {title}", f"type: {node_type}", f"summary: {summary}", "tags:"]
    lines += [f"  - {x}" for x in tags]
    lines += ["links:"] + [f"  - {x}" for x in links]
    lines += ["sources:"] + [f"  - {x}" for x in sources]
    lines += ["---", ""]
    return "\n".join(lines)


def merge_sources_from_text(text: str) -> list[str]:
    fm, _body = parse_frontmatter_text(text)
    value = fm.get("sources")
    return [str(x) for x in value] if isinstance(value, list) else []


def append_or_create_import_doc(title: str, node_type: str, summary: str, tags: list[str], links: list[str], source_blocks: list[tuple[str, str]], raw_sources: list[str]) -> tuple[Path, bool]:
    dirname = TYPE_DIR.get(node_type, "02_技术地图")
    base = ROOT / dirname
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{safe_id(title)}.md"
    source_paths = list(dict.fromkeys(raw_sources))
    if path.exists():
        old = path.read_text(encoding="utf-8-sig", errors="ignore").replace("\r\n", "\n")
        old_sources = merge_sources_from_text(old)
        all_sources = list(dict.fromkeys(old_sources + source_paths))
        existing_body = parse_frontmatter_text(old)[1].strip()
        new_blocks = []
        for name, body in source_blocks:
            if name not in old_sources:
                new_blocks.append(f"## 导入来源：{name}\n\n{body.strip()}")
        merged_body = existing_body + ("\n\n" + "\n\n".join(new_blocks) if new_blocks else "")
        new_summary = summary or summary_from_markdown(merged_body)
        path.write_text(write_frontmatter(title, node_type, new_summary, tags, links, all_sources) + f"# {title}\n\n" + merged_body + "\n", encoding="utf-8")
        return path, True
    body = "\n\n".join(f"## 导入来源：{name}\n\n{content.strip()}" for name, content in source_blocks)
    path.write_text(write_frontmatter(title, node_type, summary, tags, links, source_paths) + f"# {title}\n\n{body}\n", encoding="utf-8")
    return path, False


def code_blocks_from_markdown(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"```(?:\w+)?\n([\s\S]*?)```", text)]


def section_texts(text: str) -> list[tuple[str, str]]:
    _fm, body = parse_frontmatter_text(text)
    headings = list(re.finditer(r"^(#{1,3})\s+(.+?)\s*$", body, flags=re.M))
    if not headings:
        return [(title_from_markdown("document.md", text), body.strip())]
    result: list[tuple[str, str]] = []
    for idx, match in enumerate(headings):
        start = match.start()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(body)
        result.append((match.group(2).strip(), body[start:end].strip()))
    return result


PROJECT_TOPIC_RULES = [
    ("Git", "tool", ["git ", "github", "gitlab", "commit", "branch", "pull request", "merge request"], ["git", "version-control"]),
    ("Docker", "tool", ["docker ", "dockerfile", "container", "image", "docker compose"], ["docker", "container"]),
    ("Docker buildx", "tool", ["buildx", "multi-arch", "multiarch", "arm64", "platform"], ["docker", "buildx", "multi-arch"]),
    ("Kubernetes", "tool", ["kubectl", "kubernetes", "k8s", "helm"], ["kubernetes", "deploy"]),
    ("CI/CD", "tool", ["github actions", "gitlab-ci", "jenkins", "pipeline", "ci/cd"], ["ci-cd", "automation"]),
    ("Linux Shell", "tool", ["bash", "shell", "systemctl", "ssh ", "scp ", "chmod", "journalctl"], ["linux", "shell"]),
    ("Nginx", "service", ["nginx"], ["nginx", "proxy"]),
    ("Redis", "service", ["redis"], ["redis", "cache"]),
    ("MySQL", "service", ["mysql"], ["mysql", "database"]),
    ("PostgreSQL", "service", ["postgresql", "postgres"], ["postgresql", "database"]),
    ("Python", "tool", ["python", "pip ", "conda", "venv"], ["python"]),
    ("Node.js", "tool", ["node ", "npm ", "pnpm", "yarn"], ["nodejs"]),
    ("FFmpeg", "tool", ["ffmpeg", "libavcodec", "libavformat"], ["ffmpeg", "video"]),
    ("ZLMediaKit", "service", ["zlmediakit", "zlm"], ["streaming", "zlm"]),
    ("RK3588", "device", ["rk3588", "arm64", "rockchip"], ["rk3588", "arm64"]),
]


def project_title_from_import(payload: dict, prepared: list[dict]) -> str:
    title = str(payload.get("title") or "").strip()
    if title:
        return title
    for item in prepared:
        if item["name"].lower() in {"readme.md", "README.md".lower()}:
            return str(item["title"] or Path(item["name"]).stem).strip()
    return str(prepared[0]["title"] or "\u9879\u76ee\u5bfc\u5165").strip()


def command_lines_from_blocks(blocks: list[str]) -> list[str]:
    command_keywords = ("git ", "docker ", "kubectl", "helm ", "ssh ", "scp ", "curl ", "wget ", "make", "cmake", "npm ", "pnpm ", "yarn ", "pip ", "python ", "ffmpeg", "systemctl", "journalctl", "tar ", "rsync ")
    lines: list[str] = []
    for block in blocks:
        for raw in block.splitlines():
            line = raw.strip()
            if line.startswith("$ "):
                line = line[2:].strip()
            if not line or line.startswith("#"):
                continue
            lower = line.lower()
            if lower.startswith(command_keywords) or any(k in lower for k in (" docker ", " git ", " kubectl ")):
                lines.append(line)
    return list(dict.fromkeys(lines))[:80]


def make_candidate(source: str, target: str, label: str, reason: str, status: str = "suggested") -> dict:
    return {"source": source, "target": target, "label": label, "reason": reason, "status": status}


def import_project_package(payload: dict, prepared: list[dict], raw_dir: Path, tags: list[str], links: list[str]) -> dict:
    project_title = project_title_from_import(payload, prepared)
    raws = [str(x["raw"]) for x in prepared]
    combined = "\n\n".join(f"# \u6765\u6e90\uff1a{x['name']}\n{x['content']}" for x in prepared)
    combined_lower = combined.lower()
    base_tags = list(dict.fromkeys(tags + ["\u9879\u76ee\u5bfc\u5165"]))
    created: list[dict] = []
    merged: list[dict] = []
    candidates: list[dict] = []
    generated_titles: list[str] = []

    def add_doc(title: str, node_type: str, summary: str, body: str, extra_tags: list[str], extra_links: list[str]) -> str:
        path, was_merge = append_or_create_import_doc(
            title,
            node_type,
            summary,
            list(dict.fromkeys(base_tags + extra_tags)),
            list(dict.fromkeys(links + extra_links)),
            [("\u9879\u76ee\u8d44\u6599\u5305", body)],
            raws,
        )
        record = {"title": title, "path": path.relative_to(ROOT).as_posix(), "sources": raws}
        (merged if was_merge else created).append(record)
        generated_titles.append(title)
        return title

    topic_titles: list[str] = []
    for topic, node_type, needles, topic_tags in PROJECT_TOPIC_RULES:
        if any(needle in combined_lower for needle in needles):
            evidence = []
            for heading, body in section_texts(combined):
                lower = body.lower()
                if any(needle in lower or needle in heading.lower() for needle in needles):
                    evidence.append(f"### {heading}\n{body[:900]}")
                if len(evidence) >= 3:
                    break
            body = "\n\n".join(evidence) or combined[:1200]
            title = add_doc(
                topic,
                node_type,
                f"\u4ece\u9879\u76ee\u8d44\u6599\u5305\u4e2d\u81ea\u52a8\u8bc6\u522b\u7684 {topic} \u76f8\u5173\u6280\u672f\u8282\u70b9\u3002",
                "## \u81ea\u52a8\u8bc6\u522b\u4f9d\u636e\n\n" + body,
                topic_tags,
                [project_title],
            )
            topic_titles.append(title)
            candidates.append(make_candidate(project_title, title, "\u4f7f\u7528", f"\u9879\u76ee\u6587\u6863\u4e2d\u51fa\u73b0 {topic} \u76f8\u5173\u5173\u952e\u8bcd\u6216\u547d\u4ee4\u3002"))

    blocks = []
    for item in prepared:
        blocks.extend(code_blocks_from_markdown(item["content"]))
    commands = command_lines_from_blocks(blocks)
    command_title = ""
    if commands:
        command_body = "## \u547d\u4ee4\u6e05\u5355\n\n" + "\n".join(f"- `{line}`" for line in commands)
        command_title = add_doc(
            f"{project_title} \u547d\u4ee4\u6e05\u5355",
            "tool",
            "\u4ece\u9879\u76ee Markdown \u4ee3\u7801\u5757\u4e2d\u81ea\u52a8\u63d0\u53d6\u7684\u5e38\u7528\u547d\u4ee4\u3002",
            command_body,
            ["commands"],
            [project_title] + topic_titles,
        )
        candidates.append(make_candidate(project_title, command_title, "\u6c89\u6dc0", "\u9879\u76ee\u6587\u6863\u4e2d\u5305\u542b\u53ef\u6267\u884c\u547d\u4ee4\u6216\u811a\u672c\u7247\u6bb5\u3002"))

    deploy_needles = ["deploy", "deployment", "\u90e8\u7f72", "\u5b89\u88c5", "\u542f\u52a8", "docker run", "docker compose", "kubectl", "systemctl", "arm64", "rk3588"]
    deploy_sections = []
    for heading, body in section_texts(combined):
        lower = (heading + "\n" + body).lower()
        if any(x in lower for x in deploy_needles):
            deploy_sections.append(f"### {heading}\n{body[:1200]}")
    deploy_title = ""
    if deploy_sections:
        deploy_title = add_doc(
            f"{project_title} \u90e8\u7f72\u6d41\u7a0b",
            "deployment",
            "\u4ece\u9879\u76ee\u8d44\u6599\u5305\u4e2d\u81ea\u52a8\u62bd\u53d6\u7684\u90e8\u7f72\u3001\u542f\u52a8\u548c\u9a8c\u8bc1\u4fe1\u606f\u3002",
            "## \u90e8\u7f72\u76f8\u5173\u5185\u5bb9\n\n" + "\n\n".join(deploy_sections[:6]),
            ["deployment"],
            [project_title] + ([command_title] if command_title else []),
        )
        candidates.append(make_candidate(project_title, deploy_title, "\u90e8\u7f72", "\u6587\u6863\u4e2d\u51fa\u73b0\u90e8\u7f72\u3001\u542f\u52a8\u3001\u5bb9\u5668\u6216\u8bbe\u5907\u76f8\u5173\u5185\u5bb9\u3002"))

    issue_needles = ["error", "failed", "failure", "exception", "fatal", "undefined", "not found", "no such", "\u62a5\u9519", "\u9519\u8bef", "\u5931\u8d25", "\u95ee\u9898", "\u89e3\u51b3"]
    issue_titles: list[str] = []
    for heading, body in section_texts(combined):
        lower = (heading + "\n" + body).lower()
        if any(x in lower for x in issue_needles):
            title = f"{project_title} \u95ee\u9898\uff1a{heading[:42]}"
            issue_titles.append(add_doc(
                title,
                "issue",
                "\u4ece\u9879\u76ee\u8d44\u6599\u5305\u4e2d\u81ea\u52a8\u8bc6\u522b\u7684\u95ee\u9898\u3001\u62a5\u9519\u6216\u6392\u969c\u8bb0\u5f55\u3002",
                "## \u95ee\u9898\u7247\u6bb5\n\n" + body[:1600],
                ["issue"],
                [project_title],
            ))
        if len(issue_titles) >= 5:
            break
    for title in issue_titles:
        candidates.append(make_candidate(project_title, title, "\u6392\u969c", "\u6587\u6863\u4e2d\u51fa\u73b0\u95ee\u9898\u3001\u9519\u8bef\u3001\u5931\u8d25\u6216\u89e3\u51b3\u7b49\u6392\u969c\u4fe1\u53f7\u3002"))

    relation_lines = "\n".join(f"- [{x['status']}] {x['source']} --{x['label']}--> {x['target']}：{x['reason']}" for x in candidates) or "- \u6682\u65e0\u5019\u9009\u5173\u7cfb\u3002"
    source_lines = "\n".join(f"- {x['name']} -> `{x['raw']}`" for x in prepared)
    node_lines = "\n".join(f"- [[{title}]]" for title in generated_titles if title != project_title)
    overview = "\n\n".join(f"## \u6765\u6e90\uff1a{x['name']}\n\n{parse_frontmatter_text(x['content'])[1].strip()[:1200]}" for x in prepared)
    project_body = (
        "## \u5bfc\u5165\u6765\u6e90\n\n" + source_lines +
        "\n\n## \u81ea\u52a8\u62c6\u5206\u8282\u70b9\n\n" + (node_lines or "- \u6682\u672a\u62c6\u51fa\u5b50\u8282\u70b9\u3002") +
        "\n\n## \u5019\u9009\u5173\u7cfb\uff08\u5f85\u4eba\u5de5\u5ba1\u67e5\uff09\n\n" + relation_lines +
        "\n\n## \u539f\u59cb\u6750\u6599\u6458\u8981\n\n" + overview
    )
    project_links = generated_titles + links
    add_doc(
        project_title,
        "project",
        "\u7531\u9879\u76ee\u8d44\u6599\u5305\u81ea\u52a8\u751f\u6210\u7684\u9879\u76ee\u590d\u76d8\u5165\u53e3\uff0c\u5305\u542b\u62c6\u5206\u8282\u70b9\u548c\u5019\u9009\u5173\u7cfb\u3002",
        project_body,
        ["project"],
        project_links,
    )

    rebuild()
    return {
        "ok": True,
        "mode": "project_package",
        "raw_dir": raw_dir.relative_to(ROOT).as_posix(),
        "project": project_title,
        "created": created,
        "merged": merged,
        "candidates": candidates,
        "count": len(created) + len(merged),
    }


HUB_RULES = [
    ("\u5bb9\u5668\u955c\u50cf\u6784\u5efa", "concept", ["docker", "buildx", "image", "container", "arm64", "platform"], ["docker", "buildx", "image", "arm64"]),
    ("Git \u5de5\u4f5c\u6d41", "concept", ["git", "github", "gitlab", "commit", "branch", "merge", "pull request"], ["git", "workflow"]),
    ("\u90e8\u7f72\u4e0e\u8fd0\u7ef4", "concept", ["deploy", "\u90e8\u7f72", "systemctl", "ssh", "scp", "docker run", "kubectl", "\u542f\u52a8"], ["deployment", "ops"]),
    ("Linux \u7cfb\u7edf\u4e0e\u8bbe\u5907", "concept", ["linux", "udev", "systemd", "/dev/", "v4l2", "\u8bbe\u5907\u6587\u4ef6"], ["linux", "device"]),
    ("\u89c6\u9891\u91c7\u96c6\u4e0e\u63a8\u6d41", "concept", ["ffmpeg", "v4l2", "rtmp", "h264", "zlmediakit", "zlm", "\u63a8\u6d41"], ["video", "streaming"]),
]


def load_existing_nodes() -> list[dict]:
    try:
        graph = load_graph()
        return list(graph.get("nodes", []))
    except Exception:
        return []


def text_tokens(text: str) -> set[str]:
    lower = text.lower()
    words = set(re.findall(r"[a-z0-9_+.-]{2,}", lower))
    for word in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        words.add(word)
    return words


def infer_import_type(title: str, content: str, commands: list[str]) -> str:
    lower = (title + "\n" + content).lower()
    issue_words = ["error", "failed", "exception", "fatal", "not found", "no such", "\u62a5\u9519", "\u9519\u8bef", "\u5931\u8d25", "\u6392\u969c", "\u89e3\u51b3"]
    deploy_words = ["deploy", "deployment", "\u90e8\u7f72", "\u5b89\u88c5", "\u542f\u52a8", "docker run", "docker compose", "kubectl", "systemctl"]
    project_words = ["readme", "\u9879\u76ee", "overview", "\u67b6\u6784", "architecture"]
    if any(x in lower for x in issue_words):
        return "issue"
    if any(x in lower for x in deploy_words):
        return "deployment"
    if len(commands) >= 3 or any(x in lower for x in ["commands", "\u547d\u4ee4", "cheatsheet", "snippet"]):
        return "tool"
    if any(x in lower for x in project_words):
        return "project"
    return "concept"


def matched_topics(content: str) -> list[tuple[str, str, list[str]]]:
    lower = content.lower()
    result: list[tuple[str, str, list[str]]] = []
    for topic, node_type, needles, tags in PROJECT_TOPIC_RULES:
        if any(needle in lower for needle in needles):
            result.append((topic, node_type, tags))
    return result


def matched_hubs(content: str) -> list[tuple[str, str, list[str]]]:
    lower = content.lower()
    result: list[tuple[str, str, list[str]]] = []
    for hub, node_type, needles, tags in HUB_RULES:
        hits = sum(1 for needle in needles if needle in lower)
        if hits >= 2:
            result.append((hub, node_type, tags))
    return result


def candidate_existing_links(title: str, content: str, existing_nodes: list[dict], limit: int = 8) -> list[dict]:
    source_tokens = text_tokens(title + "\n" + content)
    scored: list[tuple[float, dict, str]] = []
    lower = (title + "\n" + content).lower()
    for node in existing_nodes:
        label = str(node.get("label") or "")
        if not label or label == title:
            continue
        hay = " ".join([label, str(node.get("summary") or ""), " ".join(node.get("tags") or [])])
        node_tokens = text_tokens(hay)
        overlap = len(source_tokens & node_tokens)
        score = overlap
        reason = "\u5173\u952e\u8bcd\u91cd\u5408"
        if label.lower() in lower or title.lower() in label.lower():
            score += 6
            reason = "\u6807\u9898\u6216\u6b63\u6587\u76f4\u63a5\u547d\u4e2d"
        if node.get("type") in {"project", "deployment"} and any(x in lower for x in ["deploy", "\u90e8\u7f72", "docker", "arm64"]):
            score += 1.5
        if score >= 2:
            scored.append((score, node, reason))
    scored.sort(key=lambda x: x[0], reverse=True)
    links = []
    for score, node, reason in scored[:limit]:
        links.append(make_candidate(title, str(node.get("label")), "\u76f8\u5173", f"{reason}\uff0c\u5339\u914d\u5206 {score:.1f}\u3002"))
    return links


def issue_sections_from_item(item: dict) -> list[tuple[str, str]]:
    issue_words = ["error", "failed", "exception", "fatal", "not found", "no such", "\u62a5\u9519", "\u9519\u8bef", "\u5931\u8d25", "\u95ee\u9898", "\u89e3\u51b3"]
    sections = []
    for heading, body in section_texts(item["content"]):
        lower = (heading + "\n" + body).lower()
        if any(x in lower for x in issue_words):
            sections.append((heading, body))
    return sections


def import_smart_knowledge(payload: dict, prepared: list[dict], raw_dir: Path, tags: list[str], links: list[str]) -> dict:
    raws = [str(x["raw"]) for x in prepared]
    existing_nodes = load_existing_nodes()
    created: list[dict] = []
    merged: list[dict] = []
    candidates: list[dict] = []
    hubs: list[dict] = []

    def add_doc(title: str, node_type: str, summary: str, body: str, extra_tags: list[str], extra_links: list[str]) -> str:
        path, was_merge = append_or_create_import_doc(
            title,
            node_type,
            summary,
            list(dict.fromkeys(tags + ["\u667a\u80fd\u5bfc\u5165"] + extra_tags)),
            list(dict.fromkeys(links + extra_links)),
            [("\u667a\u80fd\u5bfc\u5165", body)],
            raws,
        )
        record = {"title": title, "type": node_type, "path": path.relative_to(ROOT).as_posix(), "sources": raws}
        (merged if was_merge else created).append(record)
        return title

    for item in prepared:
        content = item["content"]
        body = parse_frontmatter_text(content)[1].strip()
        commands = command_lines_from_blocks(code_blocks_from_markdown(content))
        inferred_type = infer_import_type(str(item["title"]), content, commands)
        title = str(item["title"]).strip()
        source_name = item["name"]
        summary = item["summary"] or f"\u7531 {source_name} \u667a\u80fd\u5bfc\u5165\u7684\u77e5\u8bc6\u8282\u70b9\u3002"

        topic_matches = matched_topics(content)
        hub_matches = matched_hubs(content)
        candidate_links = candidate_existing_links(title, content, existing_nodes)
        topic_titles = [x[0] for x in topic_matches]
        hub_titles = [x[0] for x in hub_matches]

        if inferred_type == "issue":
            sections = issue_sections_from_item(item) or [(title, body)]
            for heading, section_body in sections[:6]:
                issue_title = title if len(sections) == 1 else f"{title} \u95ee\u9898\uff1a{heading[:42]}"
                add_doc(
                    issue_title,
                    "issue",
                    "\u667a\u80fd\u5bfc\u5165\u8bc6\u522b\u7684\u95ee\u9898\u3001\u62a5\u9519\u6216\u6392\u969c\u8282\u70b9\u3002",
                    "## \u95ee\u9898\u6765\u6e90\n\n" + section_body,
                    ["issue"],
                    topic_titles + hub_titles,
                )
                for link in candidate_links:
                    candidates.append(make_candidate(issue_title, link["target"], link["label"], link["reason"]))
        else:
            add_doc(
                title,
                inferred_type,
                summary,
                "## \u667a\u80fd\u5bfc\u5165\u8bf4\u660e\n\n"
                f"- \u5224\u65ad\u7c7b\u578b\uff1a`{inferred_type}`\n"
                f"- \u6765\u6e90\u6587\u4ef6\uff1a`{source_name}`\n\n"
                "## \u539f\u6587\u5185\u5bb9\n\n" + body,
                [inferred_type],
                topic_titles + hub_titles,
            )
            for link in candidate_links:
                candidates.append(make_candidate(title, link["target"], link["label"], link["reason"]))

        for topic, topic_type, topic_tags in topic_matches:
            topic_title = add_doc(
                topic,
                topic_type,
                f"\u667a\u80fd\u5bfc\u5165\u4ece {title} \u4e2d\u8bc6\u522b\u5230\u7684 {topic} \u76f8\u5173\u77e5\u8bc6\u70b9\u3002",
                f"## \u8bc6\u522b\u6765\u6e90\n\n\u6765\u6e90\u6587\u6863\uff1a[[{title}]]\n\n" + body[:1200],
                topic_tags,
                [title] + hub_titles,
            )
            candidates.append(make_candidate(title, topic_title, "\u63d0\u5230", f"\u6587\u6863\u4e2d\u547d\u4e2d {topic} \u76f8\u5173\u89c4\u5219\u5173\u952e\u8bcd\u3002"))

        for hub, hub_type, hub_tags in hub_matches:
            hub_title = add_doc(
                hub,
                hub_type,
                "\u667a\u80fd\u5bfc\u5165\u5efa\u8bae\u7684\u4e3b\u9898 Hub\uff0c\u7528\u4e8e\u805a\u5408\u76f8\u5173\u6280\u672f\u548c\u6587\u6863\u3002",
                f"## \u5019\u9009 Hub\n\n\u8be5 Hub \u7531\u6587\u6863 [[{title}]] \u89e6\u53d1\uff0c\u7528\u4e8e\u805a\u5408\u76f8\u5173\u6280\u672f\u3001\u547d\u4ee4\u548c\u90e8\u7f72\u8bb0\u5f55\u3002\n\n## \u5ba1\u67e5\u72b6\u6001\n\n- status: suggested",
                hub_tags,
                [title] + topic_titles,
            )
            hubs.append({"title": hub_title, "source": title, "status": "suggested"})
            candidates.append(make_candidate(title, hub_title, "\u5efa\u8bae\u5f52\u7c7b", "\u6587\u6863\u540c\u65f6\u547d\u4e2d\u591a\u4e2a\u4e3b\u9898\u5173\u952e\u8bcd\uff0c\u9002\u5408\u805a\u5408\u5230 Hub\u3002"))

        if commands:
            command_title = f"{title} \u547d\u4ee4\u7247\u6bb5"
            add_doc(
                command_title,
                "tool",
                "\u667a\u80fd\u5bfc\u5165\u4ece Markdown \u4ee3\u7801\u5757\u4e2d\u63d0\u53d6\u7684\u547d\u4ee4\u8282\u70b9\u3002",
                "## \u547d\u4ee4\u7247\u6bb5\n\n" + "\n".join(f"- `{line}`" for line in commands),
                ["commands"],
                [title] + topic_titles + hub_titles,
            )
            candidates.append(make_candidate(title, command_title, "\u63d0\u53d6\u547d\u4ee4", "\u6587\u6863\u4ee3\u7801\u5757\u4e2d\u5305\u542b\u53ef\u6267\u884c\u547d\u4ee4\u3002"))

    rebuild()
    return {
        "ok": True,
        "mode": "smart_import",
        "raw_dir": raw_dir.relative_to(ROOT).as_posix(),
        "created": created,
        "merged": merged,
        "candidates": candidates,
        "hubs": hubs,
        "count": len(created) + len(merged),
    }


def import_markdown(payload: dict) -> dict:
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("请至少选择一个 Markdown 文件。")
    mode = str(payload.get("mode") or "merge_by_title")
    node_type = str(payload.get("type") or "concept")
    tags = [x.strip() for x in re.split(r"[,\uFF0C]", str(payload.get("tags") or "导入")) if x.strip()]
    links = [x.strip() for x in re.split(r"[,\uFF0C]", str(payload.get("links") or "")) if x.strip()]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    raw_dir = ROOT / "raw" / "imports" / stamp
    raw_dir.mkdir(parents=True, exist_ok=True)

    prepared: list[dict] = []
    for item in files:
        name = safe_id(str(item.get("name") or "import.md"))
        if not name.lower().endswith(".md"):
            name += ".md"
        content = str(item.get("content") or "").replace("\r\n", "\n")
        if not content.strip():
            continue
        raw_path = raw_dir / name
        raw_path.write_text(content, encoding="utf-8")
        prepared.append({"name": name, "title": title_from_markdown(name, content), "summary": summary_from_markdown(content), "content": content, "raw": raw_path.relative_to(ROOT).as_posix()})
    if not prepared:
        raise ValueError("选择的 Markdown 内容为空。")

    if mode == "smart_import":
        return import_smart_knowledge(payload, prepared, raw_dir, tags, links)
    if mode == "project_package":
        return import_project_package(payload, prepared, raw_dir, tags, links)

    groups: dict[str, dict] = {}
    if mode == "merge_all":
        title = str(payload.get("title") or prepared[0]["title"] or "导入合并节点").strip()
        groups[title] = {"title": title, "summary": prepared[0]["summary"], "blocks": [], "raws": []}
        for item in prepared:
            groups[title]["blocks"].append((item["name"], parse_frontmatter_text(item["content"])[1].strip()))
            groups[title]["raws"].append(item["raw"])
    elif mode == "split_headings":
        for item in prepared:
            sections = split_markdown_h2(item["content"])
            if not sections:
                sections = [(item["title"], parse_frontmatter_text(item["content"])[1].strip())]
            for heading, body in sections:
                title = heading.strip() or item["title"]
                group = groups.setdefault(title, {"title": title, "summary": summary_from_markdown(body), "blocks": [], "raws": []})
                group["blocks"].append((item["name"], body))
                group["raws"].append(item["raw"])
    else:
        for item in prepared:
            title = item["title"]
            group = groups.setdefault(title, {"title": title, "summary": item["summary"], "blocks": [], "raws": []})
            group["blocks"].append((item["name"], parse_frontmatter_text(item["content"])[1].strip()))
            group["raws"].append(item["raw"])

    created = []
    merged = []
    for group in groups.values():
        path, was_merge = append_or_create_import_doc(group["title"], node_type, group["summary"], tags, links, group["blocks"], group["raws"])
        record = {"title": group["title"], "path": path.relative_to(ROOT).as_posix(), "sources": list(dict.fromkeys(group["raws"]))}
        (merged if was_merge else created).append(record)
    rebuild()
    return {"ok": True, "mode": mode, "raw_dir": raw_dir.relative_to(ROOT).as_posix(), "created": created, "merged": merged, "count": len(created) + len(merged)}


def read_doc_payload(doc_ref: str) -> dict:
    path = resolve_doc_ref(doc_ref)
    if not path:
        raise FileNotFoundError("没有找到这个 Markdown 文档，或路径不在知识库目录内。")
    text, warning = read_text_lossy(path)
    title = title_from_markdown(path.name, text)
    return {"ok": True, "title": title, "path": path.relative_to(ROOT).as_posix(), "content": text, "encoding_warning": warning or "?" in text}


def delete_node_doc(payload: dict) -> dict:
    node_id = str(payload.get("id") or "").strip()
    confirm = bool(payload.get("confirm"))
    if not node_id:
        raise ValueError("缺少节点 id。")
    if not confirm:
        raise ValueError("删除前需要确认。")
    if node_id.startswith("topic-"):
        raise ValueError("这是自动派生的主题节点，不是独立文档。请删除它的来源文档，重建后该主题会自动消失。")

    graph = load_graph()
    node = find_node(graph, node_id)
    if not node:
        raise FileNotFoundError("图谱中没有找到这个节点。")

    doc_ref = str(node.get("doc") or "").strip()
    path = resolve_doc_ref(doc_ref)
    if not path:
        raise FileNotFoundError("这个节点没有可归档的独立 Markdown 文档。")

    rel = path.relative_to(ROOT).as_posix()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    deleted_dir = ROOT / "raw" / "deleted" / stamp
    deleted_dir.mkdir(parents=True, exist_ok=True)
    target = deleted_dir / path.name
    counter = 2
    while target.exists():
        target = deleted_dir / f"{path.stem}-{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), str(target))

    note_path = cache_path(node_id)
    note_deleted = False
    if note_path.exists():
        note_path.unlink()
        note_deleted = True

    layout = read_layout_payload()
    positions = layout.get("positions")
    if isinstance(positions, dict) and node_id in positions:
        positions.pop(node_id, None)
        save_layout_payload({"positions": positions, "viewport": layout.get("viewport", {})})

    rebuild()
    return {
        "ok": True,
        "id": node_id,
        "title": node.get("label") or node_id,
        "deleted_doc": rel,
        "archived_to": target.relative_to(ROOT).as_posix(),
        "note_deleted": note_deleted,
    }


def build_doc_ai_append_prompt(title: str, rel_path: str, current_text: str, instruction: str, node: dict | None, neighbors: list[dict]) -> list[dict]:
    excerpt = current_text[:9000]
    context = {
        "doc_title": title,
        "doc_path": rel_path,
        "node": node or {},
        "neighbors": neighbors[:12],
        "doc_excerpt": excerpt,
        "user_instruction": instruction,
    }
    return [
        {
            "role": "system",
            "content": (
                "你是一个个人工程知识库维护助手。你的任务不是聊天答疑，而是根据用户输入和现有 Markdown 文档，生成一段可以直接追加写入该 Markdown 的知识增补。"
                "必须输出 Markdown 正文片段，不要输出完整文档，不要输出 frontmatter，不要包裹 ```markdown。"
                "如果用户指出当前文档内容跑题或太泛，请先用一小段说明纠偏，再补充真正应该沉淀的知识。"
                "内容要偏工程实践，尽量包含：是什么、为什么在本项目里重要、常用命令/代码名、注意点。"
                "不要编造没有依据的项目事实；可以基于用户输入做明确标注。"
                "输出控制在 200 到 700 个中文字符之间。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请为下面这个知识库 Markdown 文档生成一段追加内容。\n\n"
                "输出格式建议：\n"
                "### 本次补充\n"
                "- ...\n"
                "### 关键点\n"
                "- ...\n\n"
                f"上下文 JSON：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def append_doc_ai_update(payload: dict) -> dict:
    doc_ref = str(payload.get("path") or payload.get("doc") or "").strip()
    instruction = str(payload.get("instruction") or "").strip()
    node_id = str(payload.get("node_id") or "").strip()
    if not doc_ref:
        raise ValueError("缺少文档路径。")
    if len(instruction) < 4:
        raise ValueError("请先输入你想补充或纠正的内容。")
    path = resolve_doc_ref(doc_ref)
    if not path:
        raise FileNotFoundError("没有找到这个 Markdown 文档，或路径不在知识库目录内。")
    current, warning = read_text_lossy(path)
    if warning:
        raise ValueError("该文档存在编码风险。请先重新导入干净的 UTF-8 Markdown，再使用 AI 写入。")
    title = title_from_markdown(path.name, current)
    rel = path.relative_to(ROOT).as_posix()
    graph = load_graph()
    node = find_node(graph, node_id) if node_id else None
    neighbors = node_neighbors(graph, node_id) if node_id else []
    addition = call_deepseek(build_doc_ai_append_prompt(title, rel, current, instruction, node, neighbors)).strip()
    addition = re.sub(r"^```(?:markdown|md)?\s*", "", addition.strip(), flags=re.I)
    addition = re.sub(r"\s*```$", "", addition.strip())
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    safe_instruction = instruction.replace("\n", " ").strip()
    if len(safe_instruction) > 160:
        safe_instruction = safe_instruction[:157] + "..."
    block = (
        "\n\n"
        f"## 知识增补：{stamp}\n\n"
        f"> 输入：{safe_instruction}\n\n"
        f"{addition}\n"
    )
    path.write_text(current.rstrip() + block, encoding="utf-8")
    rebuild()
    return {"ok": True, "path": rel, "title": title, "addition": addition, "updated_at": stamp}


class KnowledgeHandler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path: str) -> str:
        if path.lower().endswith(".md"):
            return "text/markdown; charset=utf-8"
        return super().guess_type(path)

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
        if parsed.path == "/api/doc":
            ref = parse_qs(parsed.query).get("path", [""])[0]
            try:
                self._send_json(200, read_doc_payload(ref))
            except Exception as exc:
                self._send_json(404, {"ok": False, "message": str(exc)})
            return
        if parsed.path == "/api/graph-layout":
            self._send_json(200, read_layout_payload())
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

        if parsed.path == "/api/graph-layout":
            try:
                self._send_json(200, save_layout_payload(payload))
            except Exception as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
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
                messages = build_prompt(node, node_neighbors(graph, node_id), read_node_excerpts(node))
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

        if parsed.path == "/api/doc-ai-append":
            try:
                self._send_json(200, append_doc_ai_update(payload))
            except Exception as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
            return

        if parsed.path == "/api/import-md":
            try:
                self._send_json(200, import_markdown(payload))
            except Exception as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
            return

        if parsed.path == "/api/node-create":
            try:
                self._send_json(200, create_node_doc(payload))
            except Exception as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
            return

        if parsed.path == "/api/node-delete":
            try:
                self._send_json(200, delete_node_doc(payload))
            except Exception as exc:
                self._send_json(400, {"ok": False, "message": str(exc)})
            return

        self._send_json(404, {"ok": False, "message": "未知接口。"})


def main() -> int:
    rebuild()
    os.chdir(ROOT)
    threading.Thread(target=watcher, daemon=True).start()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), KnowledgeHandler) as httpd:
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
