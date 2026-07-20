---
title: ROS 2 sensor_msgs 传感器消息类型
type: concept
summary: sensor_msgs 是 ROS 2 标准传感器消息包，覆盖图像、点云、激光雷达、IMU、GNSS、磁力计、关节、电池、摇杆和环境传感器等常用数据。
tags:
  - ROS 2
  - sensor_msgs
  - Image
  - PointCloud2
  - LaserScan
  - Imu
  - NavSatFix
links:
  - ROS 2 设备集成常用知识：V4L2、rosdep、colcon、sensor_msgs
  - ROS 2 常用命令速查与排障
sources:
  - raw/imports/20260717-ros2-v4l2-sensor-msgs/ROS2-V4L2-rosdep-colcon-sensor-msgs.md
---
# ROS 2 sensor_msgs 传感器消息类型

## 是什么

`sensor_msgs` 是 ROS 2 中存放传感器数据消息定义的核心包，位于 `ros2/common_interfaces` 仓库下。设备接入时，如果数据属于常见传感器类型，应优先复用 `sensor_msgs`，不要轻易自定义重复消息。

## 图像类

| 消息 | 说明 |
|---|---|
| `Image` | 未压缩图像，保存原始像素数据 |
| `CompressedImage` | 压缩图像，例如 JPEG/PNG |
| `CameraInfo` | 相机标定参数和元信息 |
| `RegionOfInterest` | 图像中的感兴趣区域 ROI |

## 点云类

| 消息 | 说明 |
|---|---|
| `PointCloud` | 已弃用，Foxy 起建议使用 `PointCloud2` |
| `PointCloud2` | N 维点云集合，每个点可携带法线、强度等字段 |
| `PointField` | `PointCloud2` 中单个字段的名称、类型、偏移量 |
| `ChannelFloat32` | 与 `PointCloud` 中每个点关联的额外数据 |

## 激光雷达与距离

| 消息 | 说明 |
|---|---|
| `LaserScan` | 单回波平面激光雷达扫描 |
| `MultiEchoLaserScan` | 多回波平面激光雷达扫描 |
| `LaserEcho` | `MultiEchoLaserScan` 的子消息，表示单次回波 |
| `Range` | 主动测距传感器单次距离读数，如超声波、红外 |

## IMU 与姿态

| 消息 | 说明 |
|---|---|
| `Imu` | IMU 数据，包括角速度、线加速度和方向 |

## 导航卫星

| 消息 | 说明 |
|---|---|
| `NavSatFix` | GNSS 定位信息，经纬度、海拔等 |
| `NavSatStatus` | GNSS 定位状态，如是否差分/RTK |

## 磁力计

| 消息 | 说明 |
|---|---|
| `MagneticField` | 磁场强度矢量 |

## 关节状态

| 消息 | 说明 |
|---|---|
| `JointState` | 一组关节的位置、速度、力矩 |
| `MultiDOFJointState` | 多自由度关节状态 |

## 电池

| 消息 | 说明 |
|---|---|
| `BatteryState` | 电量、电压、电流、温度等 |

## 摇杆/手柄

| 消息 | 说明 |
|---|---|
| `Joy` | 摇杆轴和按钮状态 |
| `JoyFeedback` | 摇杆反馈，如 LED、震动、蜂鸣器 |
| `JoyFeedbackArray` | `JoyFeedback` 数组 |

## 环境与其他传感器

| 消息 | 说明 |
|---|---|
| `Temperature` | 单次温度读数 |
| `RelativeHumidity` | 单次相对湿度读数 |
| `FluidPressure` | 流体压力，例如大气压 |
| `Illuminance` | 光照度测量 |
| `TimeReference` | 外部时间源的测量时间戳 |

## 选型经验

- 摄像头原始图像优先用 `sensor_msgs/msg/Image`，压缩图像用 `CompressedImage`。
- 点云优先用 `PointCloud2`，不要再新接入 `PointCloud`。
- 激光雷达二维扫描用 `LaserScan`，多回波雷达用 `MultiEchoLaserScan`。
- IMU、GNSS、电池、手柄等都有标准消息时，优先复用标准消息，方便 rviz、rosbag、桥接和下游算法直接消费。
