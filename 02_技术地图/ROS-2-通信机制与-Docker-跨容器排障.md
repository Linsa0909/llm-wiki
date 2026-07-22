---
title: ROS 2 通信机制与 Docker 跨容器排障
type: concept
summary: ROS 2 应用通常使用 Topic、Service 和 Action 通信，但实际的发现、序列化和数据传输由 RMW 及其底层中间件完成：
tags:
  - ROS 2
  - RMW
  - DDS
  - Docker
  - 通信
  - ROS_DOMAIN_ID
  - ROS_LOCALHOST_ONLY
  - QoS
  - 排障
links:
  - ROS 2
  - DDS
  - RMW
  - IPC
  - Docker
  - srv
  - Service
  - Topic
  - Action
  - ROS_DOMAIN_ID
  - ROS_LOCALHOST_ONLY
sources:
  - raw/imports/20260722-101655/ROS2-通信机制与Docker跨容器排障.md
importance: high
---
# ROS 2 通信机制与 Docker 跨容器排障

## 导入来源：ROS2-通信机制与Docker跨容器排障.md

# ROS 2 通信机制与 Docker 跨容器排障

> 适用场景：ROS 2 节点运行在宿主机、不同 Docker 容器或不同机器中，出现节点发现不了、Topic 无数据、Service 调用卡住等问题。

## 1. ROS 2 通信链路

ROS 2 应用通常使用 Topic、Service 和 Action 通信，但实际的发现、序列化和数据传输由 RMW 及其底层中间件完成：

```text
ROS 2 应用
Topic / Service / Action / Parameter
                │
                ▼
rclcpp / rclpy（ROS 客户端库）
                │
                ▼
RMW Interface（中间件抽象接口）
                │
                ▼
具体 RMW 实现
rmw_fastrtps_cpp / rmw_cyclonedds_cpp / rmw_zenoh_cpp / ...
                │
                ▼
Fast DDS / Cyclone DDS / Zenoh / 其他中间件
                │
                ▼
UDP、TCP、共享内存或中间件自己的传输机制
```

排查通信问题时，不能只看 ROS 2 服务或话题名称，还要检查环境变量、RMW、中间件配置、Docker 网络和 QoS。

## 2. RMW 是什么

RMW 是 **ROS Middleware Interface**，即 ROS 2 的中间件抽象接口。

它的作用是把 ROS 2 上层统一 API 转换成具体中间件的行为，包括：

- 节点、Topic、Service 等实体的发现；
- 消息序列化和反序列化；
- 发布、订阅和请求—响应传输；
- QoS 配置；
- ROS 图信息维护。

RMW 不是 DDS 的另一个名称。ROS 2 最初主要建立在 DDS/RTPS 之上，但现在也存在基于 Zenoh 等非 DDS 中间件的 RMW 实现。

## 3. 常见 RMW 实现

| RMW 实现 | 底层中间件 | 说明 |
|---|---|---|
| `rmw_fastrtps_cpp` | eProsima Fast DDS | 常见 DDS 实现，功能完整 |
| `rmw_cyclonedds_cpp` | Eclipse Cyclone DDS | 常见 DDS 实现，配置相对简洁 |
| `rmw_connextdds` | RTI Connext DDS | RTI DDS 实现 |
| `rmw_gurumdds_cpp` | GurumDDS | 商业 DDS 实现 |
| `rmw_zenoh_cpp` | Eclipse Zenoh | 非 DDS 的 ROS 2 中间件实现 |

不要笼统地把某一个实现称为“所有 ROS 2 环境的默认 RMW”。默认值取决于 ROS 2 发行版、安装包、构建选项和运行环境。

## 4. 查看和选择 RMW

```bash
# 查看是否显式指定了 RMW
echo "$RMW_IMPLEMENTATION"

# 查看系统安装了哪些 RMW 包
ros2 pkg list | grep '^rmw_'

# 查看 ROS 2 环境报告
ros2 doctor --report
```

