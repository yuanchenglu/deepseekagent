<p align="center">
  <img src="assets/banner.png" alt="Deep Agent" width="100%">
</p>

# Deep Agent ☤

<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-deepagent.starseas.org-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://github.com/yuanchenglu/deepseekagent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
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

```bash
deepagent
```

更多命令：
- `deepagent model`
- `deepagent gateway`
- `deepagent setup`
- `deepagent webui start`   — 启动 WebUI 工作台 (http://localhost:8648)
- `deepagent webui status`  — 查看 WebUI 状态
- `deepagent webui stop`    — 停止 WebUI

> 💡 **WebUI** 是 DeepAgent 的默认 Web 工作台，提供聊天、模型管理、设置等功能。
> 安装时会自动构建。默认账号: `admin` / `123456`。
>
> ### 🖥️ 桌面应用（Electron）
>
> DeepAgent WebUI 可打包为独立的桌面应用（基于 Electron），无需通过浏览器访问。
>
> #### 启动（开发模式）
>
> ```bash
> cd webui
> npx electron electron/main.js
> ```
>
> #### 打包为安装包
>
> ```bash
> # 安装依赖后一键打包（当前平台）
> ./scripts/package-electron.sh
>
> # 或指定平台
> ./scripts/package-electron.sh --mac     # macOS DMG
> ./scripts/package-electron.sh --linux   # Linux AppImage/Deb
>
> # 也可通过 npm 脚本
> cd webui
> npm run electron:build          # 当前平台
> npm run electron:build:mac      # macOS 专用
> npm run electron:build:linux    # Linux 专用
> ```
>
> 打包产物输出至 `webui/dist/electron-output/`。
>
> #### 相关文件
>
> | 文件 | 说明 |
> |------|------|
> | `webui/electron/main.js` | Electron 主进程，创建窗口并加载 `dist/client/index.html` |
> | `webui/electron/preload.js` | 预加载脚本，通过 contextBridge 暴露桌面 API |
> | `webui/electron/electron-builder.config.js` | electron-builder 打包配置 |
> | `scripts/package-electron.sh` | 打包入口脚本 |
>
> > **注意**：此 Electron 打包方案是**轻量版**。如需要完整功能（内嵌 Python 运行时、自动更新、托盘图标等），请参考 `packages/desktop/`（通过 `npm run build:desktop` 构建）。

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

**当前目标**：尽快把 MVP 四个方向的可执行骨架跑通，让 Deep Agent 真正具备“CEO 指挥内置研发小组”的能力。