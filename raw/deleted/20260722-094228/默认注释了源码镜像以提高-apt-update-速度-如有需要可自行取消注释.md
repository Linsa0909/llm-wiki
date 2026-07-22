---
title: 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释
type: concept
summary: 安装完成之后该终端会自动进入到linux子系统
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-171413/WSL2安装.md
---
# 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释

## 导入来源：WSL2安装.md

## 1.windows 安装Wsl2

```
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

wsl --install
```

安装完成之后该终端会自动进入到linux子系统

重开终端 输入 

```
wsl -v -l 
```

可查看wsl版本

[Windows 10/11 WSL2 安装与配置指南 - Kelen](https://kelen.cc/share/windows-wsl2-installation-guide)





## 2. wsl2环境下安装 openclaw 

当前的wsl环境为 ubuntu 24.04 

先进行24ubuntu版本的换源：

```
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak

sudo vim /etc/apt/sources.list
```

```
# 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释
deb https://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
# 预发布软件源，不建议启用
# deb https://mirrors.aliyun.com/ubuntu/ noble-proposed main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ noble-proposed main restricted universe multiverse
```

更换源之后，建议先更新一下系统基础包，保持环境干净

```
sudo apt update && sudo apt upgrade -y
```

运行官方安装脚本

```
curl -fsSL https://openclaw.ai/install.sh | bash
```
