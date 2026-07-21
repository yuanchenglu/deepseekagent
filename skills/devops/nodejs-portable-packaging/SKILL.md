---
name: nodejs-portable-packaging
title: Node.js 应用便携版打包指南
description: 将 Node.js 应用打包成便携版（单文件可执行程序或便携目录），支持 Windows、macOS、Linux 三平台，可放到U盘直接运行。
triggers:
  - nodejs portable packaging
  - pkg nodejs executable
  - nodejs u盘运行
  - nodejs 便携版
  - pkg 打包失败
  - node:sqlite pkg
---

# Node.js 应用便携版打包指南

## 概述

将 Node.js 应用打包成便携版（单文件可执行程序或便携目录），支持 Windows、macOS、Linux 三平台，可放到U盘直接运行。

## 常用工具

### 1. pkg（推荐用于简单应用）
- 将 Node.js 应用打包成单可执行文件
- 支持 node18 目标（node20+ 支持不稳定）
- 不支持 Node.js 22.5+ 新特性（如 `node:sqlite`）

### 2. Node.js 便携版 + 项目文件（通用方案）
- 下载各平台 Node.js 便携版
- 与项目文件一起打包
- 通过启动脚本运行

## 打包流程（pkg 方案）

### 前提条件
```bash
npm install -g pkg@latest
```

### package.json 配置
```json
{
  "bin": {
    "my-app": "./bin/entry.cjs"
  },
  "pkg": {
    "scripts": [
      "dist/**/*.js"
    ],
    "assets": [
      "dist/public/**/*",
      "node_modules/some-native-module/prebuilds/**/*"
    ],
    "targets": [
      "node18-win-x64",
      "node18-linux-x64",
      "node18-macos-x64",
      "node18-macos-arm64"
    ]
  }
}
```

### 打包命令
```bash
# 单平台
pkg . --targets node18-linux-x64 --output my-app-linux

# 多平台
pkg . --targets node18-win-x64,node18-linux-x64,node18-macos-x64,node18-macos-arm64
```

## 常见问题与解决方案

### 问题 1：ESM 模块不兼容
**错误**：`Error [ERR_REQUIRE_ESM]: require() of ES Module not supported`

**解决**：创建 CommonJS 入口文件
```javascript
// bin/entry.cjs
const { spawn } = require('child_process');
const path = require('path');

const serverEntry = path.join(__dirname, '..', 'dist', 'server.js');
spawn(process.execPath, [serverEntry], { stdio: 'inherit' });
```

### 问题 2：便携模式数据目录
**需求**：将数据存储在可执行文件所在目录

**解决**：在入口添加便携补丁
```javascript
// === Portable Mode ===
const _portable_path = require('path');
const _portable_fs = require('fs');

const _isPortable = process.env.MY_APP_PORTABLE === 'true' || 
                   process.argv.includes('--portable');

if (_isPortable) {
  const _exeDir = _portable_path.dirname(process.execPath);
  const _dataDir = _portable_path.join(_exeDir, 'data');
  
  if (!_portable_fs.existsSync(_dataDir)) {
    _portable_fs.mkdirSync(_dataDir, { recursive: true });
  }
  
  process.env.HOME = _dataDir;
  process.env.USERPROFILE = _dataDir;
  process.env.MY_APP_HOME = _portable_path.join(_dataDir, '.myapp');
  
  console.log('[Portable] Data directory:', _dataDir);
}
// === End Portable Mode ===
```

**注意**：使用 `_portable_` 前缀避免与打包后的代码变量冲突。

**⚠️ 重要警告：当捆绑 Node.js 运行时时**

如果你使用**完整独立版**方案（捆绑 Node.js 运行时），`process.execPath` 会指向捆绑的 `node` 可执行文件，而不是应用目录。这会导致数据目录创建在错误位置（如 `node/data/` 而不是应用根目录的 `data/`）。

**解决方案**：使用环境变量传递脚本目录

