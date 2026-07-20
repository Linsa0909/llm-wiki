---
title: Git
type: tool
summary: 从项目资料包中自动识别的 Git 相关技术节点。
tags:
  - Git
  - 版本控制
  - 命令
  - 远程仓库
  - ghostcloud
  - insteadOf
  - 排障
  - 项目导入
  - git
  - version-control
links:
  - Git 工作流
  - Linux Shell
  - Git 常用命令与 ghostcloud.cn 内网访问处理
  - Git URL 重写 insteadOf
sources:
  - raw/imports/20260714-153922/Git-常用命令与-ghostcloud.cn-内网访问处理.md
---
# Git

## 导入来源：项目资料包

## 自动识别依据

### Git 常用命令与 ghostcloud.cn 内网访问处理
# Git 常用命令与 ghostcloud.cn 内网访问处理

### 目标
## 目标

整理 Git 日常高频命令，并沉淀一个真实使用场景：远程仓库地址中使用 `ghostcloud.cn`，但当前网络无法解析或访问该域名，需要通过内网 IP `192.168.2.46` 访问。该场景优先使用 Git 的 `url.<base>.insteadOf` 做地址重写，也可以按需要改 remote URL 或配置 hosts。

### 适用场景
## 适用场景

- 新机器初始化 Git 环境。
- 需要快速回忆 `add / commit / branch / remote / reset / stash / reflog` 等命令。
- 远程仓库域名不可访问，但内网 IP 可访问。
- 希望不修改仓库 remote URL 的情况下，让 `git pull` / `git push` 自动走内网 IP。
