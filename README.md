<p align="center">
  <img src="assets/banner.png" alt="Deep Agent" width="100%">
</p>

# DeepAgent ☤

<p align="center">
  <a href="https://deepseekagent.starseas.org/"><img src="https://img.shields.io/badge/Docs-deepseekagent.starseas.org-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="#许可证边界"><img src="https://img.shields.io/badge/License-MIT%20%2B%20BSL--1.1-blue?style=for-the-badge" alt="License: MIT and BSL-1.1"></a>
</p>

**Deep Agent 是基于 Hermes 深度改造的数字分身（CEO）产品**，核心目标是通过 **Harness 层** 让 DeepSeek 模型在真实场景下达到顶级水平。

> **Modern + Harness + Scene = Agent**
>
> - Modern 只决定下限
> - Harness 层的深度优化决定上限

## 核心定位

- **用户 = 董事长**
- **Deep Agent = CEO 数字分身**
- 研发任务 → 指挥**内置的、完全隔离的** OpenCode 研发小组执行
- 非研发任务 → Deep Agent 直接处理

用户不应该感知到底层用了 OpenCode，也不应该被自己本地的 OpenCode 配置干扰。

---

## 快速开始

CLI Alpha 首轮只承诺 **macOS Apple Silicon**。从官网安装：

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
deepagent setup
deepagent doctor
deepagent
```

第一阶段公开命令为 `--version`、`setup`、`doctor`、交互 CLI、`update` 和 `uninstall`。WebUI、旧 Electron 和 DeepCode 不包含在 CLI Alpha 安装包中。

```bash
deepagent update --check
deepagent update
deepagent uninstall --keep-data
```

安装默认使用 `~/.deepagent/`，唯一全局命令是 `~/.local/bin/deepagent`。安装、更新和卸载不读写 Hermes 或 OpenCode 的用户目录。

## 发布路线

| 阶段 | 产物 | 当前承诺 |
|---|---|---|
| 1 | 公开 CLI Alpha | macOS Apple Silicon，官网安装 |
| 2 | 浏览器 WebUI Beta | 路线图，尚未列入 Alpha 承诺 |
| 3 | DeepAgent / DeepCode 双模式 Electron | 路线图 |

详细执行文档见 `docs/open-source-readiness/`。

---

## MVP 四大方向（当前进展）

| 方向 | 文档 | 开发状态 |
|------|------|----------|
| 上游同步 + 品牌统一 | [01-Upstream...](docs/specs/01-Upstream-Sync-and-Branding.md) | 脚本已创建 |
| 桌面客户端 | [02-Desktop-Client.md](docs/specs/02-Desktop-Client.md) | PRD 完成 |
| **Code 模式（核心）** | [03-Code-Mode-Implementation.md](docs/specs/03-Code-Mode-Implementation.md) | **骨架已落地** |
| 工程质量 & Harness | [04-Engineering-and-Harness.md](docs/specs/04-Engineering-and-Harness.md) | PRD 完成 |

详见 `docs/specs/MVP-PRD-Overview.md` 和 `IMPLEMENTATION-STATUS.md`。

---

## 项目结构亮点（开发中）

- `webui/` — 默认 Web 工作台（基于 Hermes Web UI）
- `embedded/` — 内置、隔离的研发小组（OpenCode 等）
- `deepagent_code_mode/` — Code 模式核心（dispatcher + session）
- `scripts/brand-replace.py` — 品牌清理工具
- `scripts/setup-webui.sh` — WebUI 安装脚本
- `scripts/start-webui.sh` — WebUI 启动管理脚本
- 完整 PRD 体系在 `docs/specs/`

---

**当前目标**：先完成可公开、可安装、与 Hermes/OpenCode 隔离的 CLI Alpha，再按阶段开放 WebUI 与双模式桌面客户端。

---

---

## 开发说明

### 环境隔离（重要）

如果开发机器上同时安装了 **Hermes** 和 **DeepAgent**，测试 DeepAgent 前务必设置独立的工作目录：

```bash
export DEEPAGENT_HOME=~/.deepagent-test
deepagent  # 或: python -m hermes_cli.main gateway run
```

**原因：** 产品运行时已不再把用户环境中的 `HERMES_HOME` 当作 DeepAgent 根目录；但开发与正式产品仍应使用不同的 `DEEPAGENT_HOME`，避免测试数据污染正式 DeepAgent 会话和配置。

**持久化设置（开发期间）：**

```bash
echo 'export DEEPAGENT_HOME=$HOME/.deepagent-test' >> ~/.zshrc
source ~/.zshrc
```

## 许可证边界

本仓库是同仓混合许可，**不是整仓 MIT**：

| 范围 | 许可证 | 对外口径 |
|---|---|---|
| DeepAgent Core（除下列目录外的根项目代码） | [MIT](LICENSE) | 开源软件 |
| `webui/`（包含现有 WebUI 和 Desktop） | [BSL-1.1](webui/LICENSE) | 源码可见软件，不得称为 MIT 开源 |
| `embedded/opencode/` 及其内嵌组件 | 各自目录中的许可文件 | 第一阶段发布包不包含 |
| 第三方依赖 | 各自上游许可证 | 见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) |

贡献某个文件表示你同意按该文件所属目录的许可条款提供贡献。
