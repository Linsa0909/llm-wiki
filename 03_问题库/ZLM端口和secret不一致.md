# ZLM 端口和 secret 不一致

## 现象

```text
curl: (7) Failed to connect to 127.0.0.1 port 8090
```

或 API 返回鉴权失败。

## 原因

ZLMediaKit 容器内部 HTTP 端口是 80。若使用 host 网络而不是端口映射，宿主机访问 8090 不会通。另一个问题是没有挂载固定 config 时，ZLM 可能自动生成随机 secret。

## 解决

- 使用 `8090:80` 端口映射。
- 挂载固定配置：`zlm/media/conf/config.ini`。
- 固定 secret：`OCdMstJ9V4XmUvELLo7Vn7DLgmHPu9co`。