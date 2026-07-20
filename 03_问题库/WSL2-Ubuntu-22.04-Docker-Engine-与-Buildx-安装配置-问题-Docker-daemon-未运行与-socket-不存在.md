---
title: WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：Docker daemon 未运行与 socket 不存在
type: issue
summary: 从项目资料包中自动识别的问题、报错或排障记录。
tags:
  - WSL2
  - Docker
  - Buildx
  - Ubuntu22.04
  - systemd
  - 部署
  - 命令
  - 项目导入
  - issue
links:
  - Docker
  - Docker buildx
  - 部署与运维
  - Linux 系统与设备
  - 容器镜像构建
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置
sources:
  - raw/imports/20260713-195439/WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md
---
# WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 问题：Docker daemon 未运行与 socket 不存在

## 导入来源：项目资料包

## 问题片段

## Docker daemon 未运行与 socket 不存在

在 Windows 的 WSL2 Ubuntu 22.04 环境中安装 Docker 官方 Docker Engine、Docker CLI、containerd、Buildx 和 Compose 插件，并确保 Docker daemon 由 systemd 管理，解决 `Docker daemon 未运行`、`/var/run/docker.sock 不存在`、`docker version 只有 Client 没有 Server` 等问题。
