---
title: Docker IPC 模式与 ROS 2 DDS 共享内存
type: note
summary: IPC 是 **Inter-Process Communication（进程间通信）**。Linux 进程可以通过共享内存、信号量、消息队列、管道、Unix Socket 等机制协作。
tags:
  - Docker
  - IPC
  - ROS 2
  - DDS
  - Fast DDS
  - 共享内存
  - /dev/shm
links:
  - Docker
  - ROS 2
  - DDS
  - Fast DDS
sources:
  - raw/imports/20260714-203108/Docker-IPC模式与ROS2-DDS共享内存.md
importance: high
---
# Docker IPC 模式与 ROS 2 DDS 共享内存

## 导入来源：Docker-IPC模式与ROS2-DDS共享内存.md

# Docker IPC 模式与 ROS 2 DDS 共享内存

> 适用场景：理解 Docker 容器的 IPC 隔离、`/dev/shm` 容量，以及 ROS 2 节点跨容器通信时是否需要共享 IPC。

## 1. IPC 是什么

IPC 是 **Inter-Process Communication（进程间通信）**。Linux 进程可以通过共享内存、信号量、消息队列、管道、Unix Socket 等机制协作。

Docker 的 `--ipc` 主要控制容器使用哪个 **IPC namespace**。IPC namespace 隔离的核心对象包括：

- System V 共享内存、信号量和消息队列；
- POSIX 消息队列；
- Docker 为容器提供的 `/dev/shm` 共享内存挂载。

它不等于 Docker 网络模式，也不决定容器能否通过 TCP/UDP 通信。

## 2. 默认 IPC 模式

```bash
docker run -d my_image
```

未指定 `--ipc` 时，Docker 使用 daemon 配置的默认 IPC 模式。当前 `dockerd` 默认配置通常为：

```text
default-ipc-mode = private
default-shm-size = 64MiB
```

因此在未修改 daemon 配置的常见环境中，它近似等价于：

```bash
docker run --ipc=private -d my_image
```

不要把它理解成所有 Docker 环境都必然为 `private`：daemon 的默认值可以被管理员改为 `shareable`。应以实际容器配置为准：

```bash
docker inspect -f '{{.HostConfig.IpcMode}}' <container>
docker inspect -f '{{.HostConfig.ShmSize}}' <container>
```

## 3. private 模式意味着什么

`--ipc=private` 为容器创建独立的 IPC namespace：

| 资源 | 行为 |
|---|---|
| `/dev/shm` | 容器拥有自己的 tmpfs；daemon 默认大小通常为 64 MiB |
| System V 共享内存 | 与宿主机及其他 IPC namespace 隔离 |
| System V 信号量、消息队列 | 容器内独立 |
| POSIX 消息队列 | 由 IPC namespace 隔离 |

```text
宿主机 IPC namespace
├── 宿主机 /dev/shm、共享内存、信号量和消息队列
├── 容器 A：独立 IPC namespace + 独立 /dev/shm
└── 容器 B：独立 IPC namespace + 独立 /dev/shm
```

同一容器内的多个进程仍然可以互相使用共享内存；“private”只是表示它们默认不与宿主机或其他容器共享 IPC namespace。

## 4. Docker IPC 模式对比

| 启动参数 | 含义 | `/dev/shm` |
|---|---|---|
| 不指定 `--ipc` | 使用 daemon 默认值，通常为 `private` | 取决于 daemon 默认配置 |
| `--ipc=private` | 创建独立 IPC namespace | 容器独立挂载 |
| `--ipc=none` | 创建独立 IPC namespace，但不挂载 `/dev/shm` | 不存在 Docker 提供的 `/dev/shm` 挂载 |
| `--ipc=shareable` | 创建独立 IPC namespace，并允许其他容器加入 | 可供加入者共享 |
| `--ipc=container:<name-or-id>` | 加入另一个 `shareable` 容器的 IPC namespace | 与目标容器共享 |
| `--ipc=host` | 直接使用宿主机 IPC namespace | 与宿主机共享 |

### shareable 与 container 模式

```bash
# 作为 IPC namespace 提供者
docker run -d --name ipc-donor --ipc=shareable image_a

# 加入提供者的 IPC namespace
docker run -d --name ipc-client \
  --ipc=container:ipc-donor image_b
```

适用于少量明确需要共享 IPC 的容器。提供者容器的生命周期会成为系统设计的一部分，应避免随意删除或重建。

### host 模式

```bash
docker run -d --ipc=host my_image
```

容器直接使用宿主机 IPC namespace。这样做减少了隔离：容器进程可能看到或影响宿主机及其他 host-IPC 容器的共享内存、信号量和消息队列。因此只应在明确需要时启用。

## 5. IPC 模式与 `/dev/shm` 容量不是一回事

如果一个容器内部需要更大的共享内存，通常无需使用 host IPC，只要调整容量：

```bash
docker run -d --shm-size=1g my_image
```

检查容器内实际容量：

```bash
docker exec <container> df -h /dev/shm
docker exec <container> mount | grep '/dev/shm'
```

典型场景包括数据库、浏览器、多进程 Python/PyTorch 或图像处理程序。此类程序若只在一个容器内部共享数据，优先使用 `--shm-size`，保留 private IPC 的隔离性。

## 6. ROS 2 与 DDS 共享内存

ROS 2 的底层通信由所选 DDS/RMW 实现决定。是否使用共享内存不能只根据“这是 ROS 2”判断，还要确认：

