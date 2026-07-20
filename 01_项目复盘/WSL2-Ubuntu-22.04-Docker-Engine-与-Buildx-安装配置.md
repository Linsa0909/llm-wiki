---
title: WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置
type: project
summary: 由项目资料包自动生成的项目复盘入口，包含拆分节点和候选关系。
tags:
  - WSL2
  - Docker
  - Buildx
  - Ubuntu22.04
  - systemd
  - 部署
  - 命令
  - 项目导入
  - project
links:
  - Docker
  - Docker buildx
  - 部署与运维
  - Linux 系统与设备
  - 容器镜像构建
  - Linux Shell
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 命令清单
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 部署流程
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：Docker daemon 未运行与 socket 不存在
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：常见问题与定位
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：个人经验总结
sources:
  - raw/imports/20260713-195439/WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md
---
# WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置

## 导入来源：项目资料包

## 导入来源

- WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md -> `raw/imports/20260713-195439/WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md`

## 自动拆分节点

- [[Docker]]
- [[Docker buildx]]
- [[Linux Shell]]
- [[WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 命令清单]]
- [[WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 部署流程]]
- [[WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：Docker daemon 未运行与 socket 不存在]]
- [[WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：常见问题与定位]]
- [[WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：个人经验总结]]

## 候选关系（待人工审查）

- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --使用--> Docker：项目文档中出现 Docker 相关关键词或命令。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --使用--> Docker buildx：项目文档中出现 Docker buildx 相关关键词或命令。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --使用--> Linux Shell：项目文档中出现 Linux Shell 相关关键词或命令。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --沉淀--> WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 命令清单：项目文档中包含可执行命令或脚本片段。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --部署--> WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 部署流程：文档中出现部署、启动、容器或设备相关内容。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --排障--> WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：Docker daemon 未运行与 socket 不存在：文档中出现问题、错误、失败或解决等排障信号。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --排障--> WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：常见问题与定位：文档中出现问题、错误、失败或解决等排障信号。
- [suggested] WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 --排障--> WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：个人经验总结：文档中出现问题、错误、失败或解决等排障信号。

## 原始材料摘要

## 来源：WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md

# WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置

## 目标

在 Windows 的 WSL2 Ubuntu 22.04 环境中安装 Docker 官方 Docker Engine、Docker CLI、containerd、Buildx 和 Compose 插件，并确保 Docker daemon 由 systemd 管理，解决 `Docker daemon 未运行`、`/var/run/docker.sock 不存在`、`docker version 只有 Client 没有 Server` 等问题。

## 适用场景

- Windows 上使用 WSL2 作为 Linux 开发环境。
- Ubuntu 22.04 发行版需要本地运行 Docker Engine。
- 需要使用 `docker buildx` 构建镜像，或做跨架构镜像构建前的环境准备。
- 不依赖 Docker Desktop，而是在 WSL 内直接安装 Docker 官方软件包。

## 总体判断链路

1. 先确认发行版运行在 WSL 2，而不是 WSL 1。
2. 在 WSL Ubuntu 中启用 systemd。
3. 清理 Ubuntu 自带或旧版 Docker 相关包，避免和 Docker 官方源冲突。
4. 添加 Docker 官方 APT 源和 GPG 签名密钥。
5. 安装 `docker-ce`、`docker-ce-cli`、`containerd.io`、`docker-buildx-plugin`、`docker-compose-plugin`。
6. 使用 systemd 启动 `containerd.service` 和 `docker.service`。
7. 将当前用户加入 `docker` 用户组，让普通用户可直接访问 `/var/run/docker.sock`。
8. 通过 `docker version`、`docker info`、`hello-world`、`docker buildx ls` 验证。

## Windows PowerShell 中确认 WSL 版本

```powershell
wsl -l -v
wsl --version
```

预期发行版类似：

```text
NAME            STATE     VERSION
Ubuntu-22.04    Running   2
```

如果是 WSL 1：

```powershell
wsl --set-version Ubuntu-22.04 2
wsl --update
```

## WSL Ubuntu 中启用 systemd

进入 Ubuntu 后检查：

```bash
ps -p 1 -
