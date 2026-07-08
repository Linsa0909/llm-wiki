# LLM Wiki 个人知识库

这是一个面向个人工程沉淀的本地 LLM Wiki。它把真实项目过程沉淀为 Markdown 文档，再自动编译成知识图谱；点击节点可以查看解释、编辑解释，或调用 DeepSeek 生成一次并写入本地缓存。

## 核心目标

- 长期维护：知识以 Markdown 和 JSON 缓存落盘，不依赖一次性聊天记录。
- 保留个人历史细节：文档来自自己做过的项目复盘、问题排查、部署记录和命令记录。
- 图谱 + 文档双视图：图谱用于浏览关系，文档视图用于 Wiki 式阅读和搜索入口。
- AI 只做编译助手：AI 输出会写入缓存，后续读取缓存，不重复调用。

## 启动

```powershell
cd C:\Users\Linsa\Desktop\llm-wiki
.\start.ps1
```

浏览器打开：

```text
http://127.0.0.1:8765/graph/index.html
```

不要用 `file://` 打开图谱页面，因为新增节点、AI 生成、文档列表都依赖本地 HTTP 服务。

## 目录结构

```text
llm-wiki/
  00_入口/              首页、模板、知识库说明
  01_项目复盘/          项目级沉淀
  02_技术地图/          技术概念、库、服务、工具
  03_问题库/            bug、报错、排障卡片
  04_设备与部署/        设备、部署、验收清单
  graph/
    index.html          图谱前端
    graph.json          自动生成的图谱数据
    node_notes/         AI/人工解释缓存
  scripts/
    kb_server.py        本地 HTTP 服务、AI 接口、节点创建接口
    rebuild_graph.py    Markdown -> graph.json 编译器
  .env.local            本地私密配置，不提交 Git
```

## 当前代码主要用什么写的

- 前端：原生 HTML + CSS + JavaScript + SVG。
- 后端：Python 标准库 `http.server`，没有引入 Web 框架。
- 图谱数据：`scripts/rebuild_graph.py` 扫描 Markdown，生成 `graph/graph.json`。
- AI 调用：`scripts/kb_server.py` 通过 DeepSeek OpenAI-compatible Chat Completions 接口调用模型。
- 存储：Markdown 文档 + `graph/node_notes/*.json` 缓存。

## AI 生成一次：输入和输出

点击节点右侧的 `AI 生成一次` 时，前端会调用：

```text
POST /api/node-explain
```

### 输入给后端

```json
{
  "id": "topic-zlmediakit",
  "force": false
}
```

### 后端整理后输入给 DeepSeek

后端会把三类上下文组织成 prompt：

1. 当前节点

```json
{
  "id": "topic-zlmediakit",
  "label": "ZLMediaKit",
  "type": "service",
  "summary": "流媒体服务..."
}
```

2. 关联节点

```json
[
  { "label": "C++ 调用 FFmpeg 库", "type": "concept", "relation": "提到" },
  { "label": "Mino17 RK3588 红外采集推流复盘", "type": "project", "relation": "提到" }
]
```

3. 对应 Markdown 文档片段

```text
# ZLMediaKit 流媒体分发
C++ 程序只负责把 H264 RTMP 流推到 ZLMediaKit...
```

### DeepSeek 输出

DeepSeek 输出 Markdown，例如：

```md
### 是什么
ZLMediaKit 是一个轻量、高性能的流媒体服务器，支持 **RTMP、HTTP-FLV、HLS、RTSP** 等协议分发。

### 项目中怎么用
- **推流方**：C++ 程序通过 FFmpeg API 硬件编码后推送 RTMP。
- **播放方**：用 `ffplay`、VLC 或 Web 拉流。

### 关键点
端口映射和 `secret` 必须一致，否则 ZLM API 可能查不到流。
```

前端会把 Markdown 渲染为标题、加粗、行内代码和短列表。

## 不同节点类型的 AI prompt 策略

| 节点类型 | 生成重点 |
|---|---|
| project | 项目定位、整体架构、核心流程、跑通结果、关键结论 |
| concept/library/service/device/tool/deployment | 是什么、项目中怎么用、关键点、命令或代码名示例 |
| issue | 现象、原因、解决方式、验证效果 |

项目节点右侧会额外展示固定架构图：

```text
采集 -> 处理 -> 编码 -> 推流 -> 分发 -> 播放
```

## 缓存策略

第一次生成：

```text
点击节点 -> /api/node-explain -> 检查 node_notes -> 调用 DeepSeek -> 写入 graph/node_notes -> 前端展示
```

第二次点击同一节点：

```text
直接读取 graph/node_notes，不重复调用 AI
```

如果想用新 prompt 覆盖旧缓存，点击 `重新生成`。

## 新增节点

点击顶部 `新增节点`，填写标题、类型、摘要、标签、关联文档和正文。提交后会：

1. 在对应目录创建 Markdown 文档。
2. 自动重建 `graph/graph.json`。
3. 刷新图谱，新节点进入图谱和文档视图。

类型和目录映射：

| 类型 | 目录 |
|---|---|
| project | `01_项目复盘` |
| concept/library/service/device/tool/acceleration | `02_技术地图` |
| issue | `03_问题库` |
| deployment | `04_设备与部署` |

## 文档视图

点击顶部 `文档`，会打开 Wiki 文档列表。文档仍然是知识库主体，图谱只是另一种结构化展示。

## 安全说明

`.env.local` 存放 DeepSeek API Key，不应该提交到 GitHub。

示例：

```env
DEEPSEEK_API_KEY=你的key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_API_BASE=https://api.deepseek.com/chat/completions
```

仓库会通过 `.gitignore` 忽略 `.env.local`、缓存和临时文件。
