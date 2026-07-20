---
title: Mino17Adapter 代码讲解：pipeline、生命周期与编译链接
type: note
summary: `Mino17Adapter` 是 Mino17 红外相机的 HAL 适配器。它不只是“声明一个设备”，而是把真实 Linux 视频设备、ZLMediaKit、推流进程、HAL 属性和服务调用连接起来。
tags:
  - Mino17
  - HAL
  - C++
  - pipeline
  - V4L2
  - ZLMediaKit
  - RK3588
  - 代码讲解
links:
  - Mino17 RK3588 红外采集推流
  - 视频采集与推流
  - Linux设备文件与V4L2
  - ZLMediaKit流媒体分发
sources:
  - raw/imports/20260713-200504/Mino17Adapter-pipeline-lifecycle-build.md
---
# Mino17Adapter 代码讲解：pipeline、生命周期与编译链接

## 导入来源：Mino17Adapter-pipeline-lifecycle-build.md

# Mino17Adapter 代码讲解：pipeline、生命周期与编译链接

## 一句话说明

`Mino17Adapter` 是 Mino17 红外相机的 HAL 适配器。它不只是“声明一个设备”，而是把真实 Linux 视频设备、ZLMediaKit、推流进程、HAL 属性和服务调用连接起来。

它主要做四件事：

1. 读取 `mino17.conf` 或启动参数。
2. 自动识别 `/dev/videoX` 中哪个是 Mino17。
3. 启动内置 ZLMediaKit RTMP/HTTP 服务。
4. 管理视频采集、处理、编码、推流 pipeline，并把 `start_stream` / `stop_stream` / `restart_stream` 暴露给上层。

## 代码入口

这段代码没有 `main()`，入口由外部 HAL 框架调用：

```cpp
Mino17Adapter::connect(const ConnectionConfig& config)
Mino17Adapter::bindToEntity(model::DeviceEntity& entity)
Mino17Adapter::handleStartStream(...)
Mino17Adapter::handleStopStream(...)
Mino17Adapter::disconnect()
```

典型流程是：

```text
外部框架创建 Mino17Adapter
-> connect(config)
-> bindToEntity(entity)
-> 上层调用 start_stream
-> adapter 启动 pipeline
-> pipeline 推 RTMP 流
-> disconnect 或析构时停止 pipeline
```

## 为什么会有 pipeline

Mino17 原始输出不是最终可播放的视频流。它通常从 Linux V4L2 设备节点读取原始帧，例如 `/dev/video0`，然后经过一串处理：

```text
/dev/videoX
-> 读取 UYVY 640x518
-> 裁掉冗余 6 行，变成 640x512
-> 转 RGB
-> 伪彩处理
-> 转 NV12 / 硬件帧
-> h264_rkmpp 编码
-> FLV/RTMP 推流到 ZLMediaKit
```

所以 `pipeline` 就是“把相机原始帧变成网络视频流”的执行链路。`Mino17Adapter` 本身不逐帧处理图像，它负责配置、启动、停止、监控这条链路。

## pipeline 关键代码与注释

### 1. 拼出默认 pipeline 命令

```cpp
if (pipeline_command_.empty()) {
    pipeline_command_ = pipeline_executable_ + " " + camera_device_ + " " + output_url_;
}
```

含义：如果配置里没有显式给 `pipeline_command`，就用三个字段拼命令：

```text
pipeline_executable camera_device output_url
```

例如可能变成：

```bash
/opt/yunshu/bin/mino17_push /dev/video0 rtmp://127.0.0.1/live/mino17
```

风险：这是字符串拼 shell 命令，没有参数转义。如果 `camera_device_` 或 `output_url_` 来自不可信输入，会有命令注入风险。

### 2. 创建 MediaPipelineManager

```cpp
if (pipeline_mode_ != "service_script") {
    hal::utils::MediaPipelineManager::PipelineConfig pipeline_config;
    pipeline_config.hardware_device = camera_device_;
    pipeline_config.exec_command = pipeline_command_;
    pipeline_config.input_type = hal::utils::MediaPipelineManager::PipelineInputType::DeviceNode;
    pipeline_config.tool_type = hal::utils::MediaPipelineManager::PipelineToolType::Custom;
    pipeline_config.input_descriptor = camera_device_;
    pipeline_config.max_restarts = -1;
    pipeline_config.watchdog_interval_ms = 500;
    pipeline_config.restart_backoff_initial_ms = 1000;
    pipeline_config.restart_backoff_max_ms = 8000;

    pipeline_ = std::make_unique<hal::utils::MediaPipelineManager>(pipeline_config);
}
```

