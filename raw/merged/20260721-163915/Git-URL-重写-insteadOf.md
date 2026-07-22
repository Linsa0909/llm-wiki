---
title: Git URL 重写 insteadOf
type: tool
summary: Git 的 URL 重写机制，可在不修改仓库 remote URL 的情况下，将不可访问的域名自动改写为可访问的内网 IP 或替代地址。
tags:
  - Git
  - remote
  - insteadOf
  - ghostcloud
  - 内网访问
  - 排障
links:
  - Git
  - Git 常用命令与 ghostcloud.cn 内网访问处理
  - Git 远程仓库域名访问失败：ghostcloud.cn 改走 192.168.2.46
sources:
  - raw/imports/20260714-153922/Git-常用命令与-ghostcloud.cn-内网访问处理.md
---
# Git URL 重写 insteadOf

## 是什么

`url.<base>.insteadOf` 是 Git 的地址重写配置。它会在 Git 访问远程仓库前，把匹配到的 URL 前缀替换成另一个前缀。这个能力适合处理“仓库地址里写的是域名，但当前网络只能访问内网 IP”的场景。

## 本次场景

远程仓库地址使用 `ghostcloud.cn`，但当前环境无法访问该域名；内网 IP `192.168.2.46` 可以访问。因此可以让 Git 在执行 `clone / pull / push / fetch` 时自动把 `ghostcloud.cn` 改写为 `192.168.2.46`。

## HTTP 写法

```bash
git config --global url."http://192.168.2.46/".insteadOf "http://ghostcloud.cn/"
```

## SSH URL 写法

```bash
git config --global url."ssh://git@192.168.2.46/".insteadOf "ssh://git@ghostcloud.cn/"
```

## SCP 风格 SSH 写法

远程地址形如 `git@ghostcloud.cn:org/repo.git` 时使用：

```bash
git config --global url."git@192.168.2.46:".insteadOf "git@ghostcloud.cn:"
```

## 验证

```bash
git config --global --list | grep insteadOf
git remote -v
```

`git remote -v` 仍可能显示原始域名，这是正常的；重写发生在 Git 实际访问远程仓库时。

## 与其他方案对比

| 方案 | 适用情况 | 代价 |
|---|---|---|
| `insteadOf` | 只希望 Git 自动改写访问地址，不想改仓库 remote | 仅影响 Git |
| `git remote set-url` | 单个仓库长期只走内网 IP | 每个仓库都要改，remote 被写死 |
| hosts | 浏览器、SSH、Git 都要改解析 | 需要管理员权限，影响全局 |
