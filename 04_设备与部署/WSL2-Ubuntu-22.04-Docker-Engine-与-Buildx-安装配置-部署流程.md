---
title: WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 部署流程
type: deployment
summary: 从项目资料包中自动抽取的部署、启动和验证信息。
tags:
  - WSL2
  - Docker
  - Buildx
  - Ubuntu22.04
  - systemd
  - 部署
  - 命令
  - 项目导入
  - deployment
links:
  - Docker
  - Docker buildx
  - 部署与运维
  - Linux 系统与设备
  - 容器镜像构建
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置
  - WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 命令清单
sources:
  - raw/imports/20260713-195439/WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md
---
# WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置 部署流程

## 导入来源：项目资料包

## 部署相关内容

### 来源：WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md
# 来源：WSL2-Ubuntu-22.04-Docker-Engine-与-Buildx-安装配置.md

### WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置
# WSL2 Ubuntu 22.04 Docker Engine 与 Buildx 安装配置

### 目标
## 目标

在 Windows 的 WSL2 Ubuntu 22.04 环境中安装 Docker 官方 Docker Engine、Docker CLI、containerd、Buildx 和 Compose 插件，并确保 Docker daemon 由 systemd 管理，解决 `Docker daemon 未运行`、`/var/run/docker.sock 不存在`、`docker version 只有 Client 没有 Server` 等问题。

### 适用场景
## 适用场景

- Windows 上使用 WSL2 作为 Linux 开发环境。
- Ubuntu 22.04 发行版需要本地运行 Docker Engine。
- 需要使用 `docker buildx` 构建镜像，或做跨架构镜像构建前的环境准备。
- 不依赖 Docker Desktop，而是在 WSL 内直接安装 Docker 官方软件包。

### 总体判断链路
## 总体判断链路

1. 先确认发行版运行在 WSL 2，而不是 WSL 1。
2. 在 WSL Ubuntu 中启用 systemd。
3. 清理 Ubuntu 自带或旧版 Docker 相关包，避免和 Docker 官方源冲突。
4. 添加 Docker 官方 APT 源和 GPG 签名密钥。
5. 安装 `docker-ce`、`docker-ce-cli`、`containerd.io`、`docker-buildx-plugin`、`docker-compose-plugin`。
6. 使用 systemd 启动 `containerd.service` 和 `docker.service`。
7. 将当前用户加入 `docker` 用户组，让普通用户可直接访问 `/var/run/docker.sock`。
8. 通过 `docker version`、`docker info`、`hello-world`、`docker buildx ls` 验证。

### WSL Ubuntu 中启用 systemd
## WSL Ubuntu 中启用 systemd

进入 Ubuntu 后检查：

```bash
ps -p 1 -o comm=
```

如果输出：

```text
systemd
```

可以直接继续安装 Docker。

如果输出：

```text
init
```

创建 `/etc/wsl.conf`：

```bash
sudo tee /etc/wsl.conf >/dev/null <<'EOF'
[boot]
systemd=true
EOF
```

然后回到 Windows PowerShell：

```powershell
wsl --shutdown
```

重新打开 Ubuntu，再执行：

```bash
ps -p 1 -o comm=
```

预期输出：

```text
systemd
```

systemd 正常后，WSL 可以用 `systemctl` 管理 `docker.service` 和 `containerd.service`。
