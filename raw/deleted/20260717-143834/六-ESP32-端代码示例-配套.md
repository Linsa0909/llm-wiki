---
title: 六、ESP32 端代码示例（配套）
type: concept
summary: 
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-163558/二进制协议解析指南.md
---
# 六、ESP32 端代码示例（配套）

## 导入来源：二进制协议解析指南.md

## 六、ESP32 端代码示例（配套）

### 6.1 自定义协议发送端

```cpp
// ESP32 Arduino 代码 - 自定义二进制协议发送端
#include <Arduino.h>
#include <DHT.h>  // 温湿度传感器

#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// 帧结构定义
struct TelemetryPacket {
  uint16_t header = 0xAA55;  // 帧头
  uint8_t  version = 0x01;   // 协议版本
  uint8_t  msg_type = 0x02;  // 消息类型: 0x02 = 传感器数据
  uint16_t payload_len = 12; // 载荷长度

  // 载荷: 温湿度气压 (各4字节 float)
  float temperature;
  float humidity;
  float pressure;  // 这里用气压传感器的值，示例用固定值

  uint16_t crc;  // CRC16-Modbus

  // 计算 CRC16-Modbus (校验帧头到载荷末尾)
  void calcCRC() {
    uint8_t* data = (uint8_t*)this;
    size_t len = sizeof(TelemetryPacket) - 2;  // 不含 CRC 字段
    uint16_t crc_val = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
      crc_val ^= data[i];
      for (int j = 0; j < 8; j++) {
        if (crc_val & 0x0001) {
          crc_val = (crc_val >> 1) ^ 0xA001;
        } else {
          crc_val >>= 1;
        }
      }
    }
    crc = crc_val;
  }
};

TelemetryPacket packet;

void setup() {
  Serial.begin(115200);  // USB 串口
  Serial2.begin(115200, SERIAL_8N1, 16, 17);  // 硬件串口2 (TX=17, RX=16)
  dht.begin();
}

void loop() {
  // 读取传感器
  packet.temperature = dht.readTemperature();
  packet.humidity = dht.readHumidity();
  packet.pressure = 1013.25;  // 模拟气压

  // 计算 CRC
  packet.calcCRC();

  // 发送
  Serial2.write((uint8_t*)&packet, sizeof(packet));

  delay(1000);  // 1Hz
}
```

---
