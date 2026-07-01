# PRD: DeepAgent Release 级别安装系统（v1.1 整合版）

- **状态**: 已确认，待实施
- **版本**: 1.1（合并补充需求 + OpenCode 审查修正）
- **日期**: 2026-07-01

---

## 1. 背景与目标

（同 v1.0，未改动）
- 当前安装依赖源码目录，不是 Release 级别
- **一条命令安装**：`curl -fsSL https://deepseekagent.starseas.org/install.sh | sh`
- **装完即用**，不依赖源码目录
- **双源下载**：Cloudflare R2 主源 + GitHub Releases 备用源（国内友好）
- **配置保护**：用户 .env、config、skills 永不被覆盖
- **内置研发小组**（OpenCode）
- **可更新**：`deepagent update`

---

## 2. 架构设计

### 2.1 安装架构（OpenCode 审查修正）

```
用户安装流程
curl -fsSL https://deepseekagent.starseas.org/install.sh | sh
                         │
                         ▼
                  ┌──────────────┐
                  │  install.sh  │
                  └──────┬───────┘
                         │ ① 检测系统依赖（uv / Python）
                         │ ② 从主源下载 release tarball
                         │ ③ 解压到 ~/.deepagent/
                         │ ④ uv sync 装 Python 依赖（WebUI 已预构建，无需 npm build）
                         │ ⑤ 同步系统 skills → 用户目录
                         │ ⑥ 创建 ~/.local/bin/deepagent 符号链接
                         │ ⑦ 保留已有 .env/config.yaml
                         ▼
                  ┌──────────────┐
                  │  DeepAgent   │  ← 安装完成，立即可用
                  │  已就绪       │
                  └──────────────┘
```

> 🔴 **v1.0 修正**：install.sh **不执行 electron-builder**（耗时 5-15 分钟，无 GUI 环境会失败）。
> Desktop 客户端（DMG）在 CI 中预构建，作为独立下载提供。
> WebUI 以预构建 dist/ 形式包含在 release 包中，安装时不需要 npm install/npm run build。

### 2.2 双源下载与版本一致策略

```
1. 主源：Cloudflare R2 → https://deepseekagent.starseas.org/releases/deepagent-<version>.tar.gz
2. 备用：GitHub Releases → https://github.com/yuanchenglu/DeepAgent/releases/download/v<version>/...
3. 信任链加固：tarball 从 R2 下载，sha256 checksum 从 GitHub Releases 获取（不同信任域）
4. 发布顺序：先上传 GitHub Releases → 确认成功后 → 再上传 R2（避免版本不一致竞态）
```

### 2.3 Desktop 客户端与 CLI 共用后端架构

- **硬约束**：CLI 安装（`curl | sh`）和 Desktop DMG 安装**共用同一套后端**
- **不得在电脑上搞出两套 Deep Agent**。参考 OpenCode 的历史教训
- **实现方式**：
  - CLI 安装：install.sh → 下载 tarball → `~/.deepagent/`（唯一后端）
  - DMG 安装：首次启动时内部静默执行 install.sh（用户无感知），本质是同一套流程
  - Desktop 应用是 Electron 壳，`~/.deepagent/` 是唯一后端
  - 共用：同一份 .env、config.yaml、skills/、sessions.db、gateway 服务
- OpenCode 在计划中细化方案，但"共用后端"是不可妥协的硬约束

---

## 3. 域名路由与首页落地页

### 3.1 当前状态

| 路径 | 应指向 | 状态 |
|------|--------|------|
| `deepseekagent.starseas.org/` | 产品落地页 | ❌ 无法访问（bug，优先修） |
| `deepseekagent.starseas.org/docs` | Docusaurus 文档站 | 应与 `deepagent-docs.pages.dev` 一致 |
| `deepseekagent.starseas.org/install.sh` | 安装脚本（R2） | ❌ 未部署 |

### 3.2 推荐架构（Pages + R2 混合）

```
Pages（deepseekagent.starseas.org）
├── /              → Landing Page（静态 HTML）
├── /docs/*        → Docusaurus 构建产物
├── /install.sh    → Pages Function → R2 redirect
└── /download      → Desktop DMG 下载页

R2（releases bucket）
├── deepagent-<version>.tar.gz
└── DeepAgent-<version>-arm64.dmg
```

### 3.3 域名配置风险策略

> ⚠️ 已知风险：另一个 Agent 花 20+ 分钟未处理好该域名配置。

执行策略：先通过 Pages 临时域名 `*.pages.dev` 完成全量验证 → 所有功能确认无误后再绑定自定义域名。
备选回退：Plan B = GitHub Pages + Cloudflare Worker 代理，Plan C = 纯 R2 静态站点。