```javascript
// 修改后的便携补丁
if (_isPortable) {
  // 优先使用 SCRIPT_DIR 环境变量（由启动脚本设置）
  const _scriptDir = process.env.SCRIPT_DIR || _portable_path.dirname(process.execPath);
  const _dataDir = _portable_path.join(_scriptDir, 'data');
  
  if (!_portable_fs.existsSync(_dataDir)) {
    _portable_fs.mkdirSync(_dataDir, { recursive: true });
  }
  
  process.env.HOME = _dataDir;
  process.env.USERPROFILE = _dataDir;
  process.env.MY_APP_HOME = _portable_path.join(_dataDir, '.myapp');
  
  console.log('[Portable] Data directory:', _dataDir);
}
```

对应的启动脚本需要设置 `SCRIPT_DIR`：

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
mkdir -p "$DATA_DIR"

export MY_APP_PORTABLE=true
export SCRIPT_DIR="$SCRIPT_DIR"  # 传递给应用
export MY_APP_HOME="$DATA_DIR/.myapp"

exec "$NODE_DIR/bin/node" "$SCRIPT_DIR/dist/server.js" --portable "$@"
```

**⚠️ 重要警告：当捆绑 Node.js 运行时时**

如果你使用**完整独立版**方案（捆绑 Node.js 运行时），`process.execPath` 会指向捆绑的 `node` 可执行文件，而不是应用目录。这会导致数据目录创建在错误位置（如 `node/data/` 而不是应用根目录的 `data/`）。

**解决方案**：使用环境变量传递脚本目录

```javascript
// 修改后的便携补丁
if (_isPortable) {
  // 优先使用 SCRIPT_DIR 环境变量（由启动脚本设置）
  const _scriptDir = process.env.SCRIPT_DIR || _portable_path.dirname(process.execPath);
  const _dataDir = _portable_path.join(_scriptDir, 'data');
  
  if (!_portable_fs.existsSync(_dataDir)) {
    _portable_fs.mkdirSync(_dataDir, { recursive: true });
  }
  
  process.env.HOME = _dataDir;
  process.env.USERPROFILE = _dataDir;
  process.env.MY_APP_HOME = _portable_path.join(_dataDir, '.myapp');
  
  console.log('[Portable] Data directory:', _dataDir);
}
```

对应的启动脚本需要设置 `SCRIPT_DIR`：

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
mkdir -p "$DATA_DIR"

export MY_APP_PORTABLE=true
export SCRIPT_DIR="$SCRIPT_DIR"  # 传递给应用
export MY_APP_HOME="$DATA_DIR/.myapp"

exec "$NODE_DIR/bin/node" "$SCRIPT_DIR/dist/server.js" --portable "$@"
```

### 问题 3：原生模块（node-pty, sqlite3 等）
**错误**：`Cannot find module` 或 `Module did not self-register`

**解决**：
1. 在 `pkg.assets` 中包含预编译二进制文件
2. 运行时重新编译：`npm rebuild module-name`
3. 或使用纯 JavaScript 替代方案

### 问题 4：node:sqlite 不支持（pkg 5.8.1）
**错误**：`Error! Cannot read file, ENOENT node:sqlite`

**原因**：pkg 5.8.1 不支持 Node.js 22.5+ 的 `node:sqlite` 内置模块

**解决**：使用 Node.js 便携版方案（轻量版或完整版）

#### 轻量便携版（推荐，~150MB）
依赖目标电脑已安装 Node.js 23+，只打包应用代码和关键依赖：

```
my-app-portable/
├── dist/                    # 构建输出
├── node_modules/            # 关键生产依赖
├── bin/                     # 启动入口
├── start.sh                 # Linux/macOS 启动脚本
├── start.bat                # Windows 启动脚本
└── README.txt               # 使用说明
```

**启动脚本示例（轻量版）**：
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
mkdir -p "$DATA_DIR"

export MY_APP_PORTABLE=true
export HOME="$DATA_DIR"
export USERPROFILE="$DATA_DIR"
export MY_APP_HOME="$DATA_DIR/.myapp"

echo "[Portable] Data: $DATA_DIR"
exec node "$SCRIPT_DIR/dist/server.js" --portable "$@"
```

**关键依赖识别**：
```bash
# 必须复制的依赖
deps=("node-pty" "socket.io" "socket.io-client" "eventsource" "js-tiktoken")

