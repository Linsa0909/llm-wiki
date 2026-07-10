---
title: docker相关
type: concept
summary: **1. 打包镜像 (Build)**
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-171413/poc项目学习.md
---
# docker相关

## 导入来源：poc项目学习.md

# docker相关

## 第一阶段：开发与打包 

**1. 打包镜像 (Build)**

- **命令:** `docker build -t poc:v2.0 .`
- **作用:** 读取当前目录下的 `Dockerfile`，把你的代码和环境封进一个叫 `poc:v2.0` 的镜像里。
- **💡 扩展参数:**
  - `-t` (tag): 给镜像起名字和版本号（格式为 `名字:版本`）。
  - `--no-cache`: 强制不使用缓存，重新下载所有东西

**2. 验货：透视检查内部文件 (Inspect)**

- **命令:** `docker run --rm poc:v2.0 ls -la /ServiceDesign`
- **作用:** 不执行主程序，只是临时开启容器看一眼里面的代码和文件拷没拷对，看完立刻销毁容器。

**3. 导出为离线压缩包 (Save)**

- **命令:** `docker save -o poc_x86_v2.0.tar poc:v2.0`
- **作用:** 把存在 Docker 引擎里的镜像，抽成一个实实在在的 `.tar` 物理文件。接下来你就可以把它拷进 U 盘带走了。
- **💡 扩展参数:**
  - `-o` (output): 指定输出的文件名。

------

## 第二阶段：现场部署

**4. 导入镜像 (Load)**

- **命令:** `docker load -i drone_poc_v2.0.tar`
- **作用:** 加载镜像。
- **💡 扩展参数:**
  - `-i` (input): 指定你要导入的压缩包路径。
  - 导入后，你可以用 `docker images` 查看镜像是否成功出现在列表中。

**5. 终极挂载启动 (Run)**

- **命令:**

```
docker run --rm \
  -v $(pwd)/config.json:/ServiceDesign/config.json \
  -v $(pwd)/logs:/ServiceDesign/logs \
  poc:v2.0 python3 /ServiceDesign/Project.py \
    --config /ServiceDesign/config.json \
    --data-file fire_control_radar_types.h \
    --service-catalog fire_control_radar_service_catalog.json \
    --operation-bindings fire_control_radar_operation_bindings.json \
    --business-flow fire_control_radar_business_flow.json
```

- **作用:** 启动容器，同时把外部改好的配置文件“贴”进去，把内部产生的日志文件“接”出来。
- **💡 扩展参数 (极度重要):**

  - `--rm`: 阅后即焚。程序跑完（无论是成功还是报错退出）后，自动清理容器尸体，绝不弄脏客户服务器。
  - `-v` (volume): 数据卷挂载。格式为 `宿主机绝对路径:容器内绝对路径`。

------

##  第三阶段：日志与清理

**6. 查看实时日志 (Logs)**

- **命令:** `docker logs -f <容器ID或名字>`
- **作用:** 如果你刚才用了 `-d` 后台运行，你可以用这行命令像看直播一样，看着你的彩色日志在屏幕上滚动。
- **💡 扩展参数:**
  - `-f` (follow): 持续跟踪日志输出。按 `Ctrl+C` 退出查看。
  - `--tail 100`: 只看最后 100 行日志。

**7. 强杀与清理 (Rm / Rmi)**

- **命令:** `docker rmi -f drone-poc:v2.0` (删镜像)
- **作用:** 客户现场部署完了，或者你想传一个新版本的包，先把旧的垃圾清空。
- **💡 扩展命令:**
  - `docker ps`: 看当前有哪些容器正在跑。
  - `docker ps -a`: 看所有容器（包括已经死掉的）。





# 代码相关

总体：

每个视图作为一个文件夹，将每个视图的操作抽象封装成函数，视图作为一个类 使用操作即调用类的函数将主流程为 函数调用流转参数 最后实现整个过程。

所以针对每个视图，需先初始化 

主流程放在

![image-20260311113023671](C:\Users\Linsa\AppData\Roaming\Typora\typora-user-images\image-20260311113023671.png)

1.基类的封装

```
payload = json.dumps(data) if data is not None else None
```

三元表达式   x if 条件 else y ，如果条件满足执行x，否则执行y

2.动态绝对路径

```
# 1. 精准计算出你的项目根目录 (Project.py 所在目录的上一级)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 2. 拼装出完美的默认配置文件绝对路径
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
```

3.字典与列表解析

字典  { }

列表 = [  ]



遍历字典，列表是有序的，所以有index

info = {"id": "101", "name": "无人机项目A"}

```
循环字典
# 必须加 .items()，这样就能同时拿到 key(标签) 和 value(内容)
info = {"id": "101", "name": "无人机项目A"}mcf
for key, value in info.items():
    print(f"标签是 {key}，内容是 {value}")
```

2.命令行参数解析

3.配置读取并运行

4.DockerFile学习

5.logger（loguru)学习

6.一些bug排错





### Poc_Demo 

1. python项目
2. 打包镜像
3. 部署
4. 业务流程

相关docker命令：

docker build -t 

docker images 

docker sqve -o []



 

准备的文件： drone-poc：v2.0.tar config.json 空文件夹logs

1.最好拷贝到同一文件夹下

2.加载镜像，查看镜像内容，镜像是否成功加载（docker命令）

3.根据实际情况修改config.json 

4.运行 

```
docker run --rm \
  -v $(pwd)/config.json:/ServiceDesign/config.json \
  -v $(pwd)/logs:/ServiceDesign/logs \
  drone-poc:v2.0 \
  python /ServiceDesign/Project.py --config /ServiceDesign/config.json
```

5.结果 tty上可以查看到实时日志 并且每次运行的日志都会保存到logs文件夹下
