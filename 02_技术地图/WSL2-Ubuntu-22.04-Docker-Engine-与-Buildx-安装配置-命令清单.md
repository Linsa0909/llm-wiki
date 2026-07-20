---
title: WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 命令清单
type: tool
summary: 从项目 Markdown 代码块中自动提取的常用命令。
tags:
  - WSL2
  - Docker
  - Buildx
  - Ubuntu22.04
  - systemd
  - 部署
  - 命令
  - 项目导入
  - commands
links:
  - Docker
  - Docker buildx
  - 部署与运维
  - Linux 系统与设备
  - 容器镜像构建
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置
  - Linux Shell
sources:
  - raw/imports/20260713-195439/WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md
---
# WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 命令清单

## 导入来源：项目资料包

## 命令清单

- `sudo systemctl status docker --no-pager`
- `srw-rw---- 1 root docker ... /var/run/docker.sock`
- `sudo usermod -aG docker "$USER"`
- `docker version`
- `docker info`
- `docker run --rm hello-world`
- `systemctl status docker --no-pager`
- `journalctl -u docker -n 100 --no-pager`
- `docker buildx version`
- `docker buildx ls`
- `default*    docker            running`
