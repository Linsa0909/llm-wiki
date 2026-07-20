---
title: Git 常用命令与 ghostcloud.cn 内网访问处理 命令清单
type: tool
summary: 从项目 Markdown 代码块中自动提取的常用命令。
tags:
  - Git
  - Git URL 重写 insteadOf
  - 版本控制
  - 命令
  - 远程仓库
  - ghostcloud
  - insteadOf
  - 排障
  - 项目导入
  - commands
links:
  - Git 工作流
  - Linux Shell
  - Git 常用命令与 ghostcloud.cn 内网访问处理
  - Git
sources:
  - raw/imports/20260714-153922/Git-常用命令与-ghostcloud.cn-内网访问处理.md
---
# Git 常用命令与 ghostcloud.cn 内网访问处理 命令清单

## 导入来源：项目资料包

## 命令清单

- `git config --global user.name "你的名字"`
- `git config --global user.email "你的邮箱"`
- `git config --global --list`
- `git config --list`
- `git init`
- `git clone <url>`
- `git clone <url> <目录名>`
- `git status`
- `git status -s`
- `git add <文件>`
- `git add .`
- `git add -A`
- `git commit -m "提交信息"`
- `git commit -am "信息"`
- `git commit --amend`
- `git restore <文件>`
- `git restore --staged <文件>`
- `git reset HEAD~1`
- `git reset --hard HEAD~1`
- `git log`
- `git log --oneline`
- `git log --graph --oneline --all`
- `git log -p`
- `git log --author="某人"`
- `git blame <文件>`
- `git show <commit-id>`
- `git branch`
- `git branch -a`
- `git branch <分支名>`
- `git switch <分支名>`
- `git switch -c <分支名>`
- `git checkout -b <分支名>`
- `git merge <分支名>`
- `git merge --no-ff <分支名>`
- `git branch -d <分支名>`
- `git branch -D <分支名>`
- `git remote -v`
- `git remote add <别名> <url>`
- `git push <远程名> <分支名>`
- `git push -u origin main`
- `git push origin --delete <分支名>`
- `git pull`
- `git fetch`
- `git pull --rebase`
- `git revert <commit-id>`
- `git reset --soft HEAD~1`
- `git reset --mixed HEAD~1`
- `git reset --hard <commit-id>`
- `git stash`
- `git stash pop`
- `git stash list`
- `git clean -fd`
- `git gc`
- `git reflog`
- `git log --oneline --since="today" --author=$(git config user.name)`
- `git diff main..feature -- src/index.js`
- `git add -p`
- `git rebase -i HEAD~3`
- `git checkout <分支名> -- <文件路径>`
- `git config --global url."http://192.168.2.46/".insteadOf "http://ghostcloud.cn/"`
- `git config --global url."ssh://git@192.168.2.46/".insteadOf "ssh://git@ghostcloud.cn/"`
- `git config --global url."git@192.168.2.46:".insteadOf "git@ghostcloud.cn:"`
- `git config --global --list | grep insteadOf`
- `git remote set-url origin http://192.168.2.46/你的项目路径.git`
