# Linux 设备文件与 V4L2

## 宏观理解

Linux 下摄像头会被识别成 `/dev/videoX` 这类设备文件。程序不是“找到摄像头名字”就能工作，而是要打开正确的设备节点。

## 常用命令

```bash
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video59 --all
v4l2-ctl -d /dev/video59 --list-formats-ext
```

## 本项目经验

Mino17 在新板子上识别为：

```text
/dev/video59  主视频采集，640x518 UYVY
/dev/video60  metadata capture，不是主画面
```

所以运行时使用：

```bash
CAMERA_DEVICE=/dev/video59 ./install.sh
```

## v4l2-ctl 验证命令补充

本次新增了 [[V4L2 摄像头验证命令]] 节点，用于沉淀多 video 节点枚举、格式/帧率查看，以及指定 `MJPG 2080x1080 60fps` 的 mmap 出流测试。

关键命令：

```bash
v4l2-ctl -D -d /dev/video59
v4l2-ctl --list-formats-ext -d /dev/video59
v4l2-ctl -d /dev/video59 --set-fmt-video=width=2080,height=1080,pixelformat=MJPG --set-parm=60 --stream-mmap=4 --stream-count=300 --stream-to=/dev/null --verbose
```

