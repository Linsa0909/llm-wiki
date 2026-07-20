#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build graph/graph.json from Markdown wiki documents."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graph" / "graph.json"
DOC_DIRS = ["01_项目复盘", "02_技术地图", "03_问题库", "04_设备与部署"]

TYPE_BY_DIR = {
    "01_项目复盘": "project",
    "02_技术地图": "concept",
    "03_问题库": "issue",
    "04_设备与部署": "deployment",
}

DERIVED_TOPICS = {
    "libavdevice": {"type": "library", "summary": "FFmpeg 设备输入输出库。本项目用它注册并打开 v4l2 摄像头设备，例如 /dev/video59。", "tags": ["FFmpeg", "V4L2", "采集"]},
    "libavformat": {"type": "library", "summary": "FFmpeg 封装与协议库。本项目用它打开输入流、创建 FLV/RTMP 输出并写入推流包。", "tags": ["FFmpeg", "RTMP", "封装"]},
    "libavcodec": {"type": "library", "summary": "FFmpeg 编解码库。本项目用它调用 h264_rkmpp，在 RK3588 上完成 H264 硬件编码。", "tags": ["FFmpeg", "H264", "rkmpp"]},
    "libavutil": {"type": "library", "summary": "FFmpeg 基础工具库，提供帧、包、时间基、错误处理和硬件上下文等基础能力。", "tags": ["FFmpeg", "基础库"]},
    "libswscale": {"type": "library", "summary": "FFmpeg 图像缩放与像素格式转换库。本项目的 CPU 图像路径会用到格式转换能力。", "tags": ["FFmpeg", "像素格式"]},
    "h264_rkmpp": {"type": "acceleration", "summary": "Rockchip MPP 暴露给 FFmpeg 的 H264 硬件编码器，本项目的硬件加速核心。", "tags": ["RK3588", "硬件编码"]},
    "ZLMediaKit": {"type": "service", "summary": "流媒体服务。接收 C++ 程序推送的 RTMP 流，再分发为 RTMP、HTTP-FLV、HLS、RTSP 等播放地址。", "tags": ["流媒体", "RTMP", "HLS"]},
    "V4L2": {"type": "device", "summary": "Linux 视频采集接口。本项目通过它访问 Mino17 摄像头暴露出的 /dev/videoX 设备文件。", "tags": ["Linux", "摄像头", "设备文件"]},
}

WIKI_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
LABEL_ASSOC = "\u5173\u8054"
LABEL_REF = "\u5f15\u7528"
LABEL_MENTION = "\u63d0\u5230"
MAX_VISIBLE_DEGREE = 8

FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
IMPORT_SOURCE_RE = re.compile(r"raw/imports/(\d{8}-\d{6})/")


def slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\\/:*?\"<>|\s]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "node"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONT_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end():]
    data: dict[str, object] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(line[4:].strip().strip('"\''))
            continue
        if ":" in line:
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


def title_from_body(path: Path, body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def summary_from_body(body: str) -> str:
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "|", "-", ">")):
            continue
        return line[:160]
    return ""


def rel_doc(path: Path) -> str:
    return "../" + path.relative_to(ROOT).as_posix()


def import_stamp(sources: list[str]) -> str:
    for source in sources:
        match = IMPORT_SOURCE_RE.search(str(source))
        if match:
            return match.group(1)
    return ""


def normalize_target(raw: str, title_to_node: dict[str, str], path_to_node: dict[str, str]) -> str | None:
    raw = raw.strip().replace("\\", "/")
    candidates = [raw + ".md", raw] if not raw.endswith(".md") else [raw]
    for candidate in candidates:
        clean = candidate.lstrip("./")
        for path_key, node_id in path_to_node.items():
            if path_key.endswith(clean):
                return node_id
    name = Path(raw).stem
    return title_to_node.get(name) or title_to_node.get(raw)



def label_rank(label: str) -> int:
    return {LABEL_ASSOC: 3, LABEL_REF: 2, LABEL_MENTION: 1}.get(label, 0)


def add_link(
    links: list[dict],
    seen: set[tuple[str, str, str]],
    source: str,
    target: str | None,
    label: str,
    strength: float = 0.5,
    visible: bool = True,
    reason: str = "",
) -> None:
    if not target or source == target:
        return
    key = (source, target, label)
    if key in seen:
        return
    seen.add(key)
    link = {"source": source, "target": target, "label": label, "strength": round(float(strength), 3)}
    if not visible:
        link["visible"] = False
    if reason:
        link["reason"] = reason
    links.append(link)


def topic_signal(topic: str, node: dict, body: str, text: str) -> tuple[float, bool, str]:
    topic_l = topic.lower()
    title_l = str(node.get("label") or "").lower()
    tags_l = [str(x).lower() for x in node.get("tags") or []]
    body_l = body.lower()
    text_l = text.lower()
    count = text_l.count(topic_l)
    if topic_l in title_l:
        return 0.9, True, "title match"
    if any(topic_l == tag or topic_l in tag for tag in tags_l):
        return 0.82, True, "tag match"
    if f"[[{topic_l}" in body_l:
        return 0.78, True, "explicit wiki link"
    if count >= 3:
        return 0.68, True, f"repeated mention x{count}"
    return 0.25, False, "weak mention"


