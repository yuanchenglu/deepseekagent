---
name: windows-openssh-server-setup
title: Windows 10 OpenSSH 服务端安装与故障排查
description: 完整的 Windows 10 OpenSSH 服务端安装、配置和常见问题修复指南
version: 1.0
---

# Windows 10 OpenSSH 服务端安装与故障排查

## 安装 OpenSSH 服务端

```powershell
# 检查是否已安装
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

# 安装服务端
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 或使用 DISM
dism /Online /Add-Capability /CapabilityName:OpenSSH.Server~~~~0.0.1.0
```

## 启动并配置服务

```powershell
# 启动服务
Start-Service sshd

# 设置开机自启
Set-Service -Name sshd -StartupType 'Automatic'

# 验证状态
Get-Service sshd
```

## 常见错误：无法启动服务 sshd

### 原因
通常是 OpenSSH.Server 功能未正确安装或配置文件损坏。

### 完整修复脚本

```powershell
# 以管理员身份运行
Write-Host "=== OpenSSH 服务端修复脚本 ===" -ForegroundColor Green

# 1. 停止现有服务
Stop-Service sshd -ErrorAction SilentlyContinue

# 2. 卸载
Remove-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 3. 清理旧配置
Remove-Item -Path "C:\ProgramData\ssh" -Recurse -Force -ErrorAction SilentlyContinue

# 4. 重新安装
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 5. 启动并设置自启
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# 6. 验证
Get-Service sshd
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
```

## 防火墙配置

```powershell
# 创建入站规则
New-NetFirewallRule -Name "OpenSSH-Server" -DisplayName "OpenSSH Server" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

## 配置文件位置

- 主配置：`C:\ProgramData\ssh\sshd_config`
- 主机密钥：`C:\ProgramData\ssh\ssh_host_*`
- 授权密钥（标准用户）：`C:\Users\<用户名>\.ssh\authorized_keys`
- 授权密钥（管理员用户）：**`C:\ProgramData\ssh\administrators_authorized_keys`**
  > ⚠️ 关键区别：如果用户属于 Administrators 组，OpenSSH **强制读取** `administrators_authorized_keys`，而非用户的 `.ssh\authorized_keys`。且必须用 `icacls` 设置显式权限，否则 SSHd 静默忽略：
  > ```cmd
  > icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant "SYSTEM:F" /grant "BUILTIN\Administrators:F"
  > ```
  > 详见 `ssh-key-setup` skill 的完整密钥配置流程。

## 验证安装

```powershell
# 检查端口监听
netstat -an | findstr :22

# 测试本地连接
ssh localhost
```

## 注意事项

1. 必须以管理员身份运行 PowerShell
2. Windows 10 1809+ 和 Windows 11 内置 OpenSSH 客户端，服务端需要手动安装
3. 默认使用密码认证，建议配置密钥认证提高安全性
4. 如需外网访问，还需配置路由器端口转发