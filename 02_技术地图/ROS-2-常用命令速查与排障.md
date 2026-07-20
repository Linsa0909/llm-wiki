---
title: ROS 2 常用命令速查与排障
type: note
summary: 每个新终端都要先加载 ROS 2 基础环境。若还要使用自己的工作空间，应先加载基础环境，再加载工作空间覆盖层：
tags:
  - ROS 2
  - 命令速查
  - 调试
  - colcon
  - rosbag
  - DDS
links:
  - ROS 2
  - DDS
  - colcon
  - rosbag
sources:
  - raw/imports/20260714-202751/ROS2-常用命令速查与排障.md
---
# ROS 2 常用命令速查与排障

## 导入来源：ROS2-常用命令速查与排障.md

# ROS 2 常用命令速查与排障

> 适用场景：ROS 2 Humble/Jazzy 日常开发、节点联调、话题/服务/动作检查、参数调试和 rosbag 录放。
>
> 约定：`<package_name>`、`<executable_name>`、`<launch_file>` 是占位符，使用时替换为真实名称；示例命令默认在 Bash/WSL/Linux 终端执行。

## 1. 环境与工作空间

每个新终端都要先加载 ROS 2 基础环境。若还要使用自己的工作空间，应先加载基础环境，再加载工作空间覆盖层：

```bash
# 1) 加载系统安装的 ROS 2（发行版按实际环境替换）
source /opt/ros/humble/setup.bash

# 2) 加载自己的工作空间（完成过 colcon build 后才会存在）
source ~/ros2_ws/install/setup.bash

# 确认当前发行版和环境变量
echo "$ROS_DISTRO"
printenv | grep '^ROS'
```

建议把固定环境写入 `~/.bashrc`，但如果机器上同时安装多个 ROS 2 发行版，最好继续手动 `source`，避免环境混用。

快速自检：

```bash
which ros2
ros2 --help
ros2 doctor --report
```

## 2. 功能包创建与查询

```bash
# 创建 C++ 包
ros2 pkg create my_pkg \
  --build-type ament_cmake \
  --dependencies rclcpp std_msgs

# 创建 Python 包
ros2 pkg create my_pkg \
  --build-type ament_python \
  --dependencies rclpy

# 列出所有可见的包
ros2 pkg list

# 查找指定包
ros2 pkg list | grep '^tf2$'

# 查看包的 package.xml
ros2 pkg xml my_pkg

# 查看包安装前缀；找不到包时很有用
ros2 pkg prefix my_pkg
```

## 3. 编译工作空间

在工作空间根目录（例如 `~/ros2_ws`）执行：

```bash
# 编译全部包
colcon build

# 只编译指定包
colcon build --packages-select my_pkg

# 建立符号链接；Python/资源文件修改后通常无需重复复制
colcon build --symlink-install

# Release 模式
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# 显示更直接的构建日志
colcon build --event-handlers console_direct+
```

编译后必须重新加载覆盖层：

```bash
source install/setup.bash
```

常见清理重编译（确认当前目录确实是目标工作空间后再执行）：

```bash
rm -rf build/ install/ log/
colcon build --symlink-install
source install/setup.bash
```

## 4. 运行节点与 Launch

```bash
# 运行单个节点
ros2 run <package_name> <executable_name>
ros2 run turtlesim turtlesim_node

# 用 launch 文件启动一个或多个节点
ros2 launch <package_name> <launch_file>
ros2 launch turtlesim multisim.launch.py

# 查看包内可执行程序
ros2 pkg executables <package_name>
```

## 5. 节点检查

```bash
# 列出运行中的节点
ros2 node list

# 查看节点的发布者、订阅者、服务和动作
ros2 node info /turtlesim
```

如果节点未出现，优先检查：进程是否存活、终端是否加载了同一 ROS 环境、`ROS_DOMAIN_ID` 是否一致、DDS 网络是否被防火墙或容器隔离。

## 6. 话题（Topic）

```bash
# 列出话题；-t 同时显示类型
ros2 topic list
ros2 topic list -t

# 查看话题详情
ros2 topic info /turtle1/cmd_vel
ros2 topic info /turtle1/cmd_vel --verbose

# 查看数据、频率和带宽
ros2 topic echo /turtle1/pose
ros2 topic hz /turtle1/pose
ros2 topic bw /turtle1/pose

# 发布一条消息（--once 可省略；不加时默认持续发布）
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"

# 以 10 Hz 持续发布
ros2 topic pub --rate 10 /turtle1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"

# 查看消息定义
ros2 interface show geometry_msgs/msg/Twist
```

## 7. 服务（Service）

```bash
# 列出服务，或同时显示类型
ros2 service list
ros2 service list -t

# 查看服务类型和详情
ros2 service type /spawn
ros2 service info /spawn

# 调用服务
ros2 service call /spawn turtlesim/srv/Spawn \
  "{x: 5.0, y: 5.0, theta: 0.0, name: 'turtle2'}"

# 查看服务接口定义
ros2 interface show turtlesim/srv/Spawn
```

