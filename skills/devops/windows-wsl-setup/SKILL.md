---
name: windows-wsl-setup
title: Windows WSL2 安装与故障排查
description: 在 Windows 10/11（含 LTSC）上安装和配置 WSL2 的完整指南，包含 SSH 远程操作下的编码处理技巧
version: 1.0
---

# Windows WSL2 安装与故障排查

## 使用场景

通过 SSH 远程管理 Windows 机器时，需要安装或修复 WSL2（含 Linux 发行版）。

## 前提条件

- Windows 10 2004+ 或 Windows 11（或 LTSC 2021）
- 已启用 OpenSSH Server（参考 `windows-openssh-server-setup` 技能）
- 管理员凭据

## 标准安装（Windows 10/11 常规版）

```powershell
# 1. 启用 WSL 功能（一行搞定）
wsl --install

# 如果已启用功能但缺发行版
wsl --install -d Ubuntu

# 查看可用发行版
wsl --list --online
```

## LTSC 版安装（关键：不走 Store）

Windows 10 LTSC 2021（build 19044）不存在 Microsoft Store 的 WSL 发行版通道，
`wsl --install` 会失败或假成功。

### 检查当前状态

```powershell
# 检查 WSL 功能是否启用
dism /online /get-featureinfo /featurename:Microsoft-Windows-Subsystem-Linux
dism /online /get-featureinfo /featurename:VirtualMachinePlatform

# 检查 WSL2 内核文件
dir C:\Windows\System32\lxss\tools\kernel
```

### 分步安装 LTSC

```powershell
# 1. 启用 WSL 功能（若未启用）
dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 2. 下载 WSL2 Linux 内核更新包（~15MB，下载后需要管理员权限安装）
#    使用计划任务以 SYSTEM 权限绕过 UAC：
schtasks /create /tn WslKernelInstall /tr "msiexec /i %TEMP%\wsl_update_x64.msi /quiet /norestart" /sc once /st 00:01 /rl highest /ru SYSTEM /f
schtasks /run /tn WslKernelInstall

# 3. 安装发行版（从微软 CDN 下载 Ubuntu Appx 包 ~1GB）
curl.exe -L -o "%TEMP%\Ubuntu.appxbundle" "https://aka.ms/wslubuntu2204"
Add-AppxPackage -Path "%TEMP%\Ubuntu.appxbundle"
```

### 验证安装

```powershell
wsl --list (wsl -l)
wsl --status
```

## SSH 远程操作 Windows 的编码问题

### 现象

通过 sshpass/SSH 连接中文 Windows 时，输出为 UTF-16 LE 编码，
直接显示为夹杂 `\u0000` 的空隙乱码。

### 解决方案

```bash
# 方式一：通过 iconv 转换（推荐）
sshpass -p 'password' ssh user@host 'cmd /c "wsl --status"' 2>&1 | iconv -f UTF-16LE -t UTF-8//IGNORE

# 方式二：使用 PowerShell + Out-File(ASCII) 输出到文件再读取
sshpass -p 'password' ssh user@host powershell -Command "cmdlet > \"$env:TEMP\\out.txt\"; Get-Content \"$env:TEMP\\out.txt\""
```

### 注意

- iconv 在某些破损的 UTF-16 流上会报 `incomplete character` 错误，
  加 `//IGNORE` 跳过
- 对于纯英文输出，`chcp 437` 设定代码页可以避免 UTF-16 问题
- 嵌套引号（SSH → cmd → PowerShell）极易出错，优先用批处理脚本文件

## 常见错误

### MSI 安装错误 1603

WSL2 内核更新 MSI 返回 1603（Fatal error during installation）：
- 原因通常是 UAC 拦截或系统权限不足
- 解法：用计划任务以 SYSTEM 身份运行（见上方 `schtasks` 示例）
- 若仍失败，检查 Windows Update 是否最新

### wsl --install 假成功

LTSC 上 `wsl --install` 可能返回 SUCCESS 但实际未安装发行版。
因为该命令在 LTSC 上仅确认了收件箱功能已启用，不会从 Store 下载发行版。
**必须手动下载 Appx 包安装。**

### wsl 命令输出帮助文本

`wsl -l -v` 等命令返回帮助文本而非错误信息，说明：
- 没有发行版被安装（exit code 1）
- 或参数不被该 wsl.exe 版本支持（旧版 WSL 不支持 `--verbose`）
