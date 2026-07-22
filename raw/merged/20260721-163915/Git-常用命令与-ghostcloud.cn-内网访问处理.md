---
title: Git 常用命令与 ghostcloud.cn 内网访问处理
type: project
summary: 由项目资料包自动生成的项目复盘入口，包含拆分节点和候选关系。
tags:
  - Git
  - Git URL 重写 insteadOf
  - 版本控制
  - 命令
  - 远程仓库
  - ghostcloud
  - insteadOf
  - 排障
  - 项目导入
  - project
links:
  - Git 工作流
  - Linux Shell
  - Git
  - Git 常用命令与 ghostcloud.cn 内网访问处理 命令清单
  - Git 远程仓库域名访问失败：ghostcloud.cn 改走 192.168.2.46
  - Git 常用命令与 ghostcloud.cn 内网访问处理 问题：个人经验总结
sources:
  - raw/imports/20260714-153922/Git-常用命令与-ghostcloud.cn-内网访问处理.md
---
# Git 常用命令与 ghostcloud.cn 内网访问处理

## 导入来源：项目资料包

## 导入来源

- Git-常用命令与-ghostcloud.cn-内网访问处理.md -> `raw/imports/20260714-153922/Git-常用命令与-ghostcloud.cn-内网访问处理.md`

## 自动拆分节点

- [[Git]]
- [[Git URL 重写 insteadOf]]
- [[Linux Shell]]
- [[Git 常用命令与 ghostcloud.cn 内网访问处理 命令清单]]
- [[Git 远程仓库域名访问失败：ghostcloud.cn 改走 192.168.2.46]]
- [[Git 常用命令与 ghostcloud.cn 内网访问处理 问题：个人经验总结]]

## 候选关系（待人工审查）

- [suggested] Git 常用命令与 ghostcloud.cn 内网访问处理 --使用--> Git：项目文档中出现 Git 相关关键词或命令。
- [suggested] Git 常用命令与 ghostcloud.cn 内网访问处理 --使用--> Git URL 重写 insteadOf：本次 ghostcloud.cn 内网访问问题主要通过 Git insteadOf 地址重写解决。
- [suggested] Git 常用命令与 ghostcloud.cn 内网访问处理 --使用--> Linux Shell：项目文档中出现 Linux Shell 相关关键词或命令。
- [suggested] Git 常用命令与 ghostcloud.cn 内网访问处理 --沉淀--> Git 常用命令与 ghostcloud.cn 内网访问处理 命令清单：项目文档中包含可执行命令或脚本片段。
- [suggested] Git 常用命令与 ghostcloud.cn 内网访问处理 --排障--> Git 远程仓库域名访问失败：ghostcloud.cn 改走 192.168.2.46：文档中出现问题、错误、失败或解决等排障信号。
- [suggested] Git 常用命令与 ghostcloud.cn 内网访问处理 --排障--> Git 常用命令与 ghostcloud.cn 内网访问处理 问题：个人经验总结：文档中出现问题、错误、失败或解决等排障信号。

## 原始材料摘要

## 来源：Git-常用命令与-ghostcloud.cn-内网访问处理.md

# Git 常用命令与 ghostcloud.cn 内网访问处理

## 目标

整理 Git 日常高频命令，并沉淀一个真实使用场景：远程仓库地址中使用 `ghostcloud.cn`，但当前网络无法解析或访问该域名，需要通过内网 IP `192.168.2.46` 访问。该场景优先使用 Git 的 `url.<base>.insteadOf` 做地址重写，也可以按需要改 remote URL 或配置 hosts。

## 适用场景

- 新机器初始化 Git 环境。
- 需要快速回忆 `add / commit / branch / remote / reset / stash / reflog` 等命令。
- 远程仓库域名不可访问，但内网 IP 可访问。
- 希望不修改仓库 remote URL 的情况下，让 `git pull` / `git push` 自动走内网 IP。

## Git 基础配置

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
git restore
