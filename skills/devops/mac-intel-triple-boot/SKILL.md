---
name: mac-intel-triple-boot
title: MacBook Pro Intel 三系统引导指南
description: macOS + Windows + Deepin原生UEFI引导配置
author: System
version: 1.0.0
---

# MacBook Pro Intel 三系统引导指南

## 目标
在MacBook Pro 2017 Intel上实现macOS + Windows + Deepin三系统原生引导（Option键选择）

## 关键约束
- 不使用第三方引导助手（rEFInd等）
- 不使用黑苹果方案
- 基于官方UEFI/GPT规范

## 分区架构
```
磁盘布局（GPT）：
1. EFI System Partition (ESP) - macOS - 200MB
2. APFS Container - macOS - ~300GB
3. Microsoft Reserved - 16MB
4. NTFS - Windows - ~300GB
5. EFI System Partition (ESP) - Deepin - 500MB
6. Linux Swap - 16GB
7. ext4 - Deepin - ~剩余空间
8. exFAT - Share共享分区 - 200GB
```

## 安装流程

### 阶段1：macOS准备（所有分区在此创建）
1. 完整安装macOS
2. 打开磁盘工具 → 显示所有设备
3. 创建所有分区：
   - Windows分区（MS-DOS FAT格式，稍后转为NTFS）
   - Deepin ESP分区（MS-DOS FAT，500MB）
   - Deepin根分区（MS-DOS FAT，占位）
   - Share分区（exFAT）

### 阶段2：Windows安装
1. 创建Windows 10/11 UEFI启动盘
2. 按住Option键，选择EFI Boot
3. 安装到预设的Windows分区
4. 删除Boot Camp创建的混合分区表（如存在）

### 阶段3：Deepin安装
1. 使用Deepin启动盘
2. 手动分区：
   - /boot/efi → 独立的500MB ESP分区
   - swap → 16GB
   - / → 剩余空间
3. **关键**：GRUB必须安装到独立ESP，不是主硬盘ESP

## 故障排查

### Windows黑屏
**原因**：NVRAM启动项冲突
**解决**：
```bash
# 在Deepin中
sudo efibootmgr -v  # 查看启动项
sudo efibootmgr -b XXXX -B  # 删除冲突项
```
或重置NVRAM：Cmd+Option+P+R

### Deepin覆盖Windows引导
**原因**：GRUB安装到错误的ESP
**预防**：安装时明确选择独立的Deepin ESP分区

## 官方文档参考
- Apple HT201468: Boot Camp分区表说明
- UEFI Specification 2.9: ESP要求
- Microsoft Windows UEFI安装指南
- Deepin安装手册：手动分区章节

## 验证命令
```bash
# 查看所有ESP分区
diskutil list

# 查看NVRAM启动项
sudo nvram -p | grep boot

# 查看UEFI启动项（在Linux中）
sudo efibootmgr -v
```