# 间接依赖
deps+=("engine.io" "ws" "@socket.io" "debug" "ms")
```

#### 完整独立版（~500MB）
包含 Node.js 运行时，无需目标电脑预装 Node.js：

```bash
# 下载各平台 Node.js 运行时
NODE_VERSION="22.11.0"

# Linux
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz"

# macOS Intel
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-x64.tar.gz"

# macOS ARM
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-arm64.tar.gz"

# Windows
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-win-x64.zip"
```

**启动脚本示例（完整版）**：

**Linux/macOS (`start.sh`)**：
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SCRIPT_DIR  # 必须导出，供应用使用
export DATA_DIR="$SCRIPT_DIR/data"
mkdir -p "$DATA_DIR"

export MY_APP_PORTABLE=true
export HOME="$DATA_DIR"
export MY_APP_HOME="$DATA_DIR/.myapp"

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" = "Darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        NODE_DIR="$SCRIPT_DIR/node-darwin-arm64"
    else
        NODE_DIR="$SCRIPT_DIR/node-darwin-x64"
    fi
else
    NODE_DIR="$SCRIPT_DIR/node-linux-x64"
fi

exec "$NODE_DIR/bin/node" "$SCRIPT_DIR/dist/server.js" --portable "$@"
```

**Windows (`start.bat`)**：
```batch
@echo off
setlocal enabledelayedexpansion

:: 设置脚本目录（Windows 使用 %~dp0 获取脚本所在目录）
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

:: 设置数据目录
set DATA_DIR=%SCRIPT_DIR%\data
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

:: 设置环境变量
set MY_APP_PORTABLE=true
set SCRIPT_DIR=%SCRIPT_DIR%
set HOME=%DATA_DIR%
set MY_APP_HOME=%DATA_DIR%\.myapp

:: 检测 Node.js 目录
set NODE_DIR=%SCRIPT_DIR%\node-win-x64

:: 启动应用
cd /d "%SCRIPT_DIR%"
"%NODE_DIR%\node.exe" "%SCRIPT_DIR%\dist\server.js" --portable

pause
```

**⚠️ 关键：SCRIPT_DIR 必须导出**

当捆绑 Node.js 运行时时，`process.execPath` 指向的是 `node` 可执行文件而非应用目录。应用代码中必须使用 `process.env.SCRIPT_DIR` 来确定数据目录位置：

```javascript
// 应用代码中的便携补丁
const _portable_path = require('path');
const _portable_fs = require('fs');

const _isPortable = process.env.MY_APP_PORTABLE === 'true' || 
                   process.argv.includes('--portable');

if (_isPortable) {
  // 优先使用 SCRIPT_DIR 环境变量
  const _scriptDir = process.env.SCRIPT_DIR || _portable_path.dirname(process.execPath);
  const _dataDir = _portable_path.join(_scriptDir, 'data');
  
  if (!_portable_fs.existsSync(_dataDir)) {
    _portable_fs.mkdirSync(_dataDir, { recursive: true });
  }
  
  process.env.HOME = _dataDir;
  process.env.USERPROFILE = _dataDir;
  process.env.MY_APP_HOME = _portable_path.join(_dataDir, '.myapp');
  
  console.log('[Portable] Data directory:', _dataDir);
}
```

### 问题 5：pkg 变量命名冲突
**错误**：打包成功但运行时出现 `SyntaxError: Identifier 'fs' has already been declared`

**原因**：pkg 将补丁代码注入到打包后的文件中，与现有变量名冲突

**解决**：在便携补丁中使用唯一前缀的变量名
```javascript
// 错误 - 可能冲突
const fs = require('fs');
const path = require('path');

// 正确 - 使用唯一前缀
const _portable_fs = require('fs');
const _portable_path = require('path');
```

### 问题 6：pkg 目标版本选择
**建议**：使用 `node18` 而非 `node20` 或 `node23`
- pkg 5.8.1 对 node20+ 支持不稳定
- node18 是最稳定的打包目标

