# FFmpeg 开发库与运行库缺失

## 现象

```text
No package 'libavcodec' found
fatal error: libavcodec/avcodec.h: No such file or directory
v4l2 input format not found
```

## 原因

- `PKG_CONFIG_PATH` 没指向定制 FFmpeg。
- 缺少 `libavdevice`。
- 容器内运行库不完整。

## 解决

- 使用 `ffmpeg-rockchip-bin/lib/pkgconfig`。
- Makefile 链接 `libavdevice libavcodec libavformat libavutil libswscale libswresample librga`。
- Dockerfile 显式安装运行时依赖。