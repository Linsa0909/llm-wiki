---
title: FFmpeg
type: concept
summary: 在 RK3588 平台（Mino17）上，通过 C++ 程序直接调用 FFmpeg/libav 库 API，从 V4L2 摄像头采集 UYVY 格式视频，经 h264_rkmpp 硬件编码后以 RTMP 推流到 ZLMediaKit 流媒体服务器的技术实现与配置积累。
created_at: 20260722-104237
tags:
  - FFmpeg
  - libav
  - V4L2
  - h264_rkmpp
  - RK3588
  - Mino17
  - RTMP
  - ZLMediaKit
sources:
  - raw/merged/20260722-104237/知识整合-FFmpeg.md
  - raw/merged/20260722-104237/Docker.md
---
# FFmpeg

本文整理在 RK3588 平台（Mino17 红外相机设备）上，将原先基于 `ffmpeg` 命令行的采集推流流程，改造为 **C++ 直接调用 FFmpeg/libav 库 API** 的方式。核心技术包括：V4L2 摄像头设备识别与采集、`h264_rkmpp` 硬件编码、RTMP 推流到 ZLMediaKit，以及编译配置与常见问题排错。内容适合作为同类项目开发与维护的参考沉淀。

## 项目背景与数据流概要

- **输入**：Mino17 红外相机，通过 V4L2 驱动输出 `/dev/video59`（设备路径因板子而异），原始格式 `640x518 UYVY`，帧率 `50fps`。
- **画面裁剪**：底部 6 行为机芯冗余观测数据，有效画面裁剪为 `640x512`。
- **伪彩与格式转换**：CPU 路径完成伪彩处理，并使用 `libswscale` 将像素格式转换为 NV12（或 RGB24 -> NV12）。
- **硬件编码**：使用 `h264_rkmpp` 编码器（基于 Rockchip MPP），输出 H264 码流，分辨率 `640x512`，帧率 `50fps`，码率约 `500 kbps`。
- **推流地址**：`rtmp://127.0.0.1:1935/ghostapp/uav0`（容器内部指向 ZLMediaKit）。
- **分发**：ZLMediaKit 接收 RTMP 后，可分发 RTMP、HTTP-FLV、HLS、RTSP 等多种协议。

**核心变化**：正式链路不再执行 `ffmpeg` 命令；而是 C++ 程序链接 FFmpeg/libav 库，直接调用 API 完成采集、编码和推流。

## V4L2 设备识别与摄像头确认

在 RK3588 上，摄像头通过 V4L2 框架映射为 `/dev/videoX` 设备文件。识别步骤：

- 列出所有设备：`v4l2-ctl --list-devices`
- 查看指定设备详情（格式、帧率）：`v4l2-ctl -d /dev/video59 --all`

在当前 Mino17 项目中，红外主画面为 `/dev/video59`，另一设备 `/dev/video60` 为 metadata capture 通道，非画面。

注意事项：
- 设备路径因板子枚举顺序可能变化，部署时需通过以上命令确认。
- 通过环境变量 `CAMERA_DEVICE` 可指定设备路径。

## FFmpeg/libav API 调用链

C++ 程序严格按照以下核心流程调用 FFmpeg 库（省略错误处理）:

```cpp
avdevice_register_all();                          // 注册设备

// 1. 打开 V4L2 输入
v4l2_fmt = av_find_input_format("v4l2");
avformat_open_input(&input_ctx, camera_dev, v4l2_fmt, nullptr);

// 2. 解码取帧
avcodec_send_packet(dec_ctx, packet);
avcodec_receive_frame(dec_ctx, dec_frame);

// 3. 图像处理（裁剪、伪彩、格式转换）
sws_scale(sws_ctx, dec_frame->data, dec_frame->linesize,
          0, dec_frame->height, enc_frame->data, enc_frame->linesize);

// 4. 硬件编码
encoder = avcodec_find_encoder_by_name("h264_rkmpp");
avcodec_open2(enc_ctx, encoder, nullptr);

// 5. 封装与推流
avformat_alloc_output_context2(&output_ctx, NULL, "flv", rtmp_url);
avio_open(&output_ctx->pb, rtmp_url, AVIO_FLAG_WRITE);
avformat_write_header(output_ctx, nullptr);
av_interleaved_write_frame(output_ctx, &pkt);
```