如果 `RMW_IMPLEMENTATION` 为空，表示进程将加载当前 ROS 2 安装的默认实现，而不是“没有 RMW”。

显式选择：

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run demo_nodes_cpp talker
```

Docker：

```bash
docker run --rm \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  my_ros_image
```

前提是镜像中已经安装对应实现，否则程序会报告 RMW 实现不存在。

## 5. 两端 RMW 必须一样吗

从标准角度看，一些 DDS 厂商实现可能互操作；但在实际 ROS 2 项目中，不同实现、版本和配置组合可能在发现、ROS 图、QoS、服务请求或共享内存方面表现不同。

排障时的推荐做法是：

1. 先让通信双方使用相同 ROS 2 发行版；
2. 使用相同 RMW 实现；
3. 使用相同 `ROS_DOMAIN_ID`；
4. 确认发现范围和网络配置；
5. 基线通信成功后，再验证跨 RMW 互操作需求。

如果 Service 能在列表中看到，但调用一直停在 `requester: making request`，RMW 或 ROS 2 daemon 不一致是重点检查项之一，但不是唯一原因。

## 6. ROS_DOMAIN_ID

`ROS_DOMAIN_ID` 用来把同一物理网络划分为多个独立的 ROS 2 逻辑域。

```text
Domain 0：节点 A、节点 B 可以互相发现
Domain 7：节点 C、节点 D 可以互相发现
Domain 0 与 Domain 7：默认互相不可见
```

查看：

```bash
echo "$ROS_DOMAIN_ID"
```

设置：

```bash
export ROS_DOMAIN_ID=0
```

Docker：

```bash
docker run --rm -e ROS_DOMAIN_ID=0 my_ros_image
```

未设置时通常使用 Domain 0。通信双方必须使用相同 Domain ID，除非专门部署了 domain bridge。

## 7. ROS_LOCALHOST_ONLY

在 ROS 2 Humble 等版本中，`ROS_LOCALHOST_ONLY` 用于限制通信范围：

| 值 | 含义 |
|---|---|
| `0` 或未启用 | 不限制为 localhost，可参与外部网络发现和通信 |
| `1` | 限制为 localhost 范围，不对局域网其他机器开放 |

```bash
export ROS_LOCALHOST_ONLY=0
```

Docker：

```bash
docker run --rm -e ROS_LOCALHOST_ONLY=0 my_ros_image
```

它更准确的含义是“只允许 localhost 范围通信”，不要简单理解成所有实现都只是绑定一个固定的 `127.0.0.1` Socket；具体落实方式由 RMW/中间件决定。

### 新版 ROS 2 的发现范围

ROS 2 Iron 起，官方逐步使用粒度更细的发现配置，例如：

```bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
```

常见取值：

| 值 | 含义 |
|---|---|
| `SUBNET` | 在可达子网内自动发现 |
| `LOCALHOST` | 只自动发现本机节点 |
| `OFF` | 关闭自动发现 |
| `SYSTEM_DEFAULT` | 使用中间件系统默认设置 |

具体使用哪个变量应以当前 ROS 2 发行版为准。Humble 项目可继续按 `ROS_LOCALHOST_ONLY` 排查。

## 8. Docker 网络模式对 ROS 2 的影响

### 默认 bridge 网络

默认情况下，每个容器拥有独立网络 namespace、独立 IP 和独立 loopback。

```text
容器 A 的 localhost ≠ 容器 B 的 localhost ≠ 宿主机 localhost
```

容器即使可以通过容器 IP 互相访问，DDS 自动发现仍可能受多播、广播、NAT、网卡选择或防火墙影响。

### host 网络

```bash
docker run --network host ...
```

在 Linux Docker Engine 中，host 模式取消容器与宿主机之间的网络 namespace 隔离，容器直接共享宿主机网络栈：

- 容器没有独立容器 IP；
- `-p` 端口映射失去意义；
- DDS 发现通常更直接；
- 网络隔离降低；
- 可能出现端口冲突。

因此不能简单断言：“只要 `ROS_LOCALHOST_ONLY=1`，两个 host-network 容器就必然无法通信。”它们共享宿主机网络栈，是否能在 localhost 范围互通还取决于 RMW 和具体配置。

但如果目标包含其他机器，必须关闭 localhost-only 限制。

## 9. IPC 与普通 DDS 网络通信的区别

```bash
--network host
```

主要处理网络 namespace 和网络发现问题。

```bash
--ipc host
```

主要处理共享内存、信号量和消息队列等 IPC 资源共享问题。

普通 DDS UDP 通信不要求 `--ipc host`。只有明确需要跨容器共享内存传输时，才需要评估 host IPC 或 shareable IPC。

例如 Fast DDS 官方的跨容器 SHM 方案通常同时使用：

```bash
--network host --ipc host
```

不要把 `--ipc host` 当成“ROS 2 服务发现不了”的通用修复项。

## 10. 推荐的同机跨容器基线

服务端容器：

```bash
docker run --rm -it \
  --network host \
  -e ROS_DOMAIN_ID=0 \
  -e ROS_LOCALHOST_ONLY=0 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  my_ros_server_image