## 8. 动作（Action）

```bash
# 列出动作并显示类型
ros2 action list
ros2 action list -t

# 查看动作详情
ros2 action info /navigate_to_pose

# 发送动作目标并显示反馈
ros2 action send_goal --feedback \
  /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 2.0, z: 0.0}, orientation: {w: 1.0}}}}"

# 查看动作接口定义
ros2 interface show nav2_msgs/action/NavigateToPose
```

## 9. 参数（Parameter）

```bash
# 查看节点参数
ros2 param list
ros2 param list /turtlesim

# 读取和设置参数
ros2 param get /turtlesim background_r
ros2 param set /turtlesim background_r 150

# 保存和加载参数
ros2 param dump /turtlesim > turtle.yaml
ros2 param load /turtlesim turtle.yaml

# 带参数启动节点
ros2 run turtlesim turtlesim_node --ros-args \
  -p background_r:=255 \
  -p background_g:=100 \
  -p background_b:=50
```

参数能否在运行时修改，取决于节点是否声明该参数并接受新的参数值。

## 10. rosbag 录制与回放

```bash
# 录制全部话题
ros2 bag record -a

# 录制指定话题并指定输出目录
ros2 bag record -o my_bag /turtle1/pose /turtle1/cmd_vel

# 查看 bag 信息
ros2 bag info my_bag

# 正常、倍速和循环回放
ros2 bag play my_bag
ros2 bag play my_bag --rate 0.5
ros2 bag play my_bag --loop
```

录制前建议先执行 `ros2 topic hz` 和 `ros2 topic bw`，评估数据频率、带宽和磁盘空间。

## 11. 接口定义查询

ROS 2 接口名称必须写成：

- 消息：`包名/msg/类型`
- 服务：`包名/srv/类型`
- 动作：`包名/action/类型`

```bash
# 所有可见接口
ros2 interface list

# 查看具体接口
ros2 interface show geometry_msgs/msg/Twist
ros2 interface show sensor_msgs/msg/Image
ros2 interface show turtlesim/srv/Spawn
ros2 interface show nav2_msgs/action/NavigateToPose

# 查看某个接口包提供的全部接口
ros2 interface package sensor_msgs

# 根据字段结构查找接口
ros2 interface find "std_msgs/Header header"
```

## 12. 诊断与可视化

```bash
# 检查 ROS 2 环境和系统状态
ros2 doctor
ros2 doctor --report

# 以 debug 日志级别运行节点
ros2 run my_pkg my_node --ros-args --log-level debug

# 节点通信图、图像查看和 3D 可视化
rqt_graph
rqt_image_view
rviz2
```

## 13. 常用组合

```bash
# 从话题输出中筛选坐标字段
ros2 topic echo /turtle1/pose | grep -E '^x:|^y:'

# 录制所有话题到指定目录
ros2 bag record -a -o bags/experiment_1

# 先列出话题及类型，再检查指定话题频率
ros2 topic list -t
ros2 topic hz /turtle1/pose

# 带 launch 参数启动
ros2 launch my_pkg my_launch.py \
  rtmp_url:=rtmp://127.0.0.1:1935/live/uav0 \
  enable_pseudo_color:=true
```

## 14. 故障定位顺序

当“节点看不到、话题没数据、包找不到”时，按下面顺序排查：

1. `echo $ROS_DISTRO`：确认已加载 ROS 2 环境。
2. `echo $ROS_DOMAIN_ID`：确认通信双方处于同一 Domain；未设置时通常为默认值 0。
3. `ros2 pkg prefix <package_name>`：确认包在当前环境中可见。
4. `ros2 node list`：确认节点已经运行并被发现。
5. `ros2 topic list -t`：确认话题名称和消息类型完全匹配。
6. `ros2 topic info <topic> --verbose`：检查发布者、订阅者和 QoS。
7. `ros2 topic echo <topic>`：确认是否真实收到数据。
8. `ros2 doctor --report`：收集环境诊断信息。
9. 若跨主机、容器或 WSL，检查 DDS 发现、组播、防火墙、网络模式和 `ROS_LOCALHOST_ONLY`。

## 15. 易错点

- 只加载工作空间覆盖层但没有先加载对应 ROS 2 基础环境，可能导致依赖不可见。
- 编译后忘记重新执行 `source install/setup.bash`，新包或新可执行程序不会出现在当前终端。
- 把 ROS 1 风格的 `geometry_msgs/Twist` 用在 ROS 2 CLI；ROS 2 应写成 `geometry_msgs/msg/Twist`。
- 节点名、话题名、服务名通常以 `/` 开头，而包名和接口类型不以 `/` 开头。
- 同名话题存在但 QoS 不兼容时，发布者和订阅者仍可能无法通信。
- `--symlink-install` 不能替代所有重编译：C++ 修改、接口生成、依赖或入口配置变化后仍需重新执行 `colcon build`。
