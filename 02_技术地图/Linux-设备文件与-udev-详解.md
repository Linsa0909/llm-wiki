---
title: Linux 设备文件与 udev 详解
type: concept
summary: Linux 将所有 I/O 设备抽象为文件，统一通过 `open()/read()/write()/ioctl()/close()` 访问。
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-155519/Linux设备文件与udev详解.md
---
# Linux 设备文件与 udev 详解

## 导入来源：Linux设备文件与udev详解.md

# Linux 设备文件与 udev 详解

> 面向无人系统/设备集成开发岗位，重点覆盖 `/dev/tty*`、设备树概念、udev 规则编写。

---

## 一、Linux 设备模型核心概念

### 1.1 "一切皆文件"

Linux 将所有 I/O 设备抽象为文件，统一通过 `open()/read()/write()/ioctl()/close()` 访问。

```
用户空间 (User Space)
    │
    │ read() / write() / ioctl()
    ▼
┌─────────────┐
│  /dev/ttyUSB0 │  ← 设备节点 (Device Node)
│  /dev/i2c-1   │     major:minor 号关联到驱动
│  /dev/can0    │
└──────┬───────┘
       │
       ▼
内核空间 (Kernel Space)
┌─────────────┐
│  设备驱动     │  ← 字符设备驱动 / 块设备驱动 / 网络设备驱动
│  (Driver)    │
└──────┬───────┘
       │
       ▼
┌─────────────┐
│  硬件设备     │  ← USB 转串口芯片 / CAN 控制器 / 传感器
└─────────────┘
```

### 1.2 设备类型

| 类型 | 标识 | 典型设备 | 访问方式 |
|------|------|----------|----------|
| **字符设备** | `c` | `/dev/ttyUSB0`, `/dev/i2c-1`, `/dev/gpio*` | 字节流，顺序读写 |
| **块设备** | `b` | `/dev/sda`, `/dev/mmcblk0` | 块读写，支持随机访问，有缓存 |
| **网络设备** | 无设备文件 | `eth0`, `wlan0`, `can0` | Socket API |

```bash
# 查看设备类型
ls -la /dev/ttyUSB0
# crw-rw---- 1 root dialout 188, 0 Jun 23 10:00 /dev/ttyUSB0
#  c = 字符设备
#  188 = major number (主设备号，关联驱动)
#    0 = minor number (次设备号，区分同类设备的不同实例)
```

### 1.3 Major / Minor 号

```
Major Number: 告诉内核使用哪个驱动程序
Minor Number: 驱动程序用这个号区分不同的设备实例

示例:
  /dev/ttyUSB0 → major=188, minor=0
  /dev/ttyUSB1 → major=188, minor=1  (同一个驱动，第二个设备)
  /dev/ttyACM0 → major=166, minor=0  (不同驱动)
```

---

## 二、/dev/tty* 设备详解

### 2.1 tty 设备家族全景

```
/dev/tty* 设备树 (简化):

tty (TeleTYpewriter) 家族
├── 虚拟终端 (Virtual Console)
│   ├── /dev/tty1 ~ /dev/tty63     # 本地控制台 (Ctrl+Alt+F1~F6)
│   └── /dev/tty0                  # 当前激活的控制台
│
├── 伪终端 (Pseudo Terminal - PTY)
│   ├── /dev/pts/0, /dev/pts/1...  # SSH/Terminal 模拟器产生的终端
│   └── /dev/ptmx                  # PTY master 多路复用
│
├── 串口设备 (Serial Port)
│   ├── /dev/ttyS0 ~ /dev/ttyS3    # 主板原生串口 (COM1~COM4)
│   ├── /dev/ttyUSB0 ~ /dev/ttyUSBn # USB 转串口 (CP2102/CH340/FT232)
│   └── /dev/ttyACM0 ~ /dev/ttyACMn # USB CDC-ACM 虚拟串口 (Arduino/ESP32-S3)
│
└── 其他
    ├── /dev/ttyAMA0               # ARM 平台 (树莓派) 原生串口
    └── /dev/ttyprintk             # 内核 printk 输出
```

