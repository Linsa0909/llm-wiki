---
title: ROS 2：`.srv` 与 Service（服务）入门
type: concept
summary: 调用服务时，需要同时知道“服务名称”和“服务类型”：
tags:
  - ROS 2
  - srv
  - Service
  - 服务
  - 接口
  - CLI
links:
  - ROS 2
  - topic
  - action
  - msg
  - hal_interface
sources:
  - raw/imports/20260722-095304/ROS2-srv与Service服务入门.md
---
# ROS 2：`.srv` 与 Service（服务）入门

## 导入来源：ROS2-srv与Service服务入门.md

# ROS 2：`.srv` 与 Service（服务）入门

> 一句话：`.srv` 是 ROS 2 服务的“请求/响应协议说明书”，规定客户端要发送哪些字段，以及服务端要返回哪些字段。

## 1. 先区分三个概念

| 概念 | 示例 | 含义 |
|---|---|---|
| `.srv` 文件 | `GetProperty.srv` | 写在源码里的接口定义文件 |
| 服务类型 | `hal_interface/srv/GetProperty` | `.srv` 编译后生成的 ROS 2 类型 |
| 服务名称 | `/hal/device/mino17_0/get_property` | ROS 图中正在运行的服务入口 |

调用服务时，需要同时知道“服务名称”和“服务类型”：

```bash
ros2 service call \
  /hal/device/mino17_0/get_property \
  hal_interface/srv/GetProperty \
  "{group_id: infrared_camera, property_id: is_streaming}"
```

## 2. Service 是什么

ROS 2 Service 使用客户端/服务端的请求—响应模式：

```text
客户端发送 Request
        │
        ▼
     服务名称
        │
        ▼
服务端处理并返回 Response
```

它适合：

- 查询一次当前状态；
- 修改一个配置并确认是否成功；
- 开关设备；
- 执行能够快速完成的短操作。

它不适合持续传输图像、雷达或遥测数据，也不适合耗时很长且需要进度反馈、取消功能的任务。

## 3. `.srv` 文件长什么样

一个 `.srv` 文件只能有一个 `---` 分隔符：

```srv
# 请求部分：客户端填写
string group_id
string property_id
---
# 响应部分：服务端填写
bool success
string error_message
string value_json
uint64 sequence_number
builtin_interfaces/Time last_update_time
```

- `---` 上方定义 Request；
- `---` 下方定义 Response；
- 字段格式通常是 `类型 字段名`；
- `#` 后面是注释；
- 请求或响应部分都可以为空。

例如 `std_srvs/srv/Empty` 没有请求字段，也没有响应字段，它的定义基本只有：

```srv
---
```

## 4. 常见字段类型

```srv
bool enabled
int32 count
uint64 sequence_number
float64 temperature
string name
builtin_interfaces/Time stamp
int32[] values
string[3] labels
```

还可以引用其他接口类型：

```srv
geometry_msgs/Pose target_pose
```

`.srv` 不是运行时脚本。构建接口包后，ROS 2 会为 C++、Python 等语言生成相应的 Request 和 Response 类型。

## 5. Service、Topic、Action 怎么选

| 项目 | Topic | Service | Action |
|---|---|---|---|
| 通信模式 | 发布/订阅 | 请求/响应 | 目标/反馈/结果 |
| 典型数据 | 连续数据流 | 一次查询或短操作 | 长时间任务 |
| 是否返回结果 | 不要求 | 返回响应 | 返回结果 |
| 中途反馈 | 不支持 | 不支持 | 支持 |
| 取消任务 | 不支持 | 不支持 | 支持 |
| 示例 | 图像、雷达、状态流 | 查询属性、开关设备 | 导航、机械臂运动 |

选择口诀：

- 连续发布：Topic；
- 问一次、答一次：Service；
- 执行较久，还要进度和取消：Action。

Service 的接口语义是请求—响应，但客户端程序可以使用异步 API，不代表客户端线程必须一直阻塞等待。

## 6. 如何发现服务

每个新终端先加载 ROS 2 环境和工作空间：

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

然后查看服务：

```bash
# 列出当前 ROS 图中的所有服务
ros2 service list

# 同时显示服务类型
ros2 service list -t

# 查询某个服务的类型
ros2 service type /hal/device/mino17_0/get_property

# 查找使用某种类型的全部服务
ros2 service find hal_interface/srv/GetProperty
```

这里要注意：

- `ros2 interface list` 显示“已安装、可用的接口类型”；
- `ros2 service list` 显示“当前正在运行、能被发现的服务”。

接口存在，不代表服务端节点正在运行。

## 7. 如何查看 `.srv` 定义

```bash
# 查看服务类型的请求和响应字段
ros2 interface show hal_interface/srv/GetProperty

# 列出 hal_interface 包内的全部接口
ros2 interface package hal_interface

# 只筛选 srv
ros2 interface package hal_interface | grep '/srv/'
```

如果有源码，也可以直接查看：

```bash
find ~/ros2_ws/src -name 'GetProperty.srv' -print
```

推荐先使用 `ros2 interface show`，因为它显示的是当前终端实际加载到的已构建接口。

## 8. 如何在命令行调用服务

通用格式：

```bash
ros2 service call <服务名称> <服务类型> "{请求字段: 值}"
```

### 示例一：调用 GetProperty

