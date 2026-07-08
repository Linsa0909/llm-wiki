# 节点 AI 解释缓存设计

## 目标

知识图谱里的节点点击后，应该直接展示解释，而不是复制节点名称再去问 AI。解释可以由 AI 生成，但必须满足：**同一个节点生成一次后要缓存，后续点击只读缓存**。

## 当前实现

- `graph/index.html` 点击节点后打开右侧知识卡片。
- 前端先读取本地服务接口：`GET /api/node-note?id=<node_id>`。
- 如果服务端没有缓存，再读取浏览器 `localStorage` 和内置基础解释。
- 点击“保存/编辑解释”会同时写入：
  - 浏览器 `localStorage`
  - 本地文件缓存：`graph/node_notes/<node_id>.json`

## 后续接入 DeepSeek 的正确方式

不能在前端 HTML 里直接写 DeepSeek API key。正确流程应该是：

```text
点击节点
  -> 前端请求本地服务
  -> 本地服务检查 graph/node_notes 是否已有缓存
  -> 已有：直接返回缓存
  -> 没有：读取节点信息和相关 Markdown 文档片段
  -> 调用一次 DeepSeek
  -> 把结果写入 graph/node_notes
  -> 返回给前端展示
```

这样做的原因：

- API key 不暴露在浏览器里。
- 节点解释可长期沉淀进知识库。
- 后续不重复调用 AI，速度更快，也避免同一节点解释每次不一致。

## 当前边界

当前版本已经完成点击展示和缓存读写，但还没有真正调用 DeepSeek。等 DeepSeek API key 和对应 skill 确认后，只需要在 `scripts/kb_server.py` 增加一个生成接口即可。