重点库：
| 库 | 作用 |
|---|---|
| `libavdevice` | 打开 V4L2 摄像头设备 |
| `libavformat` | 输入/输出封装，RTMP/FLV 推流 |
| `libavcodec` | 编解码（包括查找编码器 `h264_rkmpp`） |
| `libavutil` | 基础结构、错误处理、硬件上下文 |
| `libswscale` | 像素格式转换（如 UYVY -> NV12） |

## h264_rkmpp 硬件编码

- 编码器名称：`h264_rkmpp`
- 硬件基础：Rockchip MPP (Media Process Platform) 在 RK3588 上的实现。
- 使用方式：`avcodec_find_encoder_by_name("h264_rkmpp")`，然后设置 `enc_ctx` 参数（宽高、码率、帧率、time_base 等）。
- 日志验证：程序启动时应输出 `OK: rkmpp hardware device initialized.` 和 `OK: encoder opened: h264_rkmpp, 640x512, 500 kbps.`
- 注意：当前项目中 RGA 加速图像处理未启用（CPU 路径优先保证画面一致），但硬件编码已正常使用。

## RTMP 推流与 ZLMediaKit

- 推流协议：RTMP，地址 `rtmp://127.0.0.1:1935/ghostapp/uav0`
- ZLMediaKit 以 Docker 容器运行，监听 `1935` 端口（RTMP），并分发多协议：
  - RTMP: `rtmp://<板子IP>:1935/ghostapp/uav0`
  - HTTP-FLV: `http://<板子IP>:8090/ghostapp/uav0.live.flv`
  - HLS: `http://<板子IP>:8090/ghostapp/uav0/hls.m3u8`
  - RTSP: `rtsp://<板子IP>:8554/ghostapp/uav0`
- 播放验证建议：`ffplay rtmp://<板子IP>:1935/ghostapp/uav0`

## 编译与运行时依赖配置

### pkg-config 路径

FFmpeg 库位于 `ffmpeg-rockchip-bin` 目录下（RK3588 定制版），编译时必须设置 `PKG_CONFIG_PATH` 指向其 `lib/pkgconfig`：

```bash
export PKG_CONFIG_PATH=/path/to/ffmpeg-rockchip-bin/lib/pkgconfig:$PKG_CONFIG_PATH
```

### Makefile 链接库

必需链接的库（`-l` 顺序参考）：
```
libavdevice libavformat libavcodec libavutil libswscale libswresample librga
```

其中 `libswresample` 和 `librga` 是 FFmpeg 运行时依赖（音频重采样和 RGA 加速），即使当前链路未主动使用也需链接，否则运行时可能缺失符号。

### Docker 环境

最终部署以 Docker 镜像形式交付，需确保：
- 基础镜像：Ubuntu 22.04 ARM64
- 包含 `ffmpeg-rockchip-bin`、ZLMediaKit 镜像、以及编译好的采集程序。
- Dockerfile 中显式安装运行时依赖（如 `libswresample`、`librga`、`libx264` 等）。

## 常见问题与排错

