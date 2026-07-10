# LLM Wiki 个人知识库

LLM Wiki 是一个面向个人工程沉淀的本地知识库。它把真实项目过程、命令、问题排障和技术理解保存为 Markdown，再编译成可浏览、可搜索、可交互的知识图谱。

这个项目的核心思路不是“每次问 AI 一遍”，而是把你的历史经验长期沉淀下来：原始资料进入 `raw/`，整理后的 Wiki 文档进入分类目录，图谱和 AI 解释作为派生视图存在。

## 核心能力

- Markdown Wiki：所有知识节点本质上都是 `.md` 文档，方便长期维护和迁移。
- 知识图谱：自动读取 Markdown frontmatter、双链和主题关键词生成 `graph/graph.json`，并按关系强度控制默认连线，避免弱 `提到` 关系把图谱画乱。
- 智能导入：上传 Markdown 后可自动判断项目、技术、问题、部署、命令等节点，并生成候选关系和 Hub 建议。
- 文档视图：在右侧抽屉中打开 Markdown 文档，保留 Wiki 阅读体验，并支持用 AI 把增补内容写回当前 Markdown。
- 节点解释：节点可手动编辑说明，也可调用 DeepSeek 生成一次并缓存到本地。
- 图谱交互：支持拖动画布、缩放、单节点拖动、项目节点框选、组拖动、空白点击取消选择；项目节点点击有 `pointerup` 兜底，避免被拖动/框选逻辑吞掉。

## 启动

```powershell
cd C:\Users\Linsa\Desktop\llm-wiki
.\start.ps1
```

启动后访问：

```text
http://127.0.0.1:8765/graph/index.html
```

如果 `8765` 被旧进程占用，启动脚本会自动尝试下一个端口，例如：

```text
http://127.0.0.1:8766/graph/index.html
```

不要直接用 `file://` 打开页面。新增节点、智能导入、AI 生成、文档读取都依赖本地 HTTP 服务。

## 目录结构

```text
llm-wiki/
  00_入口/              首页、模板、知识库说明
  01_项目复盘/          项目级沉淀
  02_技术地图/          技术概念、库、服务、工具
  03_问题库/            bug、报错、排障卡片
  04_设备与部署/        设备、部署、验收清单
  raw/                  原始导入资料，本地留存
  graph/
    index.html          知识图谱前端
    graph.json          自动生成的图谱数据
    node_notes/         AI/人工解释缓存，本地留存
  scripts/
    kb_server.py        本地 HTTP 服务、AI 接口、导入和节点创建接口
    rebuild_graph.py    Markdown -> graph.json 编译器
  .env.local            本地私密配置，不提交 Git
```

## 智能导入

点击顶部 `导入 Markdown`，默认使用 `智能知识导入`。

导入流程：

1. 保存原始 Markdown 到 `raw/imports/`。
2. 判断文档类型：项目、技术、问题、部署、工具/命令。
3. 从代码块中提取常用命令。
4. 匹配已有节点和主题关键词。
5. 生成候选关系和 Hub 建议。
6. 写入对应 Wiki 目录，并重建图谱。

智能导入不会直接替你确认所有关系，它更像“候选整理器”。最终内容仍然可以人工审查、编辑和合并。

## 图谱连线策略

图谱数据会保留完整关系，但前端默认只绘制更有意义的强关系：

- `关联`：通常来自 frontmatter `links`，优先级最高。
- `引用`：来自 Markdown 双链，默认作为显式关系展示。
- `提到`：只有标题命中、标签命中、显式双链或多次重复出现时才默认连线；普通弱提到会保留在 `graph.json`，但不画线。
- 同一对节点存在多条关系时，默认只显示强度最高的一条。
- 单个节点的可见连线数量会做上限控制，避免项目节点或通用技术节点变成线团。

这样做的目标是：知识不丢，画面更适合阅读和演示。

## 图谱交互

- 单击节点：打开右侧知识卡片。
- 双击节点：同样打开/聚焦知识卡片。
- 点击空白画布：取消当前节点选择。
- 拖动画布：移动整个视图。
- 滚轮：缩放图谱。
- 拖动单个节点：临时调整展示位置。
- 选中项目节点后，在空白画布左键拖动：框选一组相关节点。
- 框选后拖动组内任意节点：整组节点一起移动，方便把一个项目簇拉开展示。
- 选中项目节点后如需拖动画布，可按住 `Shift` 或 `Alt` 再拖动空白区域。

当前节点位置调整属于前端展示层，刷新后会按图谱布局重新计算。后续可以增加“保存布局”能力。

## 文档视图

点击顶部 `文档` 可以打开 Wiki 文档列表。文档内容通过 `/api/doc` 读取，并在右侧抽屉中按 Markdown 样式渲染标题、列表、代码块、引用和链接。

在文档抽屉或节点卡片中，可以通过“写入当前 Markdown”的输入框描述你要补充/纠正/整理的内容。后端会调用 DeepSeek，把你的输入整理为知识片段并追加到对应 Markdown，然后自动重建图谱。

如果文档存在历史编码问题，页面会提示可能需要重新导入干净的 UTF-8 Markdown。

## AI 解释缓存

点击节点卡片里的 `AI 生成一次` 时，前端会调用：

```text
POST /api/node-explain
```

后端会把当前节点、关联节点、对应 Markdown 片段组装为 prompt，调用 DeepSeek，并把结果写入：

```text
graph/node_notes/
```

同一个节点后续优先读取缓存，不会重复调用 AI。只有点击 `重新生成` 才会覆盖旧缓存。

## DeepSeek 配置

在 `.env.local` 中配置：

```env
DEEPSEEK_API_KEY=你的 key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_API_BASE=https://api.deepseek.com/chat/completions
```

`.env.local` 不应提交到 GitHub。

## 开发说明

- 前端：原生 HTML + CSS + JavaScript + SVG。
- 后端：Python 标准库 `http.server`，没有引入 Web 框架。
- 图谱构建：`scripts/rebuild_graph.py` 扫描 Markdown 并生成 `graph/graph.json`。
- 本地服务：`scripts/kb_server.py` 提供文档读取、节点创建、智能导入和 AI 调用接口。

## 提交策略

建议提交：

- `graph/index.html`
- `scripts/kb_server.py`
- `scripts/rebuild_graph.py`
- `README.md`
- `.gitignore`
- 已确认可公开的 Wiki Markdown

默认不提交：

- `.env.local`
- `raw/imports/`
- `graph/node_notes/`
- 临时测试文件