```json
{
  "pkg": {
    "targets": [
      "node18-win-x64",
### 问题 4：node:sqlite 不支持（pkg 5.8.1）
**错误**：`Error! Cannot read file, ENOENT node:sqlite`

**原因**：pkg 5.8.1 不支持 Node.js 22.5+ 的 `node:sqlite` 内置模块

**解决**：使用 Node.js 便携版方案（轻量版或完整版）

#### 轻量便携版（推荐，~150MB）
依赖目标电脑已安装 Node.js 23+，只打包应用代码和关键依赖：

```
my-app-portable/
├── dist/                    # 构建输出
├── node_modules/            # 关键生产依赖（筛选复制）
├── bin/                     # 启动入口
├── start.sh                 # Linux/macOS 启动脚本
├── start.bat                # Windows 启动脚本
└── README.txt               # 使用说明
```

**启动脚本示例（轻量版）**：
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
mkdir -p "$DATA_DIR"

export MY_APP_PORTABLE=true
export HOME="$DATA_DIR"
export USERPROFILE="$DATA_DIR"
export MY_APP_HOME="$DATA_DIR/.myapp"

echo "[Portable] Data: $DATA_DIR"
exec node "$SCRIPT_DIR/dist/server.js" --portable "$@"
```

**关键依赖识别**：
```bash
# 必须复制的依赖
deps=("node-pty" "socket.io" "socket.io-client" "eventsource" "js-tiktoken")

# 间接依赖
deps+=("engine.io" "ws" "@socket.io" "debug" "ms")
```

#### 完整独立版（~500MB）
包含 Node.js 运行时，无需目标电脑预装 Node.js：

```bash
# 下载各平台 Node.js 运行时
NODE_VERSION="22.11.0"

# Linux
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz"

# macOS Intel
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-x64.tar.gz"

# macOS ARM
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-arm64.tar.gz"

# Windows
url="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-win-x64.zip"
```

**启动脚本示例（完整版）**：

**Linux/macOS (`start.sh`)**：
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SCRIPT_DIR  # 必须导出，供应用使用
export DATA_DIR="$SCRIPT_DIR/data"
mkdir -p "$DATA_DIR"

export MY_APP_PORTABLE=true
export HOME="$DATA_DIR"
export MY_APP_HOME="$DATA_DIR/.myapp"

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" = "Darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        NODE_DIR="$SCRIPT_DIR/node-darwin-arm64"
    else
        NODE_DIR="$SCRIPT_DIR/node-darwin-x64"
    fi
else
    NODE_DIR="$SCRIPT_DIR/node-linux-x64"
fi

exec "$NODE_DIR/bin/node" "$SCRIPT_DIR/dist/server.js" --portable "$@"
```

**Windows (`start.bat`)**：
```batch
@echo off
setlocal enabledelayedexpansion

:: 设置脚本目录（Windows 使用 %~dp0 获取脚本所在目录）
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

:: 设置数据目录
set DATA_DIR=%SCRIPT_DIR%\data
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

:: 设置环境变量
set MY_APP_PORTABLE=true
set SCRIPT_DIR=%SCRIPT_DIR%
set HOME=%DATA_DIR%
set MY_APP_HOME=%DATA_DIR%\.myapp

:: 检测 Node.js 目录
set NODE_DIR=%SCRIPT_DIR%\node-win-x64

:: 启动应用
cd /d "%SCRIPT_DIR%"
"%NODE_DIR%\node.exe" "%SCRIPT_DIR%\dist\server.js" --portable

pause
```

**⚠️ 关键：SCRIPT_DIR 必须导出**

当捆绑 Node.js 运行时时，`process.execPath` 指向的是 `node` 可执行文件而非应用目录。应用代码中必须使用 `process.env.SCRIPT_DIR` 来确定数据目录位置：

```javascript
// 应用代码中的便携补丁
const _portable_path = require('path');
const _portable_fs = require('fs');

const _isPortable = process.env.MY_APP_PORTABLE === 'true' || 
                   process.argv.includes('--portable');

