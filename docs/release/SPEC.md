# DeepAgent Release Installation System — Shared Contract (SPEC.md)

> **文档定位**：本文件是 DeepAgent Release 安装系统的**共享契约文档**。
> 所有并行任务（31.2~31.11）的工程师/AI Agent 在写代码前**必须先读此文件**，
> 确保接口对齐、路径一致、产物兼容。
>
> **读者**：人类维护者 + AI Agent（一个不读代码的弱 AI 也能按此执行）。
>
> **版本**：0.9.0-alpha.1
> **最后更新**：2025-07-17

---

## 目录

1. [文件布局](#1-文件布局安装后-deepagent-目录结构)
2. [Tarball 结构](#2-tarball-结构打包规则)
3. [VERSION 文件格式](#3-version-文件格式约定)
4. [下载 URL 结构](#4-下载-url-结构)
5. [安装后文件结构](#5-安装后文件结构wrapper-venv-配置保留)
6. [各模块的接口签名](#6-各模块的接口签名)
7. [集成清单](#7-集成清单11-个任务产出核对)

---

## 1. 文件布局（安装后 ~/.deepagent/ 目录结构）

用户执行 `curl -fsSL https://deepseekagent.starseas.org/install.sh | sh` 后，
所有文件安装到 `~/.deepagent/` 目录。精确结构如下：

```
~/.deepagent/                          # 安装根目录（DEEPAGENT_HOME）
├── deepagent/                         # 代码目录（从 tarball 解压）
│   ├── pyproject.toml                 # Python 项目配置（入口点定义在此）
│   ├── uv.lock                        # 依赖锁定文件（可复现安装）
│   ├── requirements.txt               # pip 兼容依赖列表
│   ├── VERSION                        # 版本号文件（纯文本，如 "0.9.0-alpha.1"）
│   ├── cli.py                         # CLI 入口模块
│   ├── run_agent.py                   # Agent 运行入口
│   ├── model_tools.py                 # 模型工具
│   ├── toolsets.py                    # 工具集
│   ├── hermes_constants.py            # 核心常量模块
│   ├── hermes_state.py                # 状态管理
│   ├── hermes_logging.py              # 日志模块
│   ├── hermes_time.py                 # 时间工具
│   ├── utils.py                       # 通用工具
│   ├── deepagent                      # CLI 启动脚本（Python，可执行）
│   ├── agent/                         # Agent 核心逻辑
│   ├── hermes_cli/                    # CLI 子命令模块
│   │   └── main.py                    # 主 CLI 入口（argparse 注册）
│   ├── tools/                         # 内置工具
│   │   ├── registry.py                # 工具注册表
│   │   └── skills_sync.py             # Skills 同步工具
│   ├── gateway/                       # 多平台网关（Telegram/Discord/Slack/Feishu 等）
│   ├── cron/                          # 定时任务模块
│   ├── acp_adapter/                   # ACP 协议适配器
│   ├── plugins/                       # 插件系统
│   ├── skills/                        # 内置 Skills 目录
│   │   └── <skill_name>/SKILL.md     # 每个 skill 的定义文件
│   ├── embedded/                      # 嵌入式 OpenCode 研发小组
│   │   ├── start.sh                   # Embedded team 入口脚本
│   │   ├── config/                    # OpenCode 隔离配置
│   │   └── opencode/                  # OpenCode 二进制（按平台分目录）
│   │       ├── linux-x64/opencode     # Linux x86_64 二进制
│   │       ├── macos-arm64/opencode   # macOS Apple Silicon 二进制
│   │       └── macos-x64/opencode     # macOS Intel 二进制
│   └── webui/                         # WebUI 资源
│       ├── dist/                      # 预构建前端产物
│       ├── electron/                  # Electron 桌面端配置
│       └── package.json              # WebUI 包定义
│
├── .venv/                             # Python 虚拟环境（uv venv 创建）
│   └── bin/                           # venv 可执行文件目录
│       ├── deepagent                  # deepagent 入口点（由 pip/uv 注册）
│       ├── deepagent-agent            # agent 入口点
│       └── deepagent-acp              # ACP 适配器入口点
│
├── .backup/                           # 旧版本备份目录（更新安装时自动创建）
│   ├── deepagent-0.8.0/               # 最近一次备份
│   └── deepagent-0.7.0/               # 更早的备份（保留最近 3 个）
│
├── .env                               # 用户配置文件（**永不被覆盖**）
├── config.yaml                        # 用户 YAML 配置（**永不被覆盖**）
├── logs/                              # 运行日志目录
│   └── install_update.log            # 安装/更新日志
│
└── VERSION                            # 当前安装版本号（纯文本）
```

### 关键路径常量

| 常量名 | 值 | 说明 |
|--------|-----|------|
| `DEEPAGENT_HOME` | `~/.deepagent` | 安装根目录 |
| `DEEPAGENT_CODE_DIR` | `~/.deepagent/deepagent` | 代码目录 |
| `DEEPAGENT_VENV` | `~/.deepagent/.venv` | Python 虚拟环境 |
| `DEEPAGENT_BIN` | `~/.deepagent/.venv/bin` | venv 可执行文件目录 |
| `DEEPAGENT_BACKUP` | `~/.deepagent/.backup` | 备份目录 |
| `DEEPAGENT_BUNDLED_SKILLS` | `~/.deepagent/deepagent/skills` | 内置 Skills 目录 |
| `DEEPAGENT_USER_SKILLS` | `~/.deepagent/skills` | 用户自定义 Skills 目录 |
| `WEBUI_PORT` | `8648` | WebUI 默认端口 |

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEEPAGENT_HOME` | `~/.deepagent` | 可通过环境变量覆盖安装根目录 |
| `DEEPAGENT_VERSION` | `latest` | 指定安装版本 |
| `SKIP_WEBUI_CHECK` | (未设置) | 跳过 WebUI 预构建检查 |
| `SKIP_OPENCODE_CHECK` | (未设置) | 跳过 OpenCode 二进制检查 |

---

## 2. Tarball 结构（打包规则）

### 2.1 文件名

```
deepagent-{VERSION}.tar.gz
deepagent-{VERSION}.sha256
```

示例：`deepagent-0.9.0-alpha.1.tar.gz`

### 2.2 打包规则

打包脚本：`scripts/build-release.sh`

**必须包含的文件/目录：**

| 路径 | 类型 | 说明 |
|------|------|------|
| `pyproject.toml` | 文件 | Python 项目配置，含 `[project.scripts]` 入口点 |
| `uv.lock` | 文件 | 依赖锁定文件 |
| `requirements.txt` | 文件 | pip 兼容依赖列表 |
| `constraints-termux.txt` | 文件 | Termux 约束文件 |
| `VERSION` | 文件 | 版本号文件 |
| `cli.py` | 文件 | CLI 入口模块 |
| `model_tools.py` | 文件 | 模型工具 |
| `run_agent.py` | 文件 | Agent 运行入口 |
| `hermes_state.py` | 文件 | 状态管理 |
| `hermes_constants.py` | 文件 | 核心常量 |
| `hermes_logging.py` | 文件 | 日志模块 |
| `hermes_time.py` | 文件 | 时间工具 |
| `utils.py` | 文件 | 通用工具 |
| `agent/` | 目录 | Agent 核心逻辑 |
| `hermes_cli/` | 目录 | CLI 子命令模块 |
| `tools/` | 目录 | 内置工具 |
| `gateway/` | 目录 | 多平台网关 |
| `cron/` | 目录 | 定时任务 |
| `acp_adapter/` | 目录 | ACP 协议适配器 |
| `plugins/` | 目录 | 插件系统 |
| `skills/` | 目录 | 内置 Skills |
| `embedded/` | 目录 | 嵌入式 OpenCode |
| `webui/dist/` | 目录 | 预构建 WebUI 前端 |
| `webui/bin/` | 目录 | WebUI 启动脚本 |
| `webui/electron/` | 目录 | Electron 桌面端配置 |
| `webui/package.json` | 文件 | WebUI 包定义 |

**必须排除的文件/目录：**

| 排除模式 | 说明 |
|----------|------|
| `__pycache__` | Python 缓存目录 |
| `*.pyc` / `*.pyo` | Python 编译文件 |
| `.git` | Git 元数据 |
| `.venv` / `venv` | Python 虚拟环境 |
| `node_modules` | Node.js 依赖 |
| `dist/releases` | 构建输出（防止嵌套打包） |
| `.DS_Store` | macOS 系统文件 |
| `.coverage` / `htmlcov` | 测试覆盖率文件 |
| `.pytest_cache` | pytest 缓存 |
| `*.egg-info` | Python 包信息 |

### 2.3 入口点定义（pyproject.toml `[project.scripts]`）

```toml
[project.scripts]
deepagent = "hermes_cli.main:main"
deepagent-agent = "run_agent:main"
deepagent-acp = "acp_adapter.entry:main"
```

### 2.4 SHA256 校验和

- 文件名：`deepagent-{VERSION}.sha256`
- 格式：`<hash>  deepagent-{VERSION}.tar.gz`（标准 sha256sum 格式）
- 验证命令：`sha256sum -c deepagent-{VERSION}.sha256`

---

## 3. VERSION 文件格式约定

### 3.1 文件格式

- **类型**：纯文本文件（UTF-8，无 BOM）
- **内容**：版本号字符串，不带 `v` 前缀
- **换行**：允许尾部换行（读取时 `tr -d '[:space:]'` 去除）

### 3.2 版本号格式

遵循 [Semantic Versioning](https://semver.org/) 规范：

```
MAJOR.MINOR.PATCH[-pre-release]
```

**当前版本**：`0.9.0-alpha.1`

**合法示例**：
- `0.9.0`
- `0.9.0-alpha.1`
- `0.9.0-beta.2`
- `0.9.0-rc.3`
- `1.0.0`

**非法示例**：
- `v0.9.0`（不应有 `v` 前缀）
- `0.9`（缺少 PATCH 号）
- `0.9.0.alpha.1`（应用连字符而非点号分隔 pre-release）

### 3.3 版本号读取

所有模块读取版本号时应统一使用以下逻辑：

```python
# Python 示例
from pathlib import Path

def get_current_version() -> str:
    """从 VERSION 文件读取当前版本号"""
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"
```

```bash
# Shell 示例
VERSION=$(cat VERSION | tr -d '[:space:]')
```

---

## 4. 下载 URL 结构

### 4.1 主源（Cloudflare R2）

```
https://deepseekagent.starseas.org/releases/deepagent-{VERSION}.tar.gz
https://deepseekagent.starseas.org/releases/deepagent-{VERSION}.sha256
```

R2 bucket 名称：`deepagent-releases`
R2 自定义域名：`releases.deepseekagent.starseas.org`（通过 Cloudflare DNS 管理）

### 4.2 备用源（GitHub Releases）

```
https://github.com/yuanchenglu/deepseekagent/releases/download/v{VERSION}/deepagent-{VERSION}.tar.gz
https://github.com/yuanchenglu/deepseekagent/releases/download/v{VERSION}/deepagent-{VERSION}.sha256
```

**注意**：GitHub Releases 的 URL 使用 `v` 前缀的 tag 名（`v0.9.0-alpha.1`），但文件名中不含 `v` 前缀。

### 4.3 安装脚本 URL

```
https://deepseekagent.starseas.org/install.sh
```

此 URL 由 Cloudflare Pages Function 处理（`website/functions/install.sh.js`），
根据 `?version=` 参数查询最新版本并 302 重定向到 R2 上的安装脚本。

### 4.4 双源下载降级逻辑

安装脚本（`scripts/install-release.sh`）必须实现以下降级逻辑：

```
1. 尝试从主源 R2 下载 tarball
2. 如果 R2 下载失败（超时/404/网络错误）：
   a. 记录警告日志
   b. 尝试从备用源 GitHub Releases 下载
3. 如果两个源都失败：
   a. 报错退出，提示用户检查网络
4. 下载成功后：
   a. 下载 SHA256 校验和文件
   b. 验证 tarball 完整性
   c. 如果校验失败，报错退出
```

### 4.5 URL 常量

| 常量 | 值 |
|------|-----|
| `R2_BASE_URL` | `https://deepseekagent.starseas.org/releases` |
| `GH_REPO` | `yuanchenglu/deepseekagent` |
| `GH_BASE_URL` | `https://github.com/yuanchenglu/deepseekagent/releases/download` |
| `INSTALL_URL` | `https://deepseekagent.starseas.org/install.sh` |

---

## 5. 安装后文件结构（Wrapper、Venv、配置保留）

### 5.1 Wrapper 脚本

安装完成后，`~/.local/bin/deepagent` 是一个符号链接，指向 `~/.deepagent/.venv/bin/deepagent`：

```
~/.local/bin/deepagent → ~/.deepagent/.venv/bin/deepagent
```

**PATH 配置**：安装脚本将 `~/.local/bin` 添加到用户的 shell profile 中：
- `.zshrc`（macOS 默认）
- `.bashrc` / `.bash_profile`（Linux）
- `.profile`（通用 fallback）
- `config.fish`（Fish shell）

写入格式（以 zsh 为例）：
```bash
# deepagent — added by installer
export PATH="$HOME/.local/bin:$PATH"
```

### 5.2 Python 虚拟环境

- **位置**：`~/.deepagent/.venv/`
- **创建工具**：`uv venv`
- **Python 版本**：3.11+（推荐 3.12）
- **依赖安装**：`uv sync --no-dev`（从 uv.lock 安装，不包含开发依赖）
- **入口点注册**：由 `pyproject.toml` 的 `[project.scripts]` 自动注册

### 5.3 配置保留策略

**更新安装时，以下文件永不被覆盖：**

| 文件 | 位置 | 保留原因 |
|------|------|----------|
| `.env` | `~/.deepagent/.env` | 用户 API 密钥和配置 |
| `config.yaml` | `~/.deepagent/config.yaml` | 用户 YAML 配置 |
| `skills/` 下的用户自定义 Skills | `~/.deepagent/skills/` | 用户创建的 Skills |

**更新安装流程：**

```
1. 检测 ~/.deepagent/ 是否已存在
2. 如果已存在（更新安装）：
   a. 创建 ~/.deepagent/.backup/deepagent-{OLD_VERSION}/
   b. 将当前 deepagent/ 目录移动到备份目录
   c. 解压新版本到 ~/.deepagent/deepagent/
   d. **不覆盖** .env、config.yaml、skills/ 下的用户文件
   e. 如果 .env 不存在，从 .env.example 复制模板
   f. 运行 uv sync --no-dev 更新依赖
   g. 更新 VERSION 文件
3. 如果不存在（全新安装）：
   a. 创建 ~/.deepagent/ 目录
   b. 解压 tarball 到 ~/.deepagent/deepagent/
   c. 从 .env.example 复制为 .env
   d. 运行 uv venv + uv sync --no-dev
   e. 创建 VERSION 文件
   f. 创建 ~/.local/bin/deepagent 符号链接
   g. 配置 PATH
```

### 5.4 备份策略

- **备份位置**：`~/.deepagent/.backup/deepagent-{VERSION}/`
- **保留数量**：最近 3 个备份
- **清理逻辑**：超过 3 个时删除最旧的

### 5.5 Desktop 与 CLI 共享后端

Electron 桌面端和 CLI **共用同一个 `~/.deepagent/` 后端**，不搞两套二进制。

- CLI 通过 `~/.local/bin/deepagent` → `~/.deepagent/.venv/bin/deepagent` 运行
- Desktop（Electron）通过 `deepagent webui start` 启动后端，然后加载 `http://127.0.0.1:8648`
- 两者共享同一套配置、skills、日志

---

## 6. 各模块的接口签名

### 6.1 install.sh → CLI 接口

**安装脚本路径**：`scripts/install-release.sh`（或 `scripts/install.sh`，两者功能对标）

**参数定义：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--skip-setup` | flag | false | 跳过交互式配置向导 |
| `--version VERSION` | string | `latest` | 指定安装版本 |
| `--dir PATH` | path | `~/.deepagent` | 指定安装目录 |
| `--no-dmg` | flag | false | 跳过 macOS DMG 自动下载 |
| `--no-path` | flag | false | 跳过 PATH 配置写入 |
| `--tarball FILE` | path | (空) | 使用本地 tarball 文件（离线安装） |
| `--help` | flag | — | 显示帮助信息 |

**安装后产物：**

| 产物 | 路径 | 说明 |
|------|------|------|
| 代码目录 | `$DEEPAGENT_HOME/deepagent/` | 从 tarball 解压的源码 |
| Python venv | `$DEEPAGENT_HOME/.venv/` | uv 创建的虚拟环境 |
| CLI 入口 | `$HOME/.local/bin/deepagent` | 符号链接 → venv/bin/deepagent |
| VERSION 文件 | `$DEEPAGENT_HOME/VERSION` | 当前安装版本号 |
| .env 文件 | `$DEEPAGENT_HOME/.env` | 用户配置（新建时从 .env.example 复制） |

### 6.2 install.sh → Electron 接口

Electron 主进程（`webui/electron/main.js`）通过静默安装调用 install.sh：

```javascript
// Electron 静默安装命令
const installCmd = `curl -fsSL https://deepseekagent.starseas.org/install.sh | sh -s -- --skip-setup --no-dmg --no-path`;
```

**参数说明（Electron 调用时的固定参数）：**
- `--skip-setup`：静默安装，不弹出交互式配置
- `--no-dmg`：不自动下载 DMG（Electron 自己处理桌面端）
- `--no-path`：不修改 shell profile（Electron 直接调用 venv 中的 deepagent）

**Electron 后端检测逻辑：**
1. 检查 `~/.deepagent/VERSION` 文件是否存在
2. 检查 `~/.deepagent/.venv/bin/deepagent` 是否存在且可执行
3. **两者同时满足**才认为后端已安装
4. 如果未安装，执行静默安装命令
5. 安装失败时显示错误对话框

### 6.3 CLI → update/rollback 接口

**命令定义：**

```bash
# 检查更新
deepagent update --check

# 执行更新
deepagent update [--version VERSION]

# 回滚到上一版本
deepagent update --rollback
```

**update 命令流程：**

```
1. get_current_version() → 从 VERSION 文件读取
2. get_latest_version() → 从 GitHub API 查询最新版本
3. 比较版本号，如果无更新则退出
4. download_with_fallback() → 双源下载新版本 tarball
5. create_backup() → 备份当前版本到 .backup/
6. perform_update():
   a. 校验 SHA256
   b. 解压到临时目录
   c. 保留 .env / config.yaml / 用户 skills
   d. 覆盖 deepagent/ 目录
   e. 运行 uv sync --no-dev
   f. 更新 VERSION 文件
7. 验证：deepagent --version 输出新版本号
```

**rollback 命令流程：**

```
1. 读取 .backup/ 目录，找到最新备份
2. 如果无备份，报错退出
3. 备份当前版本到 .backup/（回滚也是一次"更新"）
4. 从 .backup/deepagent-{OLD_VERSION}/ 恢复
5. 运行 uv sync --no-dev
6. 更新 VERSION 文件
7. 验证：deepagent --version 输出回滚后的版本号
```

### 6.4 build-release.sh → CI/CD 接口

**构建脚本路径**：`scripts/build-release.sh`

**参数：**

| 参数 | 说明 |
|------|------|
| `--version VERSION` | 指定版本号（默认从 VERSION 文件读取） |
| `--help` | 显示帮助 |

**环境变量：**

| 变量 | 说明 |
|------|------|
| `SKIP_WEBUI_CHECK=1` | 跳过 WebUI 预构建检查 |
| `SKIP_OPENCODE_CHECK=1` | 跳过 OpenCode 二进制检查 |
| `SKIP_SKILLS_MANIFEST=1` | 跳过 Skills manifest 构建 |

**产物：**

| 产物 | 路径 |
|------|------|
| Tarball | `dist/releases/deepagent-{VERSION}.tar.gz` |
| SHA256 | `dist/releases/deepagent-{VERSION}.sha256` |

### 6.5 install-verify.sh 接口

**验证脚本路径**：`scripts/install-verify.sh`

**参数：**

| 参数 | 说明 |
|------|------|
| `--test-dir DIR` | 使用自定义测试目录 |
| `--skip-install` | 跳过 Phase 3（实际安装测试） |
| `--tarball FILE` | 指定 tarball 文件 |
| `--version VER` | 检查指定版本 |

**退出码：**

| 退出码 | 含义 |
|--------|------|
| 0 | 所有检查通过 |
| 1 | 有检查失败 |
| 2 | 环境跳过（缺少前置条件） |

### 6.6 Pages Function 接口

**Pages Function 路径**：`website/functions/install.sh.js`

**输入：**
- HTTP GET `/install.sh?version=0.9.0-alpha.1`
- `version` 参数可选，默认查询 GitHub API 获取最新版本

**输出：**
- HTTP 302 重定向到 R2 上的安装脚本
- `Location: https://releases.deepseekagent.starseas.org/v{VERSION}/install.sh`

**GitHub API 缓存：**
- 缓存时间：5 分钟
- 缓存位置：Pages Function 内存（KV 可选）
- 降级逻辑：API 不可用时使用默认版本 `0.9.0-alpha.1`

### 6.7 Docker 接口

**Dockerfile 接口：**

| 项目 | 值 |
|------|-----|
| 基础镜像 | `python:3.12-slim` |
| EXPOSE | `8648` |
| ENTRYPOINT | `["deepagent"]` |
| HEALTHCHECK | `curl -f http://localhost:8648/ \|\| exit 1` |
| 构建方式 | 多阶段（build stage → runtime stage） |

**Docker 运行命令：**
```bash
docker build -t deepagent .
docker run -p 8648:8648 -v ~/.deepagent:/root/.deepagent deepagent
```

---

## 7. 集成清单（11 个任务产出核对）

当所有 11 个并行任务的产出合并到项目根目录后，按此清单逐项核对：

### 7.1 文件存在性检查

| # | 文件路径 | 来源任务 | 说明 |
|---|----------|----------|------|
| 1 | `scripts/release-install.sh` | 31.2 | 核心安装脚本（或 install-release.sh） |
| 2 | `docs/release/SPEC.md` | 31.2 | 本文件（共享契约） |
| 3 | `scripts/build-release.sh` | 31.3 | Release 包构建脚本 |
| 4 | `hermes_cli/release_update.py` | 31.4 | CLI 更新模块 |
| 5 | `hermes_cli/uninstall.py` | 31.4 | CLI 卸载模块 |
| 6 | `scripts/uninstall.sh` | 31.4 | Shell 卸载脚本 |
| 7 | `webui/electron/main.js` | 31.5 | Electron 主进程 |
| 8 | `webui/electron/electron-builder.config.js` | 31.5 | Electron 构建配置 |
| 9 | `website/functions/install.sh.js` | 31.6 | Pages Function |
| 10 | `website/static/_redirects` | 31.6 | Cloudflare 重定向规则 |
| 11 | `website/wrangler.toml` | 31.6 | Wrangler 配置 |
| 12 | `landingpage/index.html` | 31.6 | 品牌替换后的落地页 |
| 13 | `scripts/build-website.sh` | 31.6 | 网站构建脚本 |
| 14 | `CLOUDFLARE_DEPLOY.md` | 31.6 | Cloudflare 部署指南 |
| 15 | `.github/workflows/release.yml` | 31.7 | CI/CD 发布流水线 |
| 16 | `.github/workflows/desktop-release.yml` | 31.7 | DMG 构建流水线 |
| 17 | `scripts/install-verify.sh` | 31.8 | 验收脚本 |
| 18 | `tests/release-install/run-all.sh` | 31.8 | 测试运行器 |
| 19 | `embedded/start.sh` | 31.9 | Embedded team 入口 |
| 20 | `embedded/config/opencode-config.yaml` | 31.9 | OpenCode 隔离配置 |
| 21 | `scripts/setup-embedded-opencode.sh` | 31.9 | OpenCode 下载脚本 |
| 22 | `docs/release/RELEASE.md` | 31.10 | 发布操作手册 |
| 23 | `docs/release/PRIVACY.md` | 31.10 | 隐私说明 |
| 24 | `docs/release/CHANGELOG.md` | 31.10 | 变更日志 |
| 25 | `docs/release/homebrew-submission.md` | 31.10 | Homebrew 提交指南 |
| 26 | `scripts/homebrew/deepagent.rb` | 31.11 | Homebrew Formula |
| 27 | `Dockerfile` | 31.11 | Docker 镜像定义 |
| 28 | `scripts/docker/README.md` | 31.11 | Docker 使用说明 |
| 29 | `scripts/nsis/installer.nsi` | 31.11 | Windows NSIS 安装器 |

### 7.2 语法校验检查

| # | 校验命令 | 说明 |
|---|----------|------|
| 1 | `bash -n scripts/release-install.sh` | 安装脚本语法 |
| 2 | `bash -n scripts/build-release.sh` | 构建脚本语法 |
| 3 | `bash -n scripts/install-verify.sh` | 验收脚本语法 |
| 4 | `bash -n scripts/uninstall.sh` | 卸载脚本语法 |
| 5 | `node -c webui/electron/main.js` | Electron 主进程语法 |
| 6 | `node -c website/functions/install.sh.js` | Pages Function 语法 |
| 7 | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"` | YAML 语法 |
| 8 | `ruby -c scripts/homebrew/deepagent.rb` | Ruby 语法 |
| 9 | `python3 -c "import ast; ast.parse(open('hermes_cli/release_update.py').read())"` | Python 语法 |
| 10 | `python3 -c "import ast; ast.parse(open('hermes_cli/main.py').read())"` | CLI 入口语法 |

### 7.3 品牌一致性检查

| # | 校验命令 | 预期结果 |
|---|----------|----------|
| 1 | `grep -ci 'hermes\|nous' landingpage/index.html` | `0`（无品牌残留） |
| 2 | `grep -ci 'hermes\|nous' CLOUDFLARE_DEPLOY.md` | 仅验证命令中的引用 |
| 3 | `grep -r 'hermes-agent.nousresearch.com' .` | `0`（无旧域名引用） |
| 4 | `grep -r 'NousResearch/hermes-agent' .` | `0`（无旧仓库引用） |

### 7.4 功能完整性检查

| # | 检查项 | 验证方法 |
|---|--------|----------|
| 1 | install.sh 支持全部参数 | `bash scripts/release-install.sh --help` |
| 2 | build-release.sh 可产出 tarball | `SKIP_WEBUI_CHECK=1 bash scripts/build-release.sh --version 0.9.0-test` |
| 3 | tarball 不含 .git/.venv/node_modules | `tar tzf dist/releases/deepagent-*.tar.gz \| grep -E '\.git/\|\.venv/\|node_modules/'` |
| 4 | install-verify.sh 可运行 | `bash scripts/install-verify.sh --skip-install` |
| 5 | deepagent --version 可用 | `deepagent --version` |
| 6 | 双源下载逻辑存在 | `grep -c 'fallback\|backup\|starseas\|github' scripts/install-release.sh` |
| 7 | 配置保留逻辑存在 | `grep -c '.env\|config.yaml\|preserve\|backup' scripts/install-release.sh` |
| 8 | Docker 有 EXPOSE 8648 | `grep 'EXPOSE 8648' Dockerfile` |
| 9 | Docker 有 HEALTHCHECK | `grep 'HEALTHCHECK' Dockerfile` |
| 10 | release.yml 有 smoke test | `grep 'smoke\|deepagent --version' .github/workflows/release.yml` |

### 7.5 13 项验收标准映射

| # | 验收标准 | 负责任务 | install-verify.sh 检查函数 |
|---|----------|----------|---------------------------|
| 1 | curl\|sh 一条命令安装 | 31.2 | `check_criterion_1` |
| 2 | deepagent --version 可用 | 31.2 | `check_criterion_2` |
| 3 | 不依赖源码目录 | 31.2 | `check_criterion_3` |
| 4 | .env 不被覆盖 | 31.2 | `check_criterion_4` |
| 5 | config.yaml 不被覆盖 | 31.2 | `check_criterion_5` |
| 6 | 用户 skills 不被覆盖 | 31.2 | `check_criterion_6` |
| 7 | 系统 skills 正确同步 | 31.2 | `check_criterion_7` |
| 8 | WebUI 可启动 | 31.5 | `check_criterion_8` |
| 9 | OpenCode 可调用 | 31.9 | `check_criterion_9` |
| 10 | 双源下载降级 | 31.2 | `check_criterion_10` |
| 11 | deepagent update | 31.4 | `check_criterion_11` |
| 12 | deepagent update --rollback | 31.4 | `check_criterion_12` |
| 13 | Desktop+CLI 共用后端 | 31.5 | `check_criterion_13` |

---

## 附录 A：pyproject.toml 关键配置

```toml
[project]
name = "deepagent"
version = "0.9.0"
description = "The self-improving AI agent"
requires-python = ">=3.11"
license = { text = "MIT" }

[project.scripts]
deepagent = "hermes_cli.main:main"
deepagent-agent = "run_agent:main"
deepagent-acp = "acp_adapter.entry:main"
```

## 附录 B：端口与服务

| 服务 | 端口 | 说明 |
|------|------|------|
| WebUI | 8648 | 默认 WebUI 端口 |
| OpenCode | — | 通过 embedded/start.sh 启动，无固定端口 |

## 附录 C：变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2025-07-17 | 0.9.0-alpha.1 | 初始版本，从零编写 |
