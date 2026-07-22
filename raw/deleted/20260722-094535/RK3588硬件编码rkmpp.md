# RK3588 硬件编码 rkmpp

## 是什么

`rkmpp` 是 Rockchip MPP 的 FFmpeg 编码/解码接口。在 RK3588 上，使用 `h264_rkmpp` 可以把 H264 编码放到硬件单元执行，降低 CPU 压力。

## 本项目证据

代码中：

```cpp
avcodec_find_encoder_by_name("h264_rkmpp");
```

运行日志中：

```text
OK: rkmpp hardware device initialized.
OK: encoder opened: h264_rkmpp, 640x512, 500 kbps.
INFO: hardware encode path remains enabled.
```

## 当前边界

- 硬件编码满足。
- RGA 图像处理加速检测到，但 50fps 主链路暂未启用。
- 当前裁剪、伪彩、NV12 转换主要走 CPU，优先保证画面效果一致。