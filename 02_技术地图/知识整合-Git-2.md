---
title: 知识整合：Git

# 知识整合：Git

> 合并来源节点：Git 常用命令与 ghostcloud.cn 内网访问处理、Git URL 重写 insteadOf、Git 常用命令与 ghostcloud.cn 内网访问处理 命令清单、Git、知识整合：Git、Git 远程仓库域名访问失败：ghostcloud.cn 改走 192.168.2.46

> 原文档已归档到：raw/merged/20260721-163915/Git-常用命令与-ghostcloud.cn-内网访问处理.md、raw/merged/20260721-163915/Git-URL-重写-insteadOf.md、raw/merged/20260721-163915/Git-常用命令与-ghostcloud.cn-内网访问处理-命令清单.md、raw/merged/20260721-163915/Git.md、raw/merged/20260721-163915/知识整合-Git.md、raw/merged/20260721-163915/Git-远程仓库域名访问失败-ghostcloud.cn-改走-192.168.2.46.md



| 分类 | 内容范围 |
|---|---|
| 应进入主知识库 | Git 常用命令（所有分类）；`insteadOf` 原理与三种写法；`ghostcloud.cn` 内网访问问题的三种解决方案及对比；个人经验总结。 |
| 可作为补充素材 | 独立的命令清单，其内容已融入主知识库表格，可作为速查表保留。 |
| 应进入 Backup | 内容高度重叠的独立文件，如：命令清单文件（资料4）、自动摘要的Git节点（资料5）、问题库独立文件（资料7）。这些资料的内容已完全并入主知识库。 |
| 可删除候选 | 与资料1内容完全相同的原始导入文件（资料2），建议删除。 |

## 1. 知识库主题

### 1.1 中心主题

Git 常用命令与 ghostcloud.cn 内网访问处理

### 1.2 知识库定位

本知识库是**学习型技术知识库**，旨在为个人提供 Git 常用命令的速查手册，并沉淀一个真实的网络排障场景解决方案。文件结构清晰，便于学习、复习和后续的知识重构，**并非项目交付文档**。

### 1.3 内容范围

- Git 基础配置、仓库创建与克隆
- 工作区/暂存区/本地仓库的日常操作
- 提交历史查看与分支管理
- 远程仓库操作、撤销回退与仓库维护
- `git reflog` 等救命命令
- `ghostcloud.cn` 域名无法访问场景的三种解决方案（`insteadOf`、`remote set-url`、`hosts`）原理、命令与对比
- 个人经验总结与方案选择建议

## 2. 核心知识摘要

- **Git 工作流**: 工作区 → `git add` → 暂存区 → `git commit` → 本地仓库。
- **高频命令速记**: `status` (看状态)、`add/commit` (提交)、`log` (看历史)、`branch/switch` (分支)、`push/pull` (远程)、`reset/revert` (撤销)、`stash` (暂存)、`reflog` (救命)。
- **撤销黄金法则**: **本地分支用 `reset`，共享分支用 `revert`**。`revert` 通过创建新提交来撤销历史，安全无后患。
- **救命命令**: `git reflog`，可查看 HEAD 所有移动记录，用于找回误删的 commit。
- **场景方案选择**: 当远程仓库域名 `ghostcloud.cn` 不可达时，推荐使用 `url.<base>.insteadOf` 进行地址重写，该方案不影响仓库原有配置，仅对 Git 通信生效。
- **三种方案对比**: `insteadOf` (仅影响 Git，灵活)；`remote set-url` (直观但需逐个仓库修改)；`hosts` (全局生效，需管理员权限)。

## 3. 知识点分类索引

### 3.1 基础概念

| 知识点 | 解释 | 备注/来源 |
|---|---|---|
| 工作区 | 当前编辑的文件目录。 | Git 基础概念 |
| 暂存区（Index） | 用 `git add` 放入，准备提交的区域。 | Git 基础概念 |
| 本地仓库 | `git commit` 后的历史记录存储区。 | Git 基础概念 |
| remote | 远程仓库的别名和 URL。 | 资料1, 2 |
| HEAD | 指向当前分支最新提交的指针。 | Git 基础概念 |
| `url.<base>.insteadOf` | Git 的 URL 重写机制。在访问远程仓库前，自动将匹配的 URL 前缀替换为另一个前缀，不修改仓库的 `remote` 配置。 | 资料1, 2, 3 |