### 3.4 首页落地页 v1 设计

**核心功能**：
- 一键命令安装：展示 `curl -fsSL ... | sh` 代码块，一键复制
- Desktop DMG 下载：条件允许时提供 Mac DMG 下载链接

**业务介绍**：
- 为 DeepSeek 深度定制的 AI Native Agent 产品
- 基于模型物理特性定制，包含内置虚拟软件研发团队（OpenCode）
- 基于 Hermes 和 OpenCode 的二次开发（如实说明）

**页面风格**：
- 对标 DeepSeek 官方聊天页面风格，简洁干净科技感
- 深色主题

---

## 4. Release 包结构

（同 v1.0，修正：WebUI 预构建 dist/ 包含在包中，electron/ 目录保留但 electron-builder 不在 install.sh 中执行）

```
deepagent-<version>.tar.gz
├── deepagent/         # Python 包（含 embedded/opencode/ 预编译二进制、skills/、tools/）
├── webui/
│   ├── dist/          # 预构建产物（即开即用，无需 npm build）
│   ├── src/           # 源码
│   └── electron/      # Desktop 封装源码（打包在 CI 中完成）
└── VERSION
```

安装后目录结构 `~/.deepagent/`：

```
~/.deepagent/
├── deepagent/         # Python 包 + venv（uv sync 生成）
├── webui/             # 预构建 WebUI
├── skills/            # 系统 + 用户 skills
│   ├── .bundled_manifest
│   └── .hub/
├── .env               # 已有则保留
├── config.yaml        # 已有则保留
├── VERSION
├── sessions.db
└── logs/
```

### skills_sync 用户修改判定

复用 Hermes 现有 `tools/skills_sync.py` 机制：基于 MD5 目录哈希的 manifest，用户改过的 skill → 不覆盖。详见源码。

---

## 5. install.sh 详细流程

### 命令行参数

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | sh
curl -fsSL ... | sh -s -- --skip-setup     # 跳过交互式配置
curl -fsSL ... | sh -s -- --version v0.9.0 # 指定版本
curl -fsSL ... | sh -s -- --dir /opt/deepagent  # 指定安装目录
```

### 流程步骤（修正后）

```
Step 1: 系统检测
  ├─ 检测 OS（macOS / Linux / Termux）
  ├─ 检测 uv（没有则安装）
  ├─ 检测 Python 3.11+（没有则 uv python install 3.11）
  └─ 检测 Node.js 23+ → ❌ 不再自动安装，仅警告（WebUI 已预构建，Node.js 仅开发需要）

Step 2: 下载 Release 包
  ├─ 从主源下载（R2）→ 失败则切备用源（GitHub Releases）
  ├─ 验证 sha256 校验和（checksum 从 GitHub 获取，不同信任域）
  └─ 解压到临时目录

Step 3: 安装（修正版）
  ├─ 判断全新安装 vs 更新安装
  ├─ 复制文件到 ~/.deepagent/
  ├─ uv sync（安装/更新 Python 依赖）
  ├─ ✅ 不再执行 electron-builder（改为 CI 预构建 DMG）
  ├─ ✅ 不再执行 npm build（WebUI 已预构建）
  ├─ deepagent gateway 注册为开机启动服务
  └─ 创建 ~/.local/bin/deepagent symlink

Step 4: Skill 同步（同 v1.0）

Step 5: 配置保留（同 v1.0）

Step 6: PATH 配置（同 v1.0）

Step 7: 🔥 Desktop DMG 自动弹出（install.sh 的最后一步）
  ├─ 下载 DeepAgent DMG 到 ~/Downloads/
  │   （如果下载失败或用户无网络，跳过，不影响安装结果）
  ├─ hdiutil attach 挂载 DMG
  ├─ open Finder 窗口："把 DeepAgent.app 拖到 Applications"
  └─ 🔔 用户可关掉 Finder（跳过 Desktop 安装），不影响 CLI 使用

Step 8: 完成提示
  ├─ "✅ DeepAgent 已安装！直接输入 deepagent 使用"
  ├─ "🖥️ DMG 已挂载，拖动 DeepAgent.app 到 Applications 即可安装桌面版"
  └─ "（关掉即可，不影响终端使用）"