### 2.2 USB 转串口的三种典型场景

| 设备文件 | 芯片 | 典型场景 | 注意事项 |
|----------|------|----------|----------|
| `/dev/ttyUSB0` | CP2102/CH340/FT232/PL2303 | 通用 USB-TTL 模块，GPS 模块，数传电台 | 热插拔后编号可能变化 |
| `/dev/ttyACM0` | ATmega32U4, ESP32-S3 USB-OTG, STM32 VCP | Arduino Leonardo/Micro, 带原生 USB 的 MCU | CDC-ACM 协议，表现略有不同 |
| `/dev/ttyS0` | 板载 8250/16550 UART | 工控机原生串口 (COM1) | 固定编号，不会变化 |

### 2.3 串口操作实战

```bash
# ===== 设备发现 =====
# 列出所有串口设备
ls /dev/tty*
dmesg | grep tty        # 内核日志中查找

# 查看 USB 设备树
lsusb
# Bus 001 Device 005: ID 10c4:ea60 Silicon Labs CP2102 USB to UART Bridge

# 查看设备详细信息
udevadm info -a -n /dev/ttyUSB0
# 会打印完整的 sysfs 设备路径和属性

# ===== 权限问题 =====
# 把自己加入 dialout 组（最常见问题）
sudo usermod -a -G dialout $USER
# 重新登录后生效

# 临时给权限（重启失效）
sudo chmod 666 /dev/ttyUSB0

# ===== 串口参数 =====
stty -F /dev/ttyUSB0         # 查看当前串口参数
stty -F /dev/ttyUSB0 115200 cs8 -cstopb -parenb  # 设置波特率/数据位/停止位/校验

# ===== 原始数据收发测试 =====
# 接收
cat /dev/ttyUSB0
# 发送
echo "AT\r\n" > /dev/ttyUSB0
# 十六进制收发
xxd /dev/ttyUSB0
echo -ne "\xAA\x55\x01\x00" > /dev/ttyUSB0
```

### 2.4 Python 串口编程模板

```python
import serial
import serial.tools.list_ports

# 自动发现串口设备
def find_serial_port(vid=None, pid=None, description_hint=None):
    """查找串口设备

    Args:
        vid: USB Vendor ID (如 0x10C4 for Silicon Labs)
        pid: USB Product ID
        description_hint: 描述关键字 (如 "CP2102", "CH340")
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if vid and pid:
            if port.vid == vid and port.pid == pid:
                return port.device
        if description_hint and description_hint.lower() in port.description.lower():
            return port.device
    return None

# 标准串口打开模板（无人设备场景）
def open_serial(port, baudrate=115200, timeout=1.0):
    ser = serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,      # 8 数据位
        parity=serial.PARITY_NONE,       # 无校验（无人机数传常用）
        stopbits=serial.STOPBITS_ONE,    # 1 停止位
        timeout=timeout,                 # 读超时
        # write_timeout=0.5,             # 写超时
        # rtscts=True,                   # 硬件流控（某些数传需要）
        # dsrdtr=True,                   # 某些工业设备需要
    )
    # 清空缓冲区
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

# 使用示例
ser = open_serial('/dev/ttyUSB0', 115200)
ser.write(b'AT\r\n')         # 发送 AT 指令
response = ser.readline()    # 读一行
print(response)
ser.close()
```

### 2.5 常见坑与排查

| 症状 | 可能原因 | 排查命令 |
|------|----------|----------|
| `Permission denied` | 不在 `dialout` 组 | `groups $USER` |
| 设备文件不出现 | 驱动未加载 | `dmesg \| tail -20` |
| 拔插后编号变了 | 内核按插入顺序分配 | 用 udev 规则固定设备名 (见下文) |
| 数据乱码 | 波特率不匹配 | `stty -F /dev/ttyUSB0` 核对 |
| `Resource temporarily unavailable` | 另一个进程占用了串口 | `lsof /dev/ttyUSB0`, `fuser /dev/ttyUSB0` |
| 读取数据不完整 | 缓冲区还在接收 / timeout 太短 | 增大 timeout，或改用非阻塞+select |

