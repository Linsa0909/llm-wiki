---
title: 一、关于 socket 的介绍
type: concept
summary: ​	Socket 又称 "套接字"，应用程序通常通过 "套接字" 向网络发出请求或者应答网络请求，使主机间或者一台计算机上的进程间可以通讯。python中提供了两个基本的 Socket 模块：服务端 Socket 和客户端 Socket，当创建了一个服务端 Socket 后，这个 Socket 就会在本机的一个端口上等
tags:
  - 导入
links:
sources:
  - raw/imports/20260709-171413/Socket-套接字.md
---
# 一、关于 socket 的介绍

## 导入来源：Socket-套接字.md

## Socket 套接字

# 一、关于 socket 的介绍

​	Socket 又称 "套接字"，应用程序通常通过 "套接字" 向网络发出请求或者应答网络请求，使主机间或者一台计算机上的进程间可以通讯。python中提供了两个基本的 Socket 模块：服务端 Socket 和客户端 Socket，当创建了一个服务端 Socket 后，这个 Socket 就会在本机的一个端口上等待连接，当客户端 Socket 访问这个端口，两者完成连接后就能够进行交互了。


二、创建套接字对象（Socket 的实例化）
在使用 Socket 进行编程时，需要先实例化一个 Scoket 类，Python 中，我们用 **socket（）函数来创建套接字**。

关于 socket 函数的用法：

**scoket(family,type[,protocol])**
第一个参数 family 是指定应用程序使用的通信协议的协议族，有：

| Family参数      | 描述                               |
| --------------- | ---------------------------------- |
| socket.AF_UNIX  | 只能够用于单一的Unix系统进程间通信 |
| socket.AF_INET  | 服务器之间网络通信                 |
| socket.AF_INET6 | IPv6                               |

默认值为 AF_INET



第二个参数 type 为要创建套接字的类型

Type参数

| Type参数           | 描述                                             |
| ------------------ | ------------------------------------------------ |
| socket.SOCK_STREAM | 流式socket , 当使用TCP时选择此参数               |
| socket.SOCK_DGRAM  | 数据报式socket ,当使用UDP时选择此参数            |
| socket.SOCK_RAW    | 原始套接字，允许对底层协议如IP、ICMP进行直接访问 |



| protocol（可选）指明所要接收的协议类型，通常为 0 或者不填 | 描述                                                         |
| --------------------------------------------------------- | ------------------------------------------------------------ |
| socket.IPPROTO_RAW                                        | 相当于protocol=255，此时socket只能用来发送IP包，而不能接收任何的数据。发送的数据需要自己填充IP包头，并且自己计算校验和。 |
| socket.IPPROTO_IP                                         | 相当于protocol=0，此时用于接收任何的IP数据包。其中的校验和和协议分析由程序自己完成。 |
|                                                           |                                                              |



一个简单的 TCP 类型的 Socket

测试代码：

```
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(s)
print(type(s))
```







## 三、套接字对象方法（Socket 常用函数）



#### 1.bind函数

该函数是服务端函数，会将之前创建的套接字与指定的IP地址和端口进行绑定，使用点直接调用该方法，以元组（host, port）的形式表示地址。

比如我们绑定本地的 12345 端口：

```
s.bind(('127.0.0.1', 12345))
```

注意这里用到了两次括号，因为 bind 方法的参数需要是一个包含主机地址和端口号的元组。
