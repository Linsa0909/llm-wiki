---
title: 知识整合：FFmpeg
type: concept
summary: Ctrl 多选节点后由 AI 合并生成的学习型技术知识库文档。
created_at: 20260722-100009
tags:
  - 合并
  - AI整理
links:
sources:
  - raw/merged/20260722-100009/C++调用FFmpeg库.md
  - raw/merged/20260722-100009/ffmpeg开发库与运行库缺失.md
  - raw/merged/20260722-100009/Mino17部署验收清单.md
  - raw/merged/20260722-100009/2026-07-08_Mino17_RK3588红外采集推流.md
---
# 知识整合：FFmpeg

> 合并来源节点：C++ 调用 FFmpeg 库、FFmpeg 开发库与运行库缺失、Mino17 部署验收清单、libavdevice、libavformat、libavcodec、libswscale、libavutil

> 原文档已归档到：raw/merged/20260722-100009/C++调用FFmpeg库.md、raw/merged/20260722-100009/ffmpeg开发库与运行库缺失.md、raw/merged/20260722-100009/Mino17部署验收清单.md、raw/merged/20260722-100009/2026-07-08_Mino17_RK3588红外采集推流.md

# 技术知识库整合文档

## 0. 中心主题识别

### 0.1 候选中心提示词

| 编号 | 候选中心提示词 | 出现频率/重要性 | 相关资料 | 判断理由 |
|---|---|---|---|---|
| 1 | Mino17 RK3588 红外采集推流 | 极高 | 资料1、2、3、4 | 核心项目名称，所有技术细节均围绕此项目展开 |
| 2 | C++ 调用 FFmpeg 库 | 高 | 资料1、2、4 | 改造后的核心架构，区别于命令行调用 |
| 3 | h264_rkmpp 硬件编码 | 高 | 资料2、3、4 | 针对RK3588平台的特定编码方案 |
| 4 | V4L2 摄像头采集 | 高 | 资料1、3、4 | 输入侧关键技术，与UYVY格式相关 |
| 5 | ZLMediaKit RTMP 推流 | 中高 | 资料3、4 | 推流目的地，虽然重要但更偏向于部署配置 |
| 6 | 部署与验收流程 | 中高 | 资料3、4 | 从开发到线上验证的完整流程 |

### 0.2 最终中心主题

> 本批资料的中心主题是：在RK3588平台（Mino17设备）上，通过C++程序直接调用FFmpeg/libav库API，从V4L2摄像头采集UYVY格式的红外视频，经过裁剪与格式转换后，利用 `h264_rkmpp` 进行硬件编码，最终以RTMP协议推流到ZLMediaKit流媒体服务器的完整技术实现与排错经验整理。

### 0.3 主题边界

| 分类 | 内容范围 |
|---|---|
| 应进入主知识库 | 项目核心架构、FFmpeg API调用链、V4L2设备识别方法、h264_rkmpp硬件编码、部署脚本与验收清单、关键问题与排错记录、核心命令与编译配置。 |
| 可作为补充素材 | 设备识别与播放验证步骤、容器状态检查、view.sh与status.sh脚本的具体实现细节。 |
| 应进入 Backup | `librga`、`libswresample`、`libx264` 等次要依赖的安装与链接细节；项目后续优化方向。 |
| 可删除候选 | 部分重复的报错描述；资料中对其他非核心概念的关联链接（仅保留链接结构）。 |

## 1. 知识库主题

### 1.1 中心主题

RK3588 Mino17 红外采集推流技术实现

### 1.2 知识库定位

**学习型技术知识库**，用于学习、复习、查阅RK3588平台上基于FFmpeg API的V4L2采集、硬件编码与RTMP推流技术，以及相关的配置、排错与验收经验。此文档**不是**项目交付文档，而是用于个人知识重构与后续项目复用的素材。

### 1.3 内容范围

- 从 `ffmpeg` 命令行调用迁移到 C++ 调用 FFmpeg/libav 库 API 的核心思想
- 在RK3588上调用 `libavdevice`、`libavformat`、`libavcodec`、`libavutil`、`libswscale` 的具体流程
- 使用 `h264_rkmpp` 编码器进行硬件编码
- V4L2 摄像头设备识别和 `UYVY` 格式处理
- 单路RTMP推流到ZLMediaKit
- 针对Mino17平台的部署、验收、排错与调试。

## 2. 核心知识摘要

