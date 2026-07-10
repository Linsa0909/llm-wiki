---
title: 二、Python struct 完全指南
type: concept
summary: 
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-163558/二进制协议解析指南.md
---
# 二、Python struct 完全指南

## 导入来源：二进制协议解析指南.md

## 二、Python struct 完全指南

### 2.1 格式字符速查

```python
import struct

# ===== 格式符 =====
# b: int8    B: uint8
# h: int16   H: uint16
# i: int32   I: uint32
# q: int64   Q: uint64
# f: float32 (单精度)
# d: float64 (双精度)
# c: char    s: string (bytes)
# x: 填充字节 (跳过)

# ===== 字节序前缀 =====
# >  : 大端 (网络序)
# <  : 小端 (Intel序)
# @  : 本地序 (依赖CPU，不推荐用于协议)
# !  : 网络序 (同>，但标准对齐)

# ===== 常用组合 =====
data = b'\x01\x02\x03\x04\x05\x06\x07\x08'

# 解析两个 uint16 (大端)
a, b = struct.unpack('>HH', data[:4])   # a=258, b=772

# 解析 uint32 + float32 (小端)
val, fval = struct.unpack('<If', data)  # val=67305985, fval=...

# 打包（构造字节）
packed = struct.pack('>BBH', 0xAA, 0x01, 256)  # 帧头+类型+长度
# → b'\xaa\x01\x01\x00'
```

### 2.2 实战模板：解析遥测帧

```python
import struct
from dataclasses import dataclass
from typing import Tuple

@dataclass
class TelemetryFrame:
    """自定义遥测帧结构"""
    header: int      # uint16, 帧头 0xAA55
    version: int     # uint8
    msg_type: int    # uint8
    payload_len: int # uint16
    # 载荷字段 (按 msg_type 不同)
    # 0x01: 心跳
    # 0x02: 传感器数据
    temperature: float = 0.0  # float32
    humidity: float = 0.0     # float32
    pressure: float = 0.0     # float32
    crc: int = 0              # uint16, CRC16-Modbus

    @classmethod
    def parse_header(cls, data: bytes) -> Tuple[int, int, int, int]:
        """解析帧头部分"""
        if len(data) < 6:
            raise ValueError(f"数据太短: {len(data)} bytes, 至少需要6")
        header, version, msg_type, payload_len = struct.unpack('>HBBH', data[:6])
        return header, version, msg_type, payload_len

    @classmethod
    def parse_sensor_payload(cls, payload: bytes):
        """解析传感器载荷"""
        if len(payload) < 12:
            raise ValueError(f"载荷太短: {len(payload)}, 传感器数据需要12字节")
        temp, hum, press = struct.unpack('<fff', payload[:12])
        return temp, hum, press

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TelemetryFrame':
        """完整解析一帧"""
        offset = 0

        # 1. 解析帧头
        header, version, msg_type, payload_len = cls.parse_header(data)
        offset += 6

        frame = cls(
            header=header,
            version=version,
            msg_type=msg_type,
            payload_len=payload_len,
        )

        if header != 0xAA55:
            raise ValueError(f"帧头错误: 0x{header:04X}, 期望 0xAA55")

        # 2. 解析载荷
        payload = data[offset:offset + payload_len]
        offset += payload_len

        if msg_type == 0x02:  # 传感器数据
            frame.temperature, frame.humidity, frame.pressure = \
                cls.parse_sensor_payload(payload)

        # 3. 解析 CRC
        if offset + 2 <= len(data):
            frame.crc = struct.unpack('<H', data[offset:offset + 2])[0]

        return frame
```

---