def compact_visible_links(links: list[dict]) -> list[dict]:
    best_by_pair: dict[tuple[str, str], dict] = {}
    for link in links:
        pair = tuple(sorted([str(link["source"]), str(link["target"])]))
        current = best_by_pair.get(pair)
        score = float(link.get("strength", 0)) + label_rank(str(link.get("label"))) * 0.1
        if current is None:
            best_by_pair[pair] = {"link": link, "score": score}
        elif score > current["score"]:
            current["link"]["visible"] = False
            best_by_pair[pair] = {"link": link, "score": score}
        else:
            link["visible"] = False

    visible_candidates = [x for x in links if x.get("visible", True)]
    visible_candidates.sort(key=lambda x: (float(x.get("strength", 0)), label_rank(str(x.get("label")))), reverse=True)
    degree: dict[str, int] = {}
    keep: set[int] = set()
    for link in visible_candidates:
        source = str(link["source"])
        target = str(link["target"])
        strong = float(link.get("strength", 0)) >= 0.88
        source_room = degree.get(source, 0) < (MAX_VISIBLE_DEGREE + (3 if strong else 0))
        target_room = degree.get(target, 0) < (MAX_VISIBLE_DEGREE + (3 if strong else 0))
        if source_room and target_room:
            keep.add(id(link))
            degree[source] = degree.get(source, 0) + 1
            degree[target] = degree.get(target, 0) + 1

    for link in links:
        if link.get("visible", True) and id(link) not in keep:
            link["visible"] = False
            link["reason"] = (str(link.get("reason") or "") + "; hidden by degree cap").strip("; ")
    return links


def main() -> int:
    md_files: list[Path] = []
    for dirname in DOC_DIRS:
        base = ROOT / dirname
        if base.exists():
            md_files.extend(sorted(base.rglob("*.md")))

    nodes: list[dict] = []
    docs: list[tuple[Path, dict, dict, str, str]] = []
    title_to_node: dict[str, str] = {}
    path_to_node: dict[str, str] = {}

    for path in md_files:
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        fm, body = parse_frontmatter(text)
        top_dir = path.relative_to(ROOT).parts[0]
        title = str(fm.get("title") or title_from_body(path, body))
        node_type = str(fm.get("type") or TYPE_BY_DIR.get(top_dir, "note"))
        node_id = str(fm.get("id") or slug(path.relative_to(ROOT).with_suffix("").as_posix()))
        tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
        sources = fm.get("sources") if isinstance(fm.get("sources"), list) else []
        docs_meta = fm.get("docs") if isinstance(fm.get("docs"), list) else []
        doc_url = rel_doc(path)
        source_refs = [str(x) for x in sources]
        created_at = str(fm.get("created_at") or "")
        imported_at = created_at or import_stamp(source_refs)
        node = {"id": node_id, "label": title, "type": node_type, "doc": doc_url, "docs": [doc_url] + [str(x) for x in docs_meta], "sources": source_refs, "summary": str(fm.get("summary") or summary_from_body(body)), "tags": tags, "is_new": False, "imported_at": imported_at}
        nodes.append(node)
        docs.append((path, node, fm, body, text))
        title_to_node[title] = node_id
        title_to_node[path.stem] = node_id
        path_to_node[path.relative_to(ROOT).as_posix()] = node_id

    links: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    recent_nodes = sorted(
        (node for node in nodes if str(node.get("imported_at") or "")),
        key=lambda node: str(node.get("imported_at") or ""),
        reverse=True,
    )[:2]
    for node in recent_nodes:
        node["is_new"] = True

    for _path, node, fm, body, text in docs:
        source = node["id"]
        fm_links = fm.get("links")
        if isinstance(fm_links, list):
            for item in fm_links:
                add_link(links, seen, source, normalize_target(str(item), title_to_node, path_to_node), LABEL_ASSOC, strength=0.82, visible=True, reason="frontmatter link")
        for match in WIKI_RE.finditer(body):
            add_link(links, seen, source, normalize_target(match.group(1), title_to_node, path_to_node), LABEL_REF, strength=0.72, visible=True, reason="wiki link")

        lower_text = text.lower()
        for topic, meta in DERIVED_TOPICS.items():
            if topic.lower() not in lower_text:
                continue
            topic_id = "topic-" + slug(topic)
            if not any(n["id"] == topic_id for n in nodes):
                nodes.append({"id": topic_id, "label": topic, "type": meta["type"], "doc": node["doc"], "docs": node.get("docs", [node["doc"]]), "sources": node.get("sources", []), "summary": meta["summary"], "tags": meta["tags"]})
            strength, visible, reason = topic_signal(topic, node, body, text)
            add_link(links, seen, source, topic_id, LABEL_MENTION, strength=strength, visible=visible, reason=reason)

    GRAPH.parent.mkdir(parents=True, exist_ok=True)
    links = compact_visible_links(links)
    GRAPH.write_text(json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {GRAPH}")
    print(f"节点: {len(nodes)}，连线: {len(links)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
