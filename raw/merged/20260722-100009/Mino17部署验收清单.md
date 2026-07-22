# Mino17 部署验收清单

## 设备识别

```bash
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video59 --all
```

预期：

```text
Mino17
/dev/video59
640x518 UYVY
50fps
```

## 容器状态

```bash
./status.sh
```

预期：

```text
采集容器 running
ZLM 容器 running
流状态 在线
H264 / 640x512 / 50fps
```

## 播放验证

```bash
./view.sh
ffplay rtmp://<板子IP>:1935/ghostapp/uav0
```

## 关键日志

```text
OK: rkmpp hardware device initialized.
OK: camera opened: /dev/video59
OK: encoder opened: h264_rkmpp, 640x512, 500 kbps.
OK: start push -> rtmp://127.0.0.1:1935/ghostapp/uav0
```