```

测试容器：

```bash
docker run --rm -it \
  --network host \
  -e ROS_DOMAIN_ID=0 \
  -e ROS_LOCALHOST_ONLY=0 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  my_ros_test_image bash
```

这是便于排障的同机 Linux 基线，不代表所有生产环境都必须使用 host network。基线成功后，可根据隔离和部署要求改回自定义 bridge、静态发现、Discovery Server、Zenoh 或其他方案。

## 11. 三个关键环境变量

| 变量 | 两端推荐关系 | 不一致时的典型影响 |
|---|---|---|
| `ROS_DOMAIN_ID` | 必须一致 | 处于不同逻辑域，默认无法发现和通信 |
| `ROS_LOCALHOST_ONLY` | 排障阶段都设为 `0` | 发现范围不同，跨机器或独立网络 namespace 通信受限 |
| `RMW_IMPLEMENTATION` | 排障阶段保持一致 | 可能出现发现、QoS、服务或工具行为差异 |

一次性检查：

```bash
env | grep -E '^(ROS_|RMW_)' | sort
```

分别在服务端和客户端执行，并逐项对比。

## 12. ROS 2 daemon 缓存问题

ROS 2 CLI 可能通过后台 daemon 获取 ROS 图信息。切换 Domain ID 或 RMW 后，旧 daemon 可能仍使用之前的配置。

修改环境变量后执行：

```bash
ros2 daemon stop
ros2 daemon start
```

然后重新检查：

```bash
ros2 node list
ros2 topic list -t
ros2 service list -t
```

如果容器是临时测试环境，也可以完全退出并重新创建容器，避免继承旧进程状态。

## 13. 分层排障方法

### 第 1 层：环境是否一致

两端分别执行：

```bash
echo "ROS_DISTRO=$ROS_DISTRO"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}"
echo "ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-0}"
echo "ROS_AUTOMATIC_DISCOVERY_RANGE=$ROS_AUTOMATIC_DISCOVERY_RANGE"
echo "RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
```

检查两端是否加载了正确的 ROS 2 和工作空间：

```bash
which ros2
ros2 pkg prefix <业务接口包>
```

### 第 2 层：Docker 网络是否符合预期

宿主机执行：

```bash
docker inspect -f \
  'name={{.Name}} network={{.HostConfig.NetworkMode}} ipc={{.HostConfig.IpcMode}}' \
  <container>