if (_isPortable) {
  // 优先使用 SCRIPT_DIR 环境变量
  const _scriptDir = process.env.SCRIPT_DIR || _portable_path.dirname(process.execPath);
  const _dataDir = _portable_path.join(_scriptDir, 'data');
  
  if (!_portable_fs.existsSync(_dataDir)) {
    _portable_fs.mkdirSync(_dataDir, { recursive: true });
  }
  
  process.env.HOME = _dataDir;
  process.env.USERPROFILE = _dataDir;
  process.env.MY_APP_HOME = _portable_path.join(_dataDir, '.myapp');
  
  console.log('[Portable] Data directory:', _dataDir);
}
```

**自动下载 Node.js 脚本**：

为简化用户操作，可以创建自动下载脚本：

**download-nodejs.sh** (Linux/macOS):
```bash
#!/bin/bash
NODE_VERSION="22.11.0"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检测平台
OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
    Linux*) PLATFORM="linux" ;;
    Darwin*) PLATFORM="darwin" ;;
    *) echo "不支持: $OS"; exit 1 ;;
esac

if [ "$ARCH" = "x86_64" ]; then ARCH="x64"; fi
if [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi

FILENAME="node-v${NODE_VERSION}-${PLATFORM}-${ARCH}.tar.gz"
URL="https://nodejs.org/dist/v${NODE_VERSION}/${FILENAME}"
NODE_DIR="$SCRIPT_DIR/node-${PLATFORM}-${ARCH}"

# 下载并解压
curl -L -o "/tmp/$FILENAME" "$URL"
mkdir -p "$NODE_DIR"
tar -xzf "/tmp/$FILENAME" -C "$NODE_DIR" --strip-components=1
rm "/tmp/$FILENAME"

echo "✓ Node.js 下载完成: $NODE_DIR"
```

**download-nodejs.bat** (Windows):
```batch
@echo off
set "NODE_VERSION=22.11.0"
set "SCRIPT_DIR=%~dp0"
set "FILENAME=node-v%NODE_VERSION%-win-x64.zip"
set "URL=https://nodejs.org/dist/v%NODE_VERSION%/%FILENAME%"
set "NODE_DIR=%SCRIPT_DIR%node-win-x64"

powershell -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%TEMP%\%FILENAME%'"
powershell -Command "Expand-Archive -Path '%TEMP%\%FILENAME%' -DestinationPath '%SCRIPT_DIR%'"
move "%SCRIPT_DIR%\node-v%NODE_VERSION%-win-x64" "%NODE_DIR%"
del "%TEMP%\%FILENAME%"

echo Node.js 下载完成: %NODE_DIR%
pause
```

## 验证清单

- [ ] 在干净环境测试（无 Node.js 安装）
- [ ] 验证数据目录正确创建
- [ ] 测试各平台启动脚本
- [ ] 检查日志输出路径
- [ ] 验证端口占用处理
- [ ] 测试热更新/重启功能

## 快速决策流程

```
能否使用 pkg?
├── 使用 Node.js 22.5+ 新特性 (node:sqlite)?
│   └── 是 → 使用 Node.js 便携版方案
├── 复杂的原生模块依赖?
│   └── 是 → 使用 Node.js 便携版方案
└── 否 → 使用 pkg（单文件，更简单）

选择便携版方案:
├── 目标电脑可预装 Node.js 23+?
│   └── 是 → 轻量便携版 (~150MB)
└── 否 → 完整独立版 (~500MB，含运行时)
```

## 文件大小参考

| 方案 | 大小 | 说明 |
|------|------|------|
| pkg 单文件 | 50-200MB | 最简单，但有兼容性限制 |
| 轻量便携版 | 150-200MB | 需目标电脑预装 Node.js |
| 完整独立版 | 300-500MB | 完全独立，含 Node.js 运行时 |
| 含 Chromium/Electron | 500MB+ | 桌面应用方案 |

## 相关工具

- **nexe**: 另一个 Node.js 打包工具
- **boxednode**: 更底层的打包方案
- **electron-builder**: 适用于 Electron 应用
