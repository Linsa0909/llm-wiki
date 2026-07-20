---
title: ROS 2 rosdep 依赖安装
type: tool
summary: rosdep install 会扫描工作空间 src 下的 package.xml，自动安装缺失的系统依赖，是 colcon build 前的重要准备步骤。
tags:
  - ROS 2
  - rosdep
  - Humble
  - package.xml
  - dependency
  - apt
links:
  - ROS 2 colcon 工作空间构建
  - ROS 2 常用命令速查与排障
  - ROS 2 设备集成常用知识：V4L2、rosdep、colcon、sensor_msgs
  - Linux Shell
sources:
  - raw/imports/20260717-ros2-v4l2-sensor-msgs/ROS2-V4L2-rosdep-colcon-sensor-msgs.md
---
# ROS 2 rosdep 依赖安装

## 命令

```bash
rosdep install -i --from-path src --rosdistro humble -y
```

## 参数拆解

| 部分 | 含义 |
|---|---|
| `rosdep install` | 自动安装 ROS 包声明的系统依赖 |
| `-i` | 忽略已安装的依赖 |
| `--from-path src` | 扫描当前工作空间 `src/` 目录下的所有包 |
| `--rosdistro humble` | 指定 ROS 2 发行版为 Humble |
| `-y` | 安装过程中自动确认 yes |

## 具体做了什么

```text
扫描 src/ 下所有 package.xml
  -> 找到 <depend>、<build_depend>、<exec_depend> 等依赖
  -> 检查系统是否已安装
  -> 对缺失依赖执行 apt install
```

## 什么时候用

刚拉完工作空间代码、新加了 ROS 包、或者容器环境是干净环境时使用：

```bash
cd /workspace/yunshu
rosdep install -i --from-path src --rosdistro humble -y
colcon build --symlink-install
```

## 与当前 hal_dev 容器的关系

如果在容器内的 `hal_dev` 工作空间中刚加新代码或新包，需要先跑 `rosdep install` 补齐系统依赖，再执行 `colcon build`。否则 colcon 可能在 CMake configure、编译或链接阶段因为缺库失败。