### 3.2 常用命令
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git config --global --list
git config --list
```

说明：

| 命令 | 作用 |
|---|---|
| `git config --global user.name "你的名字"` | 设置全局用户名 |
| `git config --global user.email "你的邮箱"` | 设置全局邮箱 |
| `git config --global --list` | 查看全局配置 |
| `git config --list` | 查看当前仓库配置 |

### 创建与克隆仓库
## 创建与克隆仓库

```bash
git init
git clone <url>
git clone <url> <目录名>
```

说明：

| 命令 | 作用 |
|---|---|
| `git init` | 在当前目录初始化新仓库 |
| `git clone <url>` | 克隆远程仓库到本地 |
| `git clone <url> <目录名>` | 克隆到指定目录 |

### 日常操作：工作区、暂存区、本地仓库
## 日常操作：工作区、暂存区、本地仓库

工作流：

```text
工作区 --git add--> 暂存区 --git commit--> 本地仓库
```

常用命令：

```bash
git status
git status -s
git add <文件>
git add .
git add -A
git commit -m "提交信息"
git commit -am "信息"
git commit --amend
git restore <文件>
git restore --staged <文件>
git reset HEAD~1
git reset --hard HEAD~1
```

说明：

| 命令 | 作用 |
|---|---|
| `git status` | 查看工作区和暂存区状态 |
| `git status -s` | 简洁模式显示状态 |
| `git add <文件>` | 将指定文件加入暂存区 |
| `git add .` | 将当前目录下变更加入暂存区 |
| `git add -A` | 加入所有变更，包括删除操作 |
| `git commit -m "提交信息"` | 提交暂存区到本地仓库 |
| `git commit -am "信息"` | 跳过 `git add`，直接提交已跟踪文件 |
| `git commit --amend` | 修改最近一次提交的消息或内容 |
| `git restore <文件>` | 撤销未暂存的工作区修改 |
| `git restore --staged <文件>` | 从暂存区撤出，不丢失文件修改 |
| `git reset HEAD~1` | 撤销最近一次 commit，保留修改 |
| `git reset --hard HEAD~1` | 撤销最近一次 commit 并丢弃修改，危险 |

注意：多人协作或不确定时，不要轻易使用 `git reset --hard`。它会丢弃工作区修改和提交后的历史。
| 命令 | 用途 | 使用场景 | 注意事项 |
|---|---|---|---|
| `git config --global user.name "<name>"` | 设置全局用户名 | 初始化 Git 环境 | - |
| `git config --global user.email "<email>"` | 设置全局邮箱 | 初始化 Git 环境 | - |
| `git init` | 初始化当前目录为新仓库 | 新建项目 | - |
| `git clone <url>` | 克隆远程仓库 | 参与已有项目 | 可加 ` <目录名>` 指定本地目录 |
| `git status` | 查看工作区和暂存区状态 | 日常操作 | 可用 `-s` 获取简洁输出 |
| `git add <文件>` | 将文件加入暂存区 | 准备提交 | `git add .` 添加当前目录变更；`git add -A` 添加所有变更 |
| `git commit -m "msg"` | 提交暂存区到本地仓库 | 记录变更 | `git commit -am "msg"` 可跳过 `add` 直接提交已跟踪文件 |
| `git commit --amend` | 修改最近一次提交 | 修正提交信息或内容 | 谨慎用于已推送的提交 |
| `git log` | 查看提交历史 | 回顾历史 | 可用 `--oneline`, `--graph`, `--all` 等参数 |
| `git switch <branch>` | 切换分支 | 切换工作分支 | 可用 `-c` 创建并切换 |
| `git merge <branch>` | 合并指定分支到当前分支 | 合并分支 | `--no-ff` 参数可保留分支历史 |
| `git remote -v` | 查看远程仓库地址 | 检查远程配置 | - |
| `git push <remote> <branch>` | 推送本地分支到远程 | 分享代码 | `-u` 参数建立跟踪关系 |
| `git pull` | 拉取远程并自动合并 | 获取最新代码 | 等价于 `fetch` + `merge` |
| `git fetch` | 只拉取远程信息，不合并 | 查看远程更新 | - |
| `git pull --rebase` | 拉取后通过变基合并 | 保持线性历史 | 需谨慎处理冲突 |
| `git reset HEAD~1` | 撤销最近一次 `commit`，保留修改 | 本地撤回提交 | `--soft` 保留修改至暂存区；`--mixed` 保留修改至工作区；`--hard` 丢弃修改（危险）|
| `git revert <commit-id>` | 创建新提交，抵消某次提交 | 安全撤销共享分支的提交 | 不改变历史，适合多人协作 |
| `git stash` | 暂存工作区改动 | 临时切换分支处理紧急事务 | `stash pop` 恢复，`stash list` 查看列表 |
| `git reflog` | 查看 HEAD 所有移动历史 | 找回丢失的提交或分支 | **救命命令** |
| `git clean -fd` | 删除未被跟踪的文件和目录 | 清理工作区 | 危险操作，会删除非版本控制文件 |
| `git gc` | 压缩仓库，优化存储 | 仓库维护，减少磁盘占用 | - |

### 3.3 配置项

| 配置项 | 含义 | 示例 | 注意事项 |
|---|---|---|---|
| `user.name` | 提交用户名 | `git config --global user.name "John Doe"` | 支持全局 (`--global`) 和局部配置 |
| `user.email` | 提交邮箱 | `git config --global user.email "john@example.com"` | 应与远程账号邮箱一致 |
| `url.<base>.insteadOf` | URL 地址重写 | `git config --global url."http://192.168.2.46/".insteadOf "http://ghostcloud.cn/"` | 仅影响 Git 通信，不修改仓库的 `remote` 配置 |

### 3.4 协议/API/接口

（无相关内容）

### 3.5 SDK/依赖/工具

| 名称 | 类型 | 用途 | 安装/使用方式 | 备注 |
|---|---|---|---|---|
| Git | 版本控制工具 | 代码版本管理与协作 | 系统安装或通过包管理器（如`apt`, `brew`, `choco`）安装 | 推荐使用 2.23 及以上版本（引入了 `switch/restore` 命令） |

### 3.6 操作流程/步骤

**场景：`ghostcloud.cn` 域名无法访问，需通过内网 IP 192.168.2.46 访问 Git 远程仓库**

1.  **问题判断**：确认网络环境，判断 `ghostcloud.cn` 域名不可达。
2.  **方案选择**：根据需求选择最佳方案。**推荐使用 `insteadOf` 方案**。
    -   **方案一：使用 `insteadOf`（推荐）**
        1.  **配置地址重写**：根据远程仓库的 URL 类型执行对应命令。
            -   **HTTP 地址**：`git config --global url."http://192.168.2.46/".insteadOf "http://ghostcloud.cn/"`
            -   **SSH URL 地址**：`git config --global url."ssh://git@192.168.2.46/".insteadOf "ssh://git@ghostcloud.cn/"`
            -   **SCP 风格 SSH 地址** (如 `git@ghostcloud.cn:org/repo.git`)：`git config --global url."git@192.168.2.46:".insteadOf "git@ghostcloud.cn:"`
        2.  **验证配置**：`git config --global --list | grep insteadOf`
        3.  **测试访问**：执行 `git pull` / `git push` 等操作，验证是否成功。
    -   **方案二：直接修改 remote URL**
        1.  **查看当前 remote**：`git remote -v`
        2.  **修改 origin 地址**：`git remote set-url origin http://192.168.2.46/你的项目路径.git`
        3.  **验证并测试**：`git remote -v` 然后执行 `git pull`。
    -   **方案三：修改系统 hosts 文件**
        1.  **编辑 hosts 文件**：使用管理员权限编辑 `/etc/hosts` (Linux/Mac) 或 `C:\Windows\System32\drivers\etc\hosts` (Windows)。
        2.  **添加映射**：在文件中添加一行 `192.168.2.46 ghostcloud.cn`。
        3.  **验证**：`ping ghostcloud.cn` 确认解析到新 IP。
        4.  **测试访问**：执行 `git pull` 验证。