字段含义：

- `hardware_device`: 真实设备路径，例如 `/dev/video0`。
- `exec_command`: 真正执行的采集推流命令。
- `input_type = DeviceNode`: 输入来自 Linux 设备节点。
- `tool_type = Custom`: 使用自定义推流命令，不是固定模板。
- `max_restarts = -1`: 通常表示无限重启。
- `watchdog_interval_ms = 500`: 每 500ms 检查一次状态。
- `restart_backoff_initial_ms = 1000`: 第一次重启等待 1 秒。
- `restart_backoff_max_ms = 8000`: 重启退避最大 8 秒。

`pipeline_` 大概率是：

```cpp
std::unique_ptr<hal::utils::MediaPipelineManager> pipeline_;
```

这表示 `Mino17Adapter` 独占 pipeline 对象。`pipeline_.reset()` 或 adapter 析构时，会释放它。

### 3. 注册 pipeline 状态回调

```cpp
pipeline_->onStateChanged([this](bool running) {
    if (running) {
        setHealth(AdapterHealth::Healthy);
    } else {
        setHealth(conn_state_.load() == ConnectionState::Connected
                      ? AdapterHealth::Degraded
                      : AdapterHealth::Unknown);
        if (entity_) {
            hal::model::ServiceParams params;
            params["error_code"] = static_cast<int32_t>(1001);
            params["message"] = std::string("Mino17 media pipeline stopped.");
            entity_->emitEvent("infrared_camera", "stream_error", params);
        }
    }
});
```

含义：pipeline 状态变化时，adapter 同步更新健康状态。

- `running == true`: 推流运行中，健康状态为 `Healthy`。
- `running == false` 且 adapter 仍连接：说明设备还在，但流断了，状态为 `Degraded`。
- 如果绑定了 `DeviceEntity`，上报 `stream_error` 事件。

重点风险：`[this]` 捕获的是当前对象地址。如果 `MediaPipelineManager` 内部有异步线程，那么必须保证 adapter 析构后回调不会再触发，否则会访问已经销毁的对象。

### 4. 启动 pipeline

```cpp
bool Mino17Adapter::startPipeline() {
    bool started = false;
    if (camera_device_ == "auto") {
        log(LogLevel::Error, "Cannot start Mino17 stream: camera device was not detected.");
    } else if (pipeline_mode_ == "service_script") {
        started = runShellCommand(pipeline_command_);
        script_running_.store(started);
        setHealth(started ? AdapterHealth::Healthy : AdapterHealth::Degraded);
    } else if (pipeline_) {
        started = pipeline_->start();
    }

    {
        std::lock_guard<std::mutex> lock(stats_mutex_);
        ++stats_.commands_sent;
        if (started) {
            ++stats_.commands_succeeded;
        } else {
            ++stats_.commands_failed;
        }
        stats_.last_activity = std::chrono::steady_clock::now();
    }
    return started;
}
```

这里分三种情况：

1. `camera_device_ == "auto"`: 说明自动探测失败，不能启动。
2. `pipeline_mode_ == "service_script"`: 直接执行 shell 命令。
3. 默认模式：调用 `pipeline_->start()`，由 `MediaPipelineManager` 管理进程。

`stats_mutex_` 用来保护统计数据，避免多线程同时改 `stats_`。

### 5. 停止和重启 pipeline

```cpp
void Mino17Adapter::stopPipeline() {
    if (pipeline_mode_ == "service_script") {
        if (!pipeline_stop_command_.empty()) {
            runShellCommand(pipeline_stop_command_);
        }
        script_running_.store(false);
        return;
    }
    if (pipeline_) {
        pipeline_->stop();
    }
}

bool Mino17Adapter::restartPipeline() {
    stopPipeline();
    return startPipeline();
}
```

默认模式交给 `MediaPipelineManager` 停止；脚本模式下，如果没有配置 `pipeline_stop_command`，代码只能把内部标记改成 false，不一定真的杀掉外部进程。

### 6. 判断 pipeline 是否运行

```cpp
bool Mino17Adapter::isPipelineRunning() const {
    if (pipeline_mode_ == "service_script") {
        if (!pipeline_status_command_.empty()) {
            return std::system(pipeline_status_command_.c_str()) == 0;
        }
        return script_running_.load();
    }
    return pipeline_ && pipeline_->isRunning();
}
```