- **项目核心改造**：成功将传统的 `ffmpeg` 命令行采集推流流程，改造为由C++程序直接调用 **FFmpeg/libav 库 API** 的方式。
- **FFmpeg/lidav库调用链**：C++程序严格遵循 `av_find_input_format(“v4l2”) → avformat_open_input() → avcodec_send_packet() → avcodec_receive_frame() → sws_scale() → avcodec_find_encoder_by_name(“h264_rkmpp”) → av_interleaved_write_frame()` 的核心流程。
- **V4L2设备识别**：使用 `v4l2-ctl --list-devices` 和 `v4l2-ctl -d /dev/videoX --all` 命令识别摄像头。Mino17设备的红外主画面通常是 `/dev/video59`，另一个是 `/dev/video60` (metadata capture)。
- **输入与输出**：输入为 `640x518 UYVY 50fps`，输出为 `640x512 H264` at `500 kbps`，编码后推流到 `rtmp://127.0.0.1:1935/ghostapp/uav0`。
- **硬件编码器**：使用 `h264_rkmpp` 编码器，利用RK3588的MPP硬件能力。
- **流媒体分发**：ZLMediaKit接收RTMP推流后，可分发RTMP、HTTP-FLV、HLS、RTSP等多种协议。
- **关键命令沉淀**：
  - 部署命令：`tar -xzf Mino17.tar.gz && cd Mino17_release && chmod +x *.sh scripts/*.sh docker/*.sh && ./install.sh`
  - 状态检查：`./status.sh` (摘要模式)，`./status.sh --raw` (原始JSON)，`./status.sh --logs` (详细日志)
  - 画面查看：`./view.sh` (内部自动识别板子IP)，`ffplay rtmp://<板子IP>:1935/ghostapp/uav0`
- **编译与依赖**：需要设置 `PKG_CONFIG_PATH` 指向 `ffmpeg-rockchip-bin/lib/pkgconfig`。Makefile 需链接 `libavdevice libavcodec libavformat libavutil libswscale libswresample librga`。

## 3. 知识点分类索引

### 3.1 基础概念

| 知识点 | 解释 | 备注/来源 |
|---|---|---|
| Linux摄像头（V4L2） | 在Linux中，摄像头不是软件对象，而是 `/dev/videoX` 设备文件。通过V4L2框架访问。 | 资料4 |
| FFmpeg 库 vs. 命令 | `ffmpeg` 本身包含命令行工具和可被 C/C++ 调用的库（如 `libavcodec`）。本项目的核心是调用库，而非生成子进程执行命令。 | 资料1 |
| h264_rkmpp | RK3588平台专用的H.264硬件编码器实现，基于Rockchip的MPP。 | 资料4 |
| ZLMediaKit | 流媒体服务器，接收RTMP推流，并分发各大流协议。 | 资料4 |
| UYVY | 一种视频像素格式，常用于摄像头输出。 | 资料4 |
| Metadata Capture | 某些摄像头会提供额外的元数据通道（如 `/dev/video60`），区别干主画面通道（`/dev/video59`）。 | 资料4 |

### 3.2 常用命令

| 命令 | 用途 | 使用场景 | 注意事项 |
|---|---|---|---|
| `v4l2-ctl --list-devices` | 列出系统所有 V4L2 设备 | 首次部署或连接新摄像头时，用于确认设备路径。 | 无 |
| `v4l2-ctl -d /dev/video59 --all` | 查看特定设备的详细信息（格式、帧率） | 验证摄像头驱动是否正常，确定输入格式。 | 需将设备路径替换为实际路径 |
| `ffplay rtmp://<IP>:1935/ghostapp/uav0` | 使用 ffplay 播放 RTMP 流 | 验证推流服务是否正常，检查画面质量。 | 需将 `<IP>` 替换为实际板子IP地址 |
| `./status.sh` | 检查容器与流状态 | 运行环境运行 | 提供摘要模式；`--raw` 输出JSON；`--logs` 提供详细日志 |
| `./view.sh` | 查看摄像头画面 | 简单验证采集与编码是否连通 | 内部自动识别IP；可通过 `VIEW_HOST` 环境变量指定IP |

### 3.3 配置项

| 配置项 | 含义 | 示例 | 注意事项 |
|---|---|---|---|
| `CAMERA_DEVICE` | 摄像头设备路径 | `/dev/video59` | 因板子而异，需通过 `v4l2-ctl` 确认 |
| `h264_rkmpp` | 硬件编码器名称 | 作为 `avcodec_find_encoder_by_name` 的参数 | 需确保 FFmpeg 编译时启用 rkmpp |
| `rtmp://127.0.0.1:1935/ghostapp/uav0` | RTMP推流地址 | ZLM的流密钥为`ghostapp/uav0` | 需要时，可修改应用和流名称 |
| `8090:80` (端口映射) | ZLMediaKit的HTTP端口映射 | 用于访问ZLM API | 需确保secret一致 |

### 3.4 协议/API/接口

| 名称/字段 | 类型 | 含义 | 示例/取值 | 备注 |
|---|---|---|---|---|
| `av_find_input_format(“v4l2”)` | FFmpeg API | 查找V4L2输入格式 | `“v4l2”` | 用于打开摄像头输入 |
| `avformat_open_input()` | FFmpeg API | 打开输入流 | 包含设备路径 | 整个API调用的入口 |
| `avcodec_find_encoder_by_name(“h264_rkmpp”)` | FFmpeg API | 查找编码器 | `“h264_rkmpp”` | 使用RK3588硬件编码器 |
| `avcodec_send_packet()` / `avcodec_receive_frame()` | FFmpeg API | 解码/编码的输入/输出队列操作 | - | 核心编解码接口（新） |
| `sws_scale()` | FFmpeg API (libswscale) | 执行像素格式转换 | 如 UYVY -> NV12 | 转换成像中间步骤，为编码做准备 |
| RTMP | 协议 | 实时消息协议 | `rtmp://...` | 推流到ZLM的协议 |