---

## 三、udev 设备管理器详解

### 3.1 udev 是什么

```
udev (userspace /dev) = Linux 设备管理器

职责:
  1. 监听内核 uevent (设备插入/拔出事件)
  2. 根据规则动态创建/删除 /dev/ 下的设备节点
  3. 设置设备权限、所属组
  4. 创建符号链接（固定设备名）
  5. 触发用户自定义脚本
```

### 3.2 工作流程

```
硬件插入
    │
    ▼
内核检测 → 加载驱动 → 发送 uevent (通过 netlink socket)
    │
    ▼
systemd-udevd 收到 uevent
    │
    ▼
遍历 udev 规则 (/etc/udev/rules.d/ 和 /lib/udev/rules.d/)
    │
    ▼
匹配规则 → 执行动作:
  - 创建 /dev/ttyUSB0
  - 设置权限 MODE="0660"
  - 创建符号链接 SYMLINK+="drone_telemetry"
  - 运行脚本 RUN+="/usr/local/bin/device_connected.sh"
```

### 3.3 udev 规则编写（重点）

规则文件路径: `/etc/udev/rules.d/99-drone-devices.rules`

```bash
# ===== 基本语法 =====
# 匹配键 (确定规则是否适用):
#   SUBSYSTEM=="tty"          子系统为 tty
#   KERNEL=="ttyUSB*"         内核设备名匹配 ttyUSB*
#   ATTRS{idVendor}=="10c4"    USB 厂商 ID (lsusb 可见)
#   ATTRS{idProduct}=="ea60"   USB 产品 ID
#   ATTRS{serial}=="0001"     设备序列号（最精确）
#   ENV{ID_PATH}=="pci-0000:00:14.0-usb-0:1"  USB 物理路径
#
# 赋值键 (确定规则执行什么):
#   SYMLINK+="mydevice"       创建符号链接
#   MODE="0660"               权限
#   GROUP="dialout"           所属组
#   OWNER="root"              所有者
#   RUN+="/path/to/script"    执行的脚本

# ===== 实战示例1: 固定 Pixhawk 飞控的设备名 =====
# 通过 USB VID/PID 识别 Pixhawk (通常是 3D Robotics 或 Hex/ProfiCNC)
SUBSYSTEM=="tty", ATTRS{idVendor}=="26ac", ATTRS{idProduct}=="0011", \
    SYMLINK+="pixhawk", MODE="0666"

# ===== 实战示例2: 通过物理 USB 端口固定名称 =====
# 无论插什么 USB-TTL，只要插在同一个物理口，名字不变
# 最稳定方案：适合工业环境（设备可能更换但端口固定）
SUBSYSTEM=="tty", KERNELS=="1-1.2", SYMLINK+="radio_telemetry"

# ===== 实战示例3: 多传感器统一管理 =====
# GPS 模块 (u-blox 芯片)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1546", ATTRS{idProduct}=="01a8", \
    SYMLINK+="gps_ublox", GROUP="dialout", MODE="0660"

# 数传电台 (SiK Radio, 通常用 CP2102)
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
    SYMLINK+="sik_radio", GROUP="dialout", MODE="0660"

# 激光雷达 (LD19 / LD06 等)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", \
    SYMLINK+="lidar", GROUP="dialout", MODE="0660"

# ===== 实战示例4: 设备插入后自动启动服务 =====
SUBSYSTEM=="tty", ATTRS{idVendor}=="26ac", ACTION=="add", \
    RUN+="/bin/systemctl start mavlink-router.service"

SUBSYSTEM=="tty", ATTRS{idVendor}=="26ac", ACTION=="remove", \
    RUN+="/bin/systemctl stop mavlink-router.service"
```

