---
title: ROS 2 设备集成常用知识：V4L2、rosdep、colcon、sensor_msgs
type: project
summary: 面向 ROS 2 设备集成的常用知识入口，覆盖 V4L2 摄像头验证、rosdep 依赖安装、colcon 工作空间构建和 sensor_msgs 消息类型选择。
tags:
  - ROS 2
  - V4L2
  - rosdep
  - colcon
  - sensor_msgs
  - 设备集成
  - 命令
links:
  - Linux 设备文件与 V4L2
  - V4L2 摄像头验证命令
  - ROS 2 rosdep 依赖安装
  - ROS 2 colcon 工作空间构建
  - ROS 2 sensor_msgs 传感器消息类型
  - ROS 2 常用命令速查与排障
  - Linux Shell
sources:
  - raw/imports/20260717-ros2-v4l2-sensor-msgs/ROS2-V4L2-rosdep-colcon-sensor-msgs.md
---
# ROS 2 设备集成常用知识：V4L2、rosdep、colcon、sensor_msgs

## 适用场景

这是一组设备接入/容器构建/ROS 2 编译前经常会连续用到的知识。典型流程是：

```text
识别摄像头设备 -> 验证 V4L2 格式与帧率 -> 安装 ROS 依赖 -> colcon build -> 选择 sensor_msgs 消息发布数据
```

## 知识节点

- [[Linux 设备文件与 V4L2]]：已有基础概念节点，解释 `/dev/videoX`、设备枚举和 V4L2 能力。
- [[V4L2 摄像头验证命令]]：本次新增命令节点，沉淀 `v4l2-ctl` 枚举格式、设置 MJPG 1080p60 和 mmap 流测试。
- [[ROS 2 rosdep 依赖安装]]：解释 `rosdep install -i --from-path src --rosdistro humble -y` 做了什么。
- [[ROS 2 colcon 工作空间构建]]：解释 `colcon build --symlink-install` 与依赖安装、工作空间 overlay 的关系。
- [[ROS 2 sensor_msgs 传感器消息类型]]：整理常用传感器消息类型及选型。

## 与当前设备集成工作的关系

- 在板子或容器里接入摄像头时，先用 V4L2 命令确认 `/dev/video59`、`/dev/video60` 哪个是真正的 Video Capture 节点。
- 在 ROS 2 工作空间刚拉代码或新加包后，先用 `rosdep install` 补系统依赖，再 `colcon build`。
- 如果要把摄像头、IMU、点云或电池数据接入 ROS 2，优先复用 `sensor_msgs` 标准消息，而不是自定义一套重复消息。
