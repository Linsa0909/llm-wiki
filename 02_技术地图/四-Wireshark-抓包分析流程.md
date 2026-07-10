---
title: 四、Wireshark 抓包分析流程
type: concept
summary: 
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-163558/二进制协议解析指南.md
---
# 四、Wireshark 抓包分析流程

## 导入来源：二进制协议解析指南.md

## 四、Wireshark 抓包分析流程

### 4.1 串口抓包

```
1. 确保安装了 USBPcap (Wireshark 安装时勾选)
2. Wireshark → 首页 → USBPcap1 (或其他编号)
3. 过滤器: usb.src == "host" or usb.dst == "host"
4. 找到你的 USB-TTL 设备
5. 发送数据 → 抓包 → 找到对应的 USB 数据包
6. 右键 → Decode As → 选择 RTU 或其他协议

注意: USBPcap 抓的是 USB 包，不是原始串口数据
      需要手动提取 DATA 部分或者用专门的串口监控软件
```

### 4.2 网络协议抓包 (MQTT, TCP)

```
1. 选择网卡 → Capture Filter: port 1883 or port 8883
2. Display Filter:
   - mqtt                          # 所有 MQTT 包
   - mqtt.msgtype == 3             # 只看 PUBLISH
   - mqtt.topic contains "drone"   # 按主题过滤
   - tcp.port == 1883              # TCP 层过滤

3. 关键操作:
   - Follow TCP Stream     → 看完整会话
   - Analyze → Decode As   → 强制解析为特定协议
   - Statistics → IO Graph → 流量可视化
   - Export Specified Packets → 导出特定包
```

### 4.3 分析实战：MQTT PUBLISH 报文

```
原始十六进制 (MQTT PUBLISH):
30 14 00 08 64 72 6F 6E 65 2F 74 65 6D 70 48 65 6C 6C 6F 20 33 30 43

逐字节解析:
  30         = 0011 0000
               0011 = MQTT Control Packet Type = 3 (PUBLISH)
               0000 = DUP=0, QoS=0, Retain=0
  14         = Remaining Length = 20 bytes
  00 08      = Topic Length = 8
  64 72 6F 6E 65 2F 74 65 6D 70 = Topic = "drone/temp"
  48 65 6C 6C 6F 20 33 30 43     = Payload = "Hello 30C"

关键: QoS=0 时没有 Packet Identifier 字段！
```

### 4.4 常见协议过滤速查

```
MQTT:       mqtt, mqtt.msgtype, mqtt.topic, mqtt.qos
HTTP:       http, http.request.method, http.response.code
WebSocket:  websocket, data.data (查看内容)
CoAP:       coap, coap.type, coap.code
DNS:        dns, dns.qry.name
TCP:        tcp.port, tcp.flags.syn, tcp.analysis.retransmission
TLS:        tls.handshake.type, tls.handshake.extensions_server_name
```

---