```

容器内执行：

```bash
ip addr
ip route
```

### 第 3 层：ROS 图能否发现

```bash
ros2 node list
ros2 topic list -t
ros2 service list -t
```

如果完全看不到对端节点，优先检查 Domain、发现范围、RMW、网络和防火墙。

### 第 4 层：接口类型是否一致

```bash
ros2 topic type /camera/image
ros2 service type /hal/device/mino17_0/get_property
ros2 interface show hal_interface/srv/GetProperty
```

两端必须加载兼容的接口定义。仅服务名称相同，不代表生成的类型一定兼容。

### 第 5 层：数据面是否正常

Topic：

```bash
ros2 topic info /camera/image --verbose
ros2 topic echo /camera/image --once
ros2 topic hz /camera/image
```

Service：

```bash
ros2 service call \
  /hal/device/mino17_0/get_property \
  hal_interface/srv/GetProperty \
  "{group_id: infrared_camera, property_id: is_streaming}"
```

Topic 可发现但没数据时，要继续检查发布端、QoS、生命周期状态和消息类型。

## 14. 常见现象、原因和处理

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 两端完全看不到节点 | `ROS_DOMAIN_ID` 不同 | 统一 Domain ID |
| 独立容器互相发现不了 | localhost-only、bridge 多播或网卡问题 | 排障阶段设为非 localhost-only，并测试 host network |
| `ros2 service list` 能看到但调用卡住 | RMW/daemon/类型不一致，服务端回调阻塞 | 对齐 RMW，重启 daemon，核对类型和服务端日志 |
| Topic 存在但无数据 | QoS 不兼容、发布端未激活、订阅类型不一致 | 用 `topic info --verbose` 检查 |
| 修改环境变量后 CLI 仍显示旧节点 | ROS 2 daemon 使用旧环境 | `ros2 daemon stop && ros2 daemon start` |
| 指定 RMW 后程序启动失败 | 镜像未安装该 RMW | 安装对应包或取消错误设置 |
| 宿主机能通信，Docker bridge 不行 | 多播/NAT/防火墙/网卡选择 | 检查 bridge 网络或使用静态发现方案 |
| `--network host` 后仍失败 | Domain、RMW、接口或应用状态问题 | 不要继续只改网络，按分层流程检查 |
| 高频大图像延迟高 | 网络复制、QoS、CPU、共享内存未启用 | 测量后再评估 SHM、零拷贝或组件内通信 |

## 15. 最小自检脚本

在每个容器中执行：

```bash
echo '=== ROS communication environment ==='
echo "ROS_DISTRO=$ROS_DISTRO"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}"
echo "ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-0}"
echo "ROS_AUTOMATIC_DISCOVERY_RANGE=${ROS_AUTOMATIC_DISCOVERY_RANGE:-unset}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-default}"

echo '=== installed RMW implementations ==='
ros2 pkg list | grep '^rmw_' | sort

echo '=== ROS graph ==='
ros2 node list
ros2 topic list -t
ros2 service list -t
```

注意：这里显示的 `default` 只是表示没有显式设置 `RMW_IMPLEMENTATION`。若必须知道实际加载的实现，应结合 `ros2 doctor --report`、进程环境和发行版默认配置确认。

## 16. 关键结论

1. `ROS_DOMAIN_ID` 决定节点是否位于同一个 ROS 2 逻辑域。
2. RMW 是中间件抽象接口，不等同于 DDS；底层也可以使用 Zenoh 等实现。
3. 默认 RMW 取决于发行版和构建配置，不能一概而论。
4. Humble 中 `ROS_LOCALHOST_ONLY=1` 限制为 localhost 范围；跨机器通信应关闭。
5. Docker bridge 中各容器的 localhost 相互独立；Linux host network 则共享宿主机网络栈。
6. `--network host` 有助于 DDS 发现，但不是所有通信问题的万能修复。
7. `--ipc host` 主要用于共享内存，不是普通 DDS 网络发现的必要条件。
8. 排障时先统一 Domain、发现范围、RMW 和接口版本，再检查 QoS 与业务逻辑。

## 17. 参考资料

- ROS 2 官方文档：ROS_DOMAIN_ID
- ROS 2 官方文档：Working with multiple RMW implementations
- ROS 2 官方文档：Different ROS 2 middleware vendors
- ROS 2 官方文档：ROS_LOCALHOST_ONLY 与发现范围
- Docker 官方文档：Host network driver
