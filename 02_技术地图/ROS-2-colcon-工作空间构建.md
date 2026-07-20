---
title: ROS 2 colcon 工作空间构建
type: tool
summary: colcon 是 ROS 2 工作空间的构建工具，通常在 rosdep 安装依赖后执行，用于编译 src 下的一个或多个包并生成 install overlay。
tags:
  - ROS 2
  - colcon
  - build
  - workspace
  - symlink-install
  - Humble
links:
  - ROS 2 rosdep 依赖安装
  - ROS 2 常用命令速查与排障
  - ROS 2 设备集成常用知识：V4L2、rosdep、colcon、sensor_msgs
  - Linux Shell
sources:
  - raw/imports/20260717-ros2-v4l2-sensor-msgs/ROS2-V4L2-rosdep-colcon-sensor-msgs.md
---
# ROS 2 colcon 工作空间构建

## 基本命令

```bash
colcon build --symlink-install
```

## 推荐顺序

```bash
cd /workspace/yunshu
source /opt/ros/humble/setup.bash
rosdep install -i --from-path src --rosdistro humble -y
colcon build --symlink-install
source install/setup.bash
```

## 常用参数

| 命令 | 作用 |
|---|---|
| `colcon build` | 构建工作空间内所有包 |
| `colcon build --symlink-install` | Python 文件、launch、配置等以软链接方式安装，便于开发时改文件后少重编 |
| `colcon build --packages-select <pkg>` | 只构建指定包 |
| `colcon build --packages-up-to <pkg>` | 构建指定包及其依赖 |
| `colcon build --cmake-clean-cache` | 清理 CMake 缓存后重新配置 |
| `colcon build --event-handlers console_direct+` | 直接输出构建日志，方便看错误 |

## build 产物

| 目录 | 含义 |
|---|---|
| `build/` | 每个包的中间构建目录 |
| `install/` | 构建后的安装空间，后续通过 `source install/setup.bash` 加载 |
| `log/` | 构建日志 |

## 注意点

- `--symlink-install` 不能替代所有重编译。C++ 源码、接口定义、CMakeLists 或 package.xml 变化后仍然需要重新 build。
- 每个新终端都要先 `source /opt/ros/humble/setup.bash`，构建完成后再 `source install/setup.bash`。
- 如果刚新加包或依赖，先跑 `rosdep install`，再跑 `colcon build`。