### 3.4 获取设备属性（写规则前必做）

```bash
# 方法1: 查看完整的设备属性链
udevadm info -a -n /dev/ttyUSB0

# 方法2: 实时监听 udev 事件（插拔设备时观察）
udevadm monitor --environment --udev

# 方法3: 触发规则测试（不实际执行）
udevadm test $(udevadm info -q path -n /dev/ttyUSB0)

# 方法4: 让新规则立即生效（不重启）
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 3.5 调试 udev 规则

```bash
# 查看 udev 日志
sudo journalctl -u systemd-udevd -f

# 或者开启详细日志
sudo udevadm control --log-priority=debug
# 调试完后恢复
sudo udevadm control --log-priority=info
```

---

## 四、sysfs 与设备信息

### 4.1 sysfs 文件系统

```
/sys 是一个内存文件系统，暴露了内核设备模型的完整信息。

/sys/
├── class/          # 按功能分类 (tty, net, i2c, gpio, ...)
│   ├── tty/
│   │   └── ttyUSB0/  → ../../devices/pci0000:00/.../ttyUSB0
│   └── net/
│       └── eth0/
├── bus/            # 按总线类型 (usb, pci, i2c, spi, ...)
│   └── usb/
│       └── devices/
│           └── 1-1/    # USB bus 1, port 1
│               └── 1-1:1.0/  # interface 0
├── devices/        # 所有设备树
└── kernel/         # 内核参数
```

### 4.2 实用查询

```bash
# 查看 USB 设备的完整拓扑
lsusb -t

# 查看设备的 sysfs 路径
udevadm info -q path -n /dev/ttyUSB0
# 输出: /devices/pci0000:00/0000:00:14.0/usb1/1-1/1-1:1.0/ttyUSB0/tty/ttyUSB0

# 从 sysfs 读取设备属性
cat /sys/class/tty/ttyUSB0/device/uevent
# USB 厂商信息
cat /sys/class/tty/ttyUSB0/device/../idVendor
cat /sys/class/tty/ttyUSB0/device/../idProduct
```

---

## 五、无人系统设备集成中的典型场景

### 5.1 地面站设备拓扑

```
工控机 (运行 Linux)
│
├── /dev/pixhawk        → 飞控数传 (USB-TTL, CP2102)
├── /dev/gps_ublox      → GPS/RTK 基站 (USB-TTL)
├── /dev/sik_radio      → 数传电台 (USB-TTL)
├── /dev/lidar          → 激光雷达 (USB-TTL, CH340)
├── /dev/camera_ptz     → 云台控制 (RS-485 转 USB)
├── /dev/can0           → CAN 总线 (USB2CAN)
└── eth0                → 地面站组网 / 视频流
```

### 5.2 设备健康检查脚本

```bash
#!/bin/bash
# check_devices.sh - 巡检所有设备是否在线

DEVICES=(
    "/dev/pixhawk:飞控数传"
    "/dev/gps_ublox:GPS模块"
    "/dev/sik_radio:数传电台"
    "/dev/lidar:激光雷达"
)

for entry in "${DEVICES[@]}"; do
    dev="${entry%%:*}"
    name="${entry##*:}"
    if [ -e "$dev" ]; then
        echo "[OK] $name ($dev) 在线"
    else
        echo "[FAIL] $name ($dev) 离线!"
    fi
done
```

---

## 六、关键总结

| 概念 | 一句话 |
|------|--------|
| `/dev/ttyUSB0` vs `/dev/ttyACM0` | USB-TTL 芯片 vs USB CDC-ACM 协议 |
| Major/Minor 号 | 主号定位驱动，次号区分实例 |
| udev 规则 | 设备热插拔时的自动配置机制 |
| 固定设备名 | 核心方案：USB 物理路径 > 序列号 > VID/PID |
| `dialout` 组 | 90% 串口权限问题的答案 |
| `udevadm` | 调试三板斧：`info` / `monitor` / `test` |
