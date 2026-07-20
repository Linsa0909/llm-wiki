# llm-wiki MCP

这是 `llm-wiki` 的本地 MCP 桥接服务，用来让 Codex 在聊天中直接把项目复盘、部署问题、命令片段和技术总结沉淀进知识库。

## 工具

- `health`：检查知识库路径、文档数量、图谱状态。
- `ingest_markdown`：导入一篇 Markdown，走智能导入。
- `ingest_project_notes`：按项目资料包方式沉淀一次项目/问题/部署过程，自动拆成项目、技术、问题、部署、命令节点。
- `search`：搜索已有文档和节点。
- `rebuild_graph`：重建 `graph/graph.json`。
- `get_node`：读取节点详情和关联节点。
- `append_doc`：追加内容到已有 Markdown 文档。

## Codex 配置示例

在 `C:\Users\Linsa\.codex\config.toml` 中加入：

```toml
[mcp_servers.llm_wiki]
command = 'C:\Users\Linsa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
args = ['C:\Users\Linsa\Desktop\llm-wiki\mcp\llm_wiki_mcp.py', '--root', 'C:\Users\Linsa\Desktop\llm-wiki']
startup_timeout_sec = 30

[mcp_servers.llm_wiki.env]
LLM_WIKI_ROOT = 'C:\Users\Linsa\Desktop\llm-wiki'
```

配置后重启 Codex，新会话中即可看到 `llm_wiki` MCP 工具。
