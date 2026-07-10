---
title: Mino17 红外相机 RK3588 C++ 采集推流方案汇报
type: issue
summary: 智能导入识别的问题、报错或排障节点。
tags:
  - 导入
  - 智能导入
  - issue
links:
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
# Mino17 红外相机 RK3588 C++ 采集推流方案汇报

## 导入来源：智能导入

## 问题来源

## 5. 使用到的主要库

| 库 | 作用 |
|---|---|
| `libavdevice` | 访问 V4L2 摄像头设备 |
| `libavformat` | 输入/输出封装，RTMP/FLV 推流 |
| `libavcodec` | 解码、编码，调用 `h264_rkmpp` |
| `libavutil` | FFmpeg 基础工具、错误处理、硬件上下文 |
| `libswscale` | 像素格式转换，如 RGB24 到 NV12 |
| `libswresample` | FFmpeg 运行时依赖 |
| `librga` | RK RGA 图像处理库，当前检测到但 50fps 主链路未启用 |
| `librockchip_mpp` | RK3588 MPP 硬件编解码依赖 |
| `libx264` | FFmpeg 运行时依赖，当前主编码器不是 x264，而是 `h264_rkmpp` |
| ZLMediaKit | 接收 RTMP 并分发多协议视频流 |