默认模式通过 `pipeline_->isRunning()` 获取真实状态。脚本模式下，如果没有 `pipeline_status_command`，只能相信 `script_running_`，这个值不一定等于真实进程状态。

## 指针、引用、生命周期

### `const ConnectionConfig& config`

`connect()` 的参数是引用：

```cpp
bool Mino17Adapter::connect(const ConnectionConfig& config)
```

含义：不复制整个配置对象，只借用调用方传入的对象，并承诺不修改它。

### `std::string* reason`

自动检测函数使用指针作为可选输出参数：

```cpp
std::string autoDetectMino17Device(std::string* reason)
```

调用方传：

```cpp
std::string detect_reason;
const auto detected = autoDetectMino17Device(&detect_reason);
```

函数内部写回：

```cpp
if (reason) {
    *reason = best_detail;
}
```

因为指针可能是 null，所以写入前必须判断。

### `entity_ = &entity`

```cpp
void Mino17Adapter::bindToEntity(model::DeviceEntity& entity) {
    entity_ = &entity;
}
```

`entity` 是引用，调用时必须有效；但保存进成员变量时变成裸指针 `entity_`。

这表示 adapter 不拥有 `DeviceEntity`，只是记住它的位置。必须保证 `DeviceEntity` 生命周期长于 `Mino17Adapter`，否则 `entity_->emitEvent(...)` 会访问悬空指针。

### `[this]` 回调

代码多次把 `this` 放进 lambda：

```cpp
[this]() { return getIsStreaming(); }
[this](bool running) { ... }
```

这意味着回调保存了当前 adapter 的地址。只要这些回调还可能被调用，adapter 对象就必须还活着。

这是这段代码里最需要审查的生命周期点。

## 编译链接要点

这段代码依赖：

- Linux/V4L2：`linux/videodev2.h`、`open`、`ioctl`、`close`。
- ZLMediaKit：`mk_common.h`、`mk_mediakit.h`、`mk_env_init2`、`mk_rtmp_server_start`、`mk_http_server_start`。
- HAL 内部模块：`DeviceEntity`、`ServiceResult`、`MediaPipelineManager`。
- C++17：`std::filesystem`、结构化绑定、`std::make_unique`。

CMake 中类似下面的链接是必要的：

```cmake
add_library(hal_mino17_adapter SHARED
  src/adapter/mino17/mino17_adapter.cpp
)

target_link_libraries(hal_mino17_adapter hal_model hal_media hal_zlm)
```

如果 `hal_zlm` 没有真正链接 ZLMediaKit，常见链接错误是：

```text
undefined reference to mk_env_init2
undefined reference to mk_rtmp_server_start
undefined reference to mk_http_server_start
```

如果作为插件被 `dlopen` 加载，还要注意 C++ ABI：插件入口最好用 `extern "C"` 导出稳定符号，跨动态库边界不要随意暴露 STL 对象或让一边 `new`、另一边 `delete`。

## 风险点

- `std::system()` 执行拼接字符串，有命令注入风险。
- `entity_` 是裸指针，生命周期由外部保证。
- `[this]` 回调可能在异步线程中访问已销毁对象。
- `connect()` 即使找不到相机也返回 `true`，调用方不能只看返回值，要看 health。
- 配置文件会覆盖外部 `config.extra`，优先级需要确认是否符合预期。
- `service_script` 模式下，没有 status 命令时，运行状态只是内部标记。
- ZLM HTTP 端口固定为 `8090`，多实例或已有服务可能冲突。

## 自查 checklist

- 编译是否通过，是否没有 `undefined reference to mk_*`。
- `ldd libhal_mino17_adapter.so` 是否没有 `not found`。
- 日志是否出现 `Loaded Mino17 config file` 或 `Mino17 config file not found`。
- 插入设备后，日志是否出现 `Auto-detected Mino17 camera device`。
- 自动检测详情是否包含 `uyvy=yes`、`640x518=yes`、`50fps=yes`。
- `connect()` 后不要只看返回值，要检查 `getHealth()` 是否为 `Healthy`。
- 调用 `start_stream` 后，`is_streaming` 是否为 true。
- RTMP 地址是否可以播放。
- 杀掉推流进程后，是否触发 `stream_error` 事件。
- `disconnect()` 后，pipeline 回调是否还能触发；如果还能触发，需要修生命周期。
- `DeviceEntity` 是否一定比 `Mino17Adapter` 活得更久。
- `pipeline_command_` 是否包含外部输入；如果包含，应该避免 shell 拼接，改成 argv 方式启动。