### 3.5 SDK/依赖/工具

| 名称 | 类型 | 用途 | 安装/使用方式 | 备注 |
|---|---|---|---|---|
| `libavdevice` | FFmpeg 库 | 打开V4L2摄像头输入 | 编译时 `-lavdevice` | 核心库之一 |
| `libavformat` | FFmpeg 库 | 输入/输出封装，RTMP/FLV推流 | 编译时 `-lavformat` | 核心库之一 |
| `libavcodec` | FFmpeg 库 | 解码、编码 | 编译时 `-lavcodec` | 核心库之一 |
| `libavutil` | FFmpeg 库 | 基础结构、错误处理、硬件上下文 | 编译时 `-lavutil` | 核心库之一 |
| `libswscale` | FFmpeg 库 | 图像缩放与像素格式转换 | 编译时 `-lswscale` | 核心库之一 |
| `libswresample` | FFmpeg 库 | 音频重采样（本项目未使用） | 编译时 `-lswresample` | 避免链接错误，建议纳入 |
| `librga` | Rockchip库 | RGA硬件加速单元 | 编译时 `-lrga` （待确认） | 资料中提到，但当前未确定是否正式使用 |
| ZLMediaKit | 流媒体服务器 | 接收并分发RTMP流 | 部署包中已内置 | 以容器形式运行 |
| `ffmpeg-rockchip-bin` | 工具包 | 专为Rockchip平台定制的FFmpeg二进制与开发文件 | 包含 `lib/pkgconfig` 路径 | 用于定位 `.prc` 文件 |

### 3.6 操作流程/步骤

**1. 部署与配置流程**

1.  **环境准备**：
    -   确认板子系统为 **Ubuntu 22.04 ARM64**。
    -   确保具备Docker运行环境。
2.  **设备识别**：
    -   执行 `v4l2-ctl --list-devices`，确认Mino17摄像头映射为 `/dev/video59` (主画面)。
    -   执行 `v4l2-ctl -d /dev/video59 --all`，确认支持分辨率为 `640x518`，格式为 `UYVY`，帧率为 `50fps`。
3.  **部署程序**：
    -   将 `Mino17.tar.gz` 解压到目标设备。
    -   进入 `Mino17_release` 目录，给脚本添加执行权限：`chmod +x *.sh scripts/*.sh docker/*.sh`。
    -   执行 `./install.sh` 完成安装（可能包含ZLM容器启动、采集程序启动等）。
4.  **启动容器**：
    -   确保 **采集容器** 和 **ZLM容器** 均处于 running 状态（通过 `./status.sh` 验证）。

**2. 验证与验收流程**

1.  **状态检查**：
    -   执行 `./status.sh`，预期输出摘要信息，包括：
        -   采集容器运行：`running`
        -   ZLM容器运行：`running`
        -   流状态：`在线`
        -   H264编码：`640x512` @ `50fps`
2.  **关键日志验证**：
    -   检查程序日志是否包含以下所有关键成功信息：
        -   `OK: rkmpp hardware device initialized.`
        -   `OK: camera opened: /dev/video59`
        -   `OK: encoder opened: h264_rkmpp, 640x512, 500 kbps.`
        -   `OK: start push -> rtmp://127.0.0.1:1935/ghostapp/uav0`
3.  **播放验证**：
    -   在同一个局域网内的其他设备（或本机）执行 `ffplay rtmp://<板子IP>:1935/ghostapp/uav0`，确认能正常看到摄像头画面。
    -   `./view.sh` 脚本也可自动拉流。

### 3.7 常见问题与排错

| 问题/报错 | 可能原因 | 解决方式 | 备注 |
|---|---|---|---|
| `fatal error: libavcodec/avcodec.h: No such file or directory` | 缺少开发包或 `PKG_CONFIG_PATH` 配置错误。 | 1. 安装完整的 `dev` 包。2. 将 `PKG_CONFIG_PATH` 指向 `ffmpeg-rockchip-bin/lib/pkgconfig` 目录。 | 主要与编译环境有关 |
| `No package 'libavcodec' found` | `pkg-config` 找不到库的 `.prc` 文件。 | 参考上一条。 | - |
| `v4l2 input format not found` | 缺少 `libavdevice` 或运行时缺少此模块。 | 1. 编译时确保链接 `-lavdevice`。2. Dockerfile / 运行环境中安装完整依赖。 | - |
| 编译时报 `goto cleanup` 错误 | C++ 不支持跳过局部
