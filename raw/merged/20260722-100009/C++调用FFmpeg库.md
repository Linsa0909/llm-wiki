# C++ 调用 FFmpeg 库

## 宏观理解

`ffmpeg` 既可以是命令行工具，也可以是一组可被 C/C++ 调用的库。本项目不是执行 `ffmpeg` 命令，而是在 C++ 中链接并调用 FFmpeg/libav 库。

## 本项目用到的库

| 库 | 作用 |
|---|---|
| `libavdevice` | 打开 V4L2 摄像头输入 |
| `libavformat` | 输入/输出封装，RTMP/FLV 推流 |
| `libavcodec` | 解码、编码，调用 `h264_rkmpp` |
| `libavutil` | 基础结构、错误处理、硬件上下文 |
| `libswscale` | 像素格式转换，如 RGB24 -> NV12 |

## 调用链

```text
av_find_input_format("v4l2")
  -> avformat_open_input()
  -> avcodec_send_packet()
  -> avcodec_receive_frame()
  -> sws_scale()
  -> avcodec_find_encoder_by_name("h264_rkmpp")
  -> av_interleaved_write_frame()
```

## 重要判断

如果 C++ 里出现 `system("ffmpeg ...")` 或 `popen("ffmpeg ...")`，那仍然是命令调用。本项目正式链路没有这种调用。