| 现象 | 可能原因 | 解决 |
|---|---|---|
| `fatal error: libavcodec/avcodec.h: No such file or directory` | 头文件路径未包含或 `PKG_CONFIG_PATH` 未指向定制 FFmpeg | 设置正确的 `PKG_CONFIG_PATH`；安装完整 dev 包 |
| `No package 'libavcodec' found` | `pkg-config` 找不到 `.pc` 文件 | 同上一行 |
| `v4l2 input format not found` | 缺少 `libavdevice` 或运行时未加载 | 编译时链接 `-lavdevice`；运行时确保 `libavdevice.so` 存在 |
| 编译报 `goto cleanup` 错误 | C++ 不允许跳过局部变量初始化 | 将变量声明提前，避免 `goto` 跨过初始化 |
| 链接缺 `librga` 或 `libswresample` | Makefile 未包含这些库 | 在链接行添加 `-lswresample -lrga` |
| GLIBC 版本不兼容 | 外部库构建环境与板子 glibc 版本不匹配 | 在 Ubuntu 22.04 ARM64 Docker 内构建和运行 |
| ZLM API 查不到流 | 端口映射或 secret 配置不一致 | 固定 ZLM config，确保宿主机端口映射与 config.ini 一致 |
| Shell 脚本 Linux 执行失败 | Windows 换行符 CRLF 或 BOM | 转换为 UTF-8 无 BOM + LF |
| `view.sh` 自动识别 IP 不准确 | 默认使用 `127.0.0.1` | 设置环境变量 `VIEW_HOST` 手动指定板子 IP |

## 关键命令

- **摄像头识别**
  ```bash
  v4l2-ctl --list-devices
  v4l2-ctl -d /dev/video59 --all
  ```

- **部署与启动**（以 `Mino17.tar.gz` 为例）
  ```bash
  tar -xzf Mino17.tar.gz
  cd Mino17_release
  chmod +x *.sh scripts/*.sh docker/*.sh
  ./install.sh
  ```

- **运行状态检查**
  ```bash
  ./status.sh                # 中文摘要
  ./status.sh --raw          # 原始 JSON
  ./status.sh --logs         # 详细日志
  ```

- **播放画面**
  ```bash
  ./view.sh
  ffplay rtmp://<板子IP>:1935/ghostapp/uav0
  # 或手动指定 IP
  VIEW_HOST=172.16.3.80 ./view.sh
  ```

- **容器日志**（调试用）
  ```bash
  docker logs <采集容器名>
  ```

## 日志验证要点

程序启动日志应包含以下关键行，确认各环节成功：

```
OK: rkmpp hardware device initialized.
OK: camera opened: /dev/video59
OK: encoder opened: h264_rkmpp, 640x512, 500 kbps.
OK: start push -> rtmp://127.0.0.1:1935/ghostapp/uav0
```

## Backup

以下内容与中心主题间接相关，但可能用于项目后续维护或环境搭建。

- **Docker 安装（WSL2 Ubuntu 22.04）**：并非 RK3588 项目特有，是为开发环境准备的 Docker 安装流程（包括 systemd 启用、官方源添加、Buildx 安装等）。已单独记录在相关文档中，此处不重复。
- **WSL2 版本确认与切换**：若需在 Windows WSL2 中构建 Docker 镜像，需先确保发行版运行在 WSL2 且 systemd 已启用。具体步骤参考 WSL2 配置文档。
- **部署包目录结构**：`Mino17_release/` 包含 `Dockerfile.arm`, `ffmpeg-rockchip-bin`, `images/zlmediakit-rk3588.tar`, `install.sh`, `run.sh`, `stop.sh`, `status.sh`, `view.sh`, `snapshot.sh`, `record_start.sh`, `record_stop.sh` 等。这些是项目部署脚本，通用性较低，未纳入正文。
- **伪彩与格式转换的 RGA 加速**：文档提到“RGA detected, but disabled for the 50FPS path until pseudo-color is implemented equivalently。”可作为未来优化方向。
- **代码镜像导出**：生产环境建议导出 `infrared-push-arm64_latest.tar` 实现完全离线部署。此步骤已记录但未展开。
- **`libx264` 运行时依赖**：虽主编码器是 `h264_rkmpp`，但 FFmpeg 构建时可能依赖 `libx264` 作为备选或运行时组件，需确保安装。