```

### 配置保留策略

| 文件 | 全新安装 | 更新安装 |
|------|---------|---------|
| .env | 从模板创建 | ✅ 保留 |
| config.yaml | 从模板创建 | ✅ 保留 |
| 用户 skills | — | ✅ 永不被覆盖 |
| sessions.db | 新建 | ✅ 保留 |
| VERSION | 写入 | 更新 |

---

## 6. OpenCode 集成

（同 v1.0，补充平台覆盖范围）
- Release 包包含 OpenCode **macOS ARM64 + macOS x64 预编译二进制**
- Linux 支持在后续版本添加
- 隔离配置在 `embedded/config/opencode-config.yaml`

---

## 7. 更新与回滚

### deepagent update

```bash
deepagent update            # 更新到最新版本
deepagent update --version v0.10.0  # 指定版本
deepagent update --check    # 查看可更新版本
deepagent update --rollback # 回滚到上一个版本
```

更新流程：下载新 Release 包 → 备份旧版本到 `~/.deepagent/.backup/` → 覆盖 deepagent/ → uv sync → 更新 VERSION。

### 回滚范围

回滚备份涵盖：`deepagent/`、`webui/`、`VERSION`、`sessions.db`、`skills/.bundled_manifest`。
不覆盖：`.env`、`config.yaml`、用户自定义 skills。

---

## 8. 实施任务清单（7 Phase）

### Phase 1: install.sh
- 编写 install.sh（系统检测、双源下载、sha256 校验、uv sync、技能同步、配置保留）
- **注意**：不包含 electron-builder 或 npm build

### Phase 2: Release 包构建脚本（build-release.sh）
- 打包 deepagent/ + webui/dist/（预构建）+ embedded/opencode/ + skills/

### Phase 3: OpenCode 集成
- 预编译 opencode 二进制（macOS ARM64 + x64）→ embedded/opencode/
- 隔离配置 + 运行测试

### Phase 4: Desktop 客户端
- CI 中预构建 DMG（electron-builder），不作为 install.sh 的一步
- DeepSeek 金鱼 Logo（512×512 最大）
- macOS：DMG 首次启动检测后端是否已安装，未安装则静默执行 install.sh

### Phase 5: deepagent update 命令
- CLI 命令 + 版本查询 + 自动下载 + 回滚

### Phase 6: 发布部署
- 先上传 GitHub Releases → 确认后上传 R2
- 域名路由配置（Pages + R2 混合）
- install.sh 托管到 R2

### Phase 7: 验证
- 验收脚本 install-verify.sh（Release 包结构验证 → 模拟安装 → 实际安装）
- 测试环境：本机 + CI runner + 虚拟机 + 干净 VM + 国内环境
- 覆盖：全新安装、更新安装、回滚、配置保留、双源降级、Desktop 共享后端

---

## 9. 验收标准（13 项）

| # | 验收点 | 验证方式 |
|---|--------|---------|
| 1 | 一条命令装好 | 实际执行 |
| 2 | 装完后 deepagent 命令可用 | 命令行 |
| 3 | 装完后可删除源码目录，deepagent 仍可用 | 删除后执行 |
| 4 | 已有 .env 不被覆盖 | 安装前后对比 |
| 5 | 已有 config.yaml 不被覆盖 | 安装前后对比 |
| 6 | 用户自定义 skills 不被覆盖 | skills_sync 验证 |
| 7 | 系统 skills 正确同步 | skills_sync 验证 |
| 8 | WebUI 可正常启动 | 浏览器打开 |
| 9 | OpenCode 可正常调用 | embedded/start.sh 执行 |
| 10 | 双源下载：主源故障时备用源正常工作 | 网络断连测试 |
| 11 | deepagent update 可正常更新 | 版本升级验证 |
| 12 | 国内用户可正常下载安装 | 中国 CDN 验证 |
| 13 | Desktop DMG 和 CLI 共用同一后端 | 安装后检查配置目录 |

---

## 10. 附录

### A. 凭证位置

Cloudflare 部署凭证（Pages / R2 / DNS 配置所需）已存入 `~/.deepagent/.env`。
环境变量名：`CF_ACCOUNT_ID`、`CF_API_TOKEN`、`CF_GLOBAL_API_KEY`、`CF_ZONE_ID_SKYSEA`、`CF_ZONE_ID_CLAWADMIN`、`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`、`R2_TOKEN_VALUE`、`R2_ENDPOINT`。

### B. 参考实现
- Hermes install.sh（参考系统检测、配置保留策略）
- Hermes tools/skills_sync.py（复用 manifest 哈希同步机制）
- OpenCode CLI（github.com/anomalyco/opencode）

### C. 开发模式关系

```
主机（master 分支，Release 安装）
  └── deepagent（已安装的软件，~/.deepagent/，不含 .git）
  └── deepagent update 更新

虚拟机 / AIPC（develop 分支，源码开发）
  └── git clone → develop 分支 → 修改代码 → push
  └── 合并到 master → 构建 Release → 主机 deepagent update
```
