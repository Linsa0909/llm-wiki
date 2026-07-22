---
title: Mino17 红外相机 RK3588 C++ 采集推流方案汇报 命令片段
type: tool
summary: 智能导入从 Markdown 代码块中提取的命令节点。
tags:
  - 导入
  - 智能导入
  - commands
links:
  - Mino17 红外相机 RK3588 C++ 采集推流方案汇报
  - Docker
  - Docker buildx
  - Linux Shell
  - FFmpeg
  - ZLMediaKit
  - RK3588
  - 容器镜像构建
  - 部署与运维
  - Linux 系统与设备
  - 视频采集与推流
sources:
  - raw/imports/20260710-160955/Mino17_Cpp_RK3588_Report.md
---
# Mino17 红外相机 RK3588 C++ 采集推流方案汇报 命令片段

## 导入来源：智能导入

## 命令片段

- `ffmpeg -f v4l2 -i /dev/video59 ... -c:v h264_rkmpp ... rtmp://...`
- `ffmpeg-rockchip-bin/            RK3588 定制 FFmpeg/libav 运行库`
- `tar -xzf Mino17.tar.gz`
