# Docker 离线部署

## 本项目打包内容

```text
images/ubuntu_22.04_arm64.tar
images/zlmediakit-rk3588.tar
ffmpeg-rockchip-bin/
Dockerfile.arm
install.sh
status.sh
view.sh
```

## 当前模式

- Ubuntu 基础镜像和 ZLM 镜像随包携带。
- C++ 代码镜像 `infrared-push-arm64:latest` 目前在板子上构建。
- 如需完全离线，可在已跑通板子导出代码镜像：

```bash
./scripts/export_app_image.sh
```

生成：

```text
images/infrared-push-arm64_latest.tar
```