```bash
ros2 service call \
  /hal/device/mino17_0/get_property \
  hal_interface/srv/GetProperty \
  "{group_id: infrared_camera, property_id: is_streaming}"
```

请求表示：查询 `infrared_camera` 能力组中的 `is_streaming` 属性。

可能得到类似响应：

```text
success: true
error_message: ''
value_json: 'true'
sequence_number: 0
last_update_time: ...
```

`value_json` 的类型是 `string`，里面保存的是 JSON 文本。因此：

- 布尔值可能显示为字符串内容 `'true'`；
- 字符串属性可能包含转义引号；
- 对象或数组也会以 JSON 文本形式返回。

### 示例二：请求整个能力组的属性快照

在当前 `GetProperty.srv` 约定中，`property_id` 为空表示查询该能力组的全部可读属性：

```bash
ros2 service call \
  /hal/device/mino17_0/get_property \
  hal_interface/srv/GetProperty \
  "{group_id: infrared_camera, property_id: ''}"
```

这是该项目对空字符串的业务约定，不是所有 `.srv` 文件都自动具有这种语义。

### 示例三：查询属性元数据

```bash
ros2 service call \
  /hal/device/mino17_0/get_property_meta \
  hal_interface/srv/GetPropertyMeta \
  "{group_id: infrared_camera, property_id: framerate}"
```

元数据响应可包含值类型、单位和 JSON Schema。当前接口要求 `group_id` 与 `property_id` 都提供，不能用空字段枚举全部属性。

### 示例四：无请求参数

```bash
ros2 service call /clear std_srvs/srv/Empty
```

## 9. 请求参数为什么使用 YAML 写法

`ros2 service call` 的最后一个参数采用 YAML 表示请求对象：

```bash
"{name: camera, enabled: true, count: 3}"
```

常见写法：

```yaml
enabled: true
count: 10
name: camera
values: [1, 2, 3]
pose:
  position: {x: 1.0, y: 2.0, z: 0.0}
```

在 Bash 中，建议用外层双引号或单引号把整个请求包起来，避免空格、花括号和特殊字符被 Shell 拆开。

## 10. `group_id` 和 `property_id` 从哪里来

字段名 `group_id`、`property_id` 是接口设计者写进 `.srv` 的；它们不是 ROS 2 自动生成的固定字段。

字段的可用值由具体系统约定。通常来自：

1. 设备能力说明或接口文档；
2. 能力模型 YAML；
3. `ros2 interface show` 里的注释；
4. 服务端提供的元数据查询接口；
5. 实际服务调用返回的错误信息。

在 Mino17 示例中：

```text
group_id    = infrared_camera
property_id = is_streaming
```

含义是“红外相机能力组”下的“是否正在推流”属性。不要凭经验随意写 `fps`、`resolution` 等名字；字段必须与当前设备模型的实际 ID 完全一致，例如该模型使用的是 `framerate`、`input_resolution` 和 `output_resolution`。

## 11. 在程序中如何调用

程序中的基本流程与命令行相同：

```text
创建 Client
  → 等待服务可用
  → 创建 Request
  → 填写请求字段
  → 异步发送请求
  → 在 Future/回调中读取 Response
```

Python 概念示例：

```python
from hal_interface.srv import GetProperty

client = node.create_client(
    GetProperty,
    '/hal/device/mino17_0/get_property'
)

request = GetProperty.Request()
request.group_id = 'infrared_camera'
request.property_id = 'is_streaming'

future = client.call_async(request)
```

实际程序还需要等待服务、处理超时、检查 `response.success`，并处理节点执行器和异常。

## 12. 常见问题与排查

### 找不到接口包

```text
The passed service type is invalid
```

检查：

```bash
source /opt/ros/<发行版>/setup.bash
source <工作空间>/install/setup.bash
ros2 interface show hal_interface/srv/GetProperty
```

### 服务类型写错

ROS 2 服务类型应写成：

```text
包名/srv/类型名
```

正确：

```text
hal_interface/srv/GetProperty
```

### 请求字段名或类型错误

先执行：

```bash
ros2 interface show hal_interface/srv/GetProperty
```

请求对象必须与 `---` 上方字段匹配。

### 服务不存在

```bash
ros2 service list | grep get_property
ros2 node list
```

确认服务端节点已启动，并处于能提供服务的生命周期状态。

### 调用停在 `requester: making request`

这通常表示请求已经发出但没有收到响应。依次检查：

- 服务端是否仍在运行；
- 客户端与服务端的 `ROS_DOMAIN_ID` 是否一致；
- Docker/跨主机网络是否允许 DDS 通信；
- 两端 `RMW_IMPLEMENTATION` 是否兼容；
- 服务端回调是否阻塞或异常；
- 客户端是否设置了合理超时。

### 服务用于高频连续查询

如果持续、频繁调用同一个服务来取状态，通常应重新评估是否改用 Topic。Service 更适合按需调用。

## 13. 最小记忆清单

```text
.srv = 请求/响应的数据协议
--- 上面 = Request
--- 下面 = Response
服务类型 = 包名/srv/类型名
服务名称 = ROS 图中的运行入口
调用 = ros2 service call 服务名 服务类型 YAML请求
短查询用 Service，连续流用 Topic，长任务用 Action
```

## 14. 参考资料

- ROS 2 官方文档：Interfaces（Topics、Services、Actions）
- ROS 2 官方教程：Understanding services
- ROS 2 官方教程：Writing a simple service and client
