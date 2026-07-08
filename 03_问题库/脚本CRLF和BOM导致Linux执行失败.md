# 脚本 CRLF/BOM 导致 Linux 执行失败

## 现象

```text
/usr/bin/env: No such file or directory
syntax error: unexpected end of file
```

## 原因

Windows 写出的 shell 脚本可能带 BOM 或 CRLF。Linux 执行 shebang 时会把不可见字符也当作路径的一部分。

## 解决

统一写成 UTF-8 无 BOM + LF。

临时修复命令：

```bash
find . -name "*.sh" -type f -exec sed -i '1s/^\xEF\xBB\xBF//' {} \; -exec sed -i 's/\r$//' {} \;
chmod +x *.sh scripts/*.sh docker/*.sh
```