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