3.  **方案对比总结**：
    -   **`insteadOf` 方案**：仅影响 Git，无需修改仓库配置，灵活且侵入性小。
    -   **`remote set-url` 方案**：简单直观，但需每个仓库单独操作，并将仓库地址写死为 IP。
    -   **`hosts` 方案**：系统全局生效，但需管理员权限，对非 Git 应用（如浏览器）也会产生影响。

### 3.7 常见问题与排错

| 问题/报错 | 可能原因 | 解决方式 | 备注 |
|---|---|---|---|
| `could not resolve host: ghostcloud.cn` | DNS 无法解析域名或域名不通 | 使用 `insteadOf` 或 `hosts` 将域名映射到可达 IP | 核心问题，参见 3.6 流程 |
| 配置 `insteadOf` 后未生效 | 重写规则的前缀（`insteadOf` 值）未能完全匹配仓库 `remote` URL 的开头 | 仔细核对 `git remote -v` 输出的 URL 前缀，确保 `git config` 命令中的前缀写法完全一致。注意 SCP 风格 URL 末尾的冒号 `:` | - |
| 误执行 `git reset --hard HEAD~1` 导致提交丢失 | 历史被丢弃 | 立即使用 `git reflog` 查找丢失提交的 commit-id，然后使用 `git reset --hard <commit-id>` 恢复 | `reflog` 是救命命令 |
| 多人协作时对共享分支执行 `git reset --hard` | 重写了共享分支历史，导致他人提交丢失或冲突 | 在共享分支上**永远使用 `git revert`**。若已操作，需与团队成员沟通，通过强制推送恢复，但风险极高 | 规则：共享分支用 `revert`，本地私有分支用 `reset` |
| 修改 hosts 后未生效 | 操作系统或应用存在 DNS 缓存 | 尝试刷新 DNS 缓存（命令行执行 `ipconfig /flushdns` (Windows) 或 `sudo dscacheutil -flushcache` (Mac)）或重启应用 | - |