1. 当前使用的 RMW/DDS 实现；
2. 对应版本是否支持并启用了共享内存传输；
3. 发布者和订阅者是否被 DDS 判断为同一主机；
4. 容器是否共享所需的网络和 IPC 资源；
5. 消息类型、QoS 和数据共享约束是否满足。

查看当前 RMW：

```bash
echo "$RMW_IMPLEMENTATION"
ros2 doctor --report | grep -i rmw
```

### 同一容器内的 ROS 2 节点

多个节点在同一个容器内运行时，它们天然处于同一 IPC namespace，可使用同一个 `/dev/shm`。通常不需要 `--ipc=host`。

若遇到共享内存不足，先检查并增大容量：

```bash
docker run --shm-size=512m ...
```

### Fast DDS 跨容器共享内存

Fast DDS 官方 Docker 指南指出，要让不同容器被识别为同一主机并共享 SHM，典型启动方式需要同时使用：

```bash
docker run --network=host --ipc=host ...
```

- `--network=host`：让 Fast DDS 根据网络接口判断这些参与者位于同一主机；
- `--ipc=host`：让容器访问同一个共享内存机制。

只使用 `--ipc=host` 不一定能启用 Fast DDS 的跨容器共享内存，因为网络栈仍可能让两个参与者被识别为不同主机。反过来，只使用 `--network=host` 也不够，因为 IPC 空间仍然隔离。

这是一种高性能但低隔离的配置。上线前需要结合安全边界、端口冲突、部署平台和 DDS 配置进行验证。

### Cyclone DDS 等其他实现

不要直接套用 Fast DDS 的结论。不同 DDS/RMW 的共享内存实现、默认开关和依赖不同，有些版本需要额外插件或中间件。应查询当前版本的官方文档并通过实际流量测试确认。

## 7. RTMP + ROS 2 多容器场景

示例架构：

```text
容器 A：ZLMediaKit，提供 RTMP 服务
        │ TCP/RTMP
        ▼
容器 B：拉流、解码并发布 sensor_msgs/msg/Image
        │ DDS
        ▼
容器 C：订阅图像并执行算法
```

这里存在两段不同性质的通信：

- A → B 是 RTMP/TCP 网络通信，不受 Docker IPC 模式直接控制；
- B → C 是 ROS 2/DDS 通信，是否能走共享内存取决于 DDS 实现和容器配置。

默认 private IPC 下，B 与 C 不能直接共享同一个 IPC namespace。DDS 通常仍可通过 UDP 等网络传输通信，但性能和复制次数可能不同。实际影响需要测量，不能仅凭架构图断定“影响不大”。图像分辨率、帧率、订阅者数量、QoS、CPU 占用和网络路径都会改变结果。

## 8. 选择建议

| 场景 | 建议 |
|---|---|
| 普通应用或单容器多进程 | 保持默认/private |
| 单容器 `/dev/shm` 不够 | 使用 `--shm-size` |
| 两个明确协作的容器需要共享 IPC | 考虑 `shareable` + `container:<id>` |
| Fast DDS 跨容器且已确认需要 SHM | 评估 `--network=host --ipc=host` |
| 只是希望 ROS 2 容器能互相发现 | 先解决 DDS 网络发现，不要直接把 IPC 改成 host |
| 无法确认性能瓶颈 | 先测量 UDP/SHM 的延迟、吞吐、CPU 和丢帧，再决定 |

## 9. Docker Compose 示例

单容器只需增大共享内存：

```yaml
services:
  ros_node:
    image: my_ros_image
    shm_size: 512m
```

Fast DDS 跨容器 SHM 的典型 Linux 配置：

```yaml
services:
  publisher:
    image: my_ros_image
    network_mode: host
    ipc: host

  subscriber:
    image: my_ros_image
    network_mode: host
    ipc: host
```

`network_mode: host` 会带来端口冲突和网络隔离降低等影响；该组合不应作为所有 ROS 2 容器的默认模板。

## 10. 验证与排障命令

```bash
# 查看容器的 IPC 和共享内存配置
docker inspect -f \
  'ipc={{.HostConfig.IpcMode}} shm={{.HostConfig.ShmSize}} network={{.HostConfig.NetworkMode}}' \
  <container>

# 查看容器内部 /dev/shm
docker exec <container> df -h /dev/shm
docker exec <container> ls -la /dev/shm

# 查看 System V IPC 资源
docker exec <container> ipcs -a

# ROS 2 节点、话题和频率
docker exec <container> ros2 node list
docker exec <container> ros2 topic list -t
docker exec <container> ros2 topic hz /camera/image_raw
```

建议在变更前后记录：端到端延迟、帧率、CPU、内存、网络吞吐和丢帧数。只有这些指标明显改善，才说明共享 IPC 配置真正解决了瓶颈。

## 11. 结论

- private IPC 的核心是隔离，并不禁止同一容器内的进程使用共享内存。
- 未指定 `--ipc` 使用 daemon 默认值；常见默认值是 private，但应实际检查。
- `/dev/shm` 容量不足时，优先用 `--shm-size`，不必直接启用 host IPC。
- ROS 2 跨容器是否需要共享 IPC，取决于具体 DDS/RMW、部署结构和性能指标。
- Fast DDS 跨容器使用 SHM 的典型配置同时需要 host network 与 host IPC。
- `--ipc=host` 会削弱隔离，应作为经过验证的性能配置，而不是通用默认项。

## 12. 参考资料

- Docker CLI：`docker container run` 的 IPC 模式说明
- Docker daemon：`default-ipc-mode` 与 `default-shm-size`
- eProsima Fast DDS：Docker 部署中的 Shared Memory Transport
