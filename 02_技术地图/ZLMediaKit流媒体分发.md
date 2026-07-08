# ZLMediaKit 流媒体分发

## 宏观理解

C++ 程序只负责把 H264 RTMP 流推到 ZLMediaKit。ZLMediaKit 负责把同一路流转成多种播放协议。

## 本项目端口

```text
RTMP: 1935
HTTP API / HTTP-FLV / HLS: 8090 -> container 80
RTSP: 8554 -> container 554
```

## 播放协议区别

| 协议 | 用途 |
|---|---|
| RTMP | 延迟低，推荐实时预览，适合 ffplay/VLC |
| HTTP-FLV | 延迟较低，适合 Web 播放器 |
| HLS | 兼容性好，但延迟高 |
| RTSP | 适合监控、NVR、部分播放器 |

## 常用验证

```bash
curl "http://127.0.0.1:8090/index/api/getMediaList?secret=OCdMstJ9V4XmUvELLo7Vn7DLgmHPu9co"
ffplay rtmp://<板子IP>:1935/ghostapp/uav0
```