### 3.8 易混淆点

| 易混淆项 | 区别说明 | 记忆方式 |
|---|---|---|
| `git reset --soft/mixed/hard` | `--soft` 只移动 HEAD，改动留在暂存区；`--mixed`(默认) 移动 HEAD 和暂存区，改动留在工作区；`--hard` 丢弃所有改动。 | “软（soft）留暂存，混（mixed）留工作，硬（hard）全丢” |
| `git revert` vs `git reset` | `revert` 通过创建新提交来“撤销”历史，安全；`reset` 通过移动分支指针来“改写”历史，危险。 | “revert 回滚历史新建，reset 硬改指针” |
| `git pull` vs `git fetch` | `pull` = `fetch` + `merge`，拉取并自动合并；`fetch` 只拉取远程数据到本地，**不自动合并**。 | “fetch 只看不听，pull 直接结婚” |
| `git pull` vs `git pull --rebase` | `pull` 默认使用 `merge`，会产生合并提交；`--rebase` 将本地提交重放在远端提交之上，历史更线性。 | “pull merge 有分叉，rebase 一条线” |
| `git switch` vs `git checkout` | `switch` 是 Git 2.23+ 引入的，专门用于切换分支；`checkout` 功能更复杂，还可用于恢复文件。 | “新用 switch 切分支，旧用 checkout 管所有” |

## 4. 主题知识结构图

```mermaid
mindmap
  root((Git 知识库))
    Git 命令
      配置初始化
        config / init / clone
      日常操作
        status / add / commit
        restore / reset / stash
      历史查看
        log / blame / show
      分支管理
        branch / switch / merge
      远程操作
        remote / push / pull / fetch
      撤销与恢复
        revert / reset / reflog
      清理与组合
        clean / gc
        add -p / rebase -i
    insteadOf 重写
      问题：域名不可达
        场景：ghostcloud.cn
        替代：192.168.2.46
      解决方案
        方案一：(推荐) insteadOf
          原理
