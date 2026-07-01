# 02 - 桌面客户端（Desktop Client）

**版本**：v0.1  
**日期**：2026-07-01  
**状态**：草案  
**关联 Overview**：MVP-PRD-Overview.md

---

## 1. 问题背景

当前 Deep Agent 主要以 TUI（终端用户界面）和 Gateway（消息平台）方式提供访问。

对于“数字分身 CEO”定位，纯 TUI 体验不足以支撑日常重度使用，尤其是 Code 模式下的研发指挥场景。

目标形态：**类似 Codex / Trae Work 的双模式桌面客户端**。

---

## 2. 目标

1. 提供现代化的桌面 / Web 客户端体验。
2. 支持 **Agent 模式**（自然对话）和 **Code 模式**（CEO 指挥研发小组）。
3. 基于现有资产快速落地（联想笔记本上的 DeepAgent WebUI 是强候选）。
4. 客户端与核心后端解耦，后端可独立演进。

---

## 3. 双模式设计

### 3.1 Agent 模式（默认）
- 聊天式界面（类似 ChatGPT / Cursor Chat）。
- 支持多会话、技能调用、记忆检索、子代理委托。
- 适合日常任务、规划、研究、非代码工作。

### 3.2 Code 模式（核心差异化）
- IDE-like 布局：
  - 左侧/上方：对话面板（CEO 下指令）
  - 右侧/下方：代码视图 + 文件树 + 终端输出
  - 集成 OpenCode（或类似）作为**内置研发小组**
- 用户指令直接翻译为对内置 OpenCode 的任务分发。
- **隔离**：内置 OpenCode 使用独立配置、独立模型、独立技能库。

---

## 4. 客户端选型与技术方案

### 4.1 强推荐方案（基于现有资产）
- **基础**：联想笔记本上的 `deepagent-web-ui`（已深度集成，已在 `~/.deepagent-web-ui` 运行）。
- 优势：
  - 已有 Vue + Naive UI 基础。
  - 已支持部分 DeepAgent 集成。
  - 可快速 fork 到 DeepAgent 仓库作为 `web/` 或 `desktop/` 模块。
- 改造方向：
  - 品牌替换为 DeepAgent。
  - 新增 Code 模式布局和与后端 Code Mode API 的对接。
  - 支持 Electron 打包成桌面应用（或先用 Web + Cloudflare 访问）。

### 4.2 备选方案
- Trae Work / Cursor 风格的开源框架。
- Tauri + Vue/React（轻量桌面）。
- 纯 Web + PWA（快速验证）。

**MVP 决策**：优先基于现有 DeepAgent WebUI 改造，1-2 周内出可点击原型。

---

## 5. 后端对接需求

客户端需要调用后端暴露的新接口：

- `/api/code-mode/start-task` （发起 Code 模式任务）
- `/api/code-mode/status`
- WebSocket 实时日志/文件变更推送
- 内置 OpenCode 的会话隔离 API

详见 `03-Code-Mode-Implementation.md`。

---

## 6. 阶段与交付

**MVP 阶段 2 目标**：
- [ ] 基于现有 WebUI 搭建双模式骨架
- [ ] Agent 模式基本可用（复用现有 Gateway 能力）
- [ ] Code 模式 UI 框架（对话 + 简单文件树）
- [ ] 支持通过 deepagent-tech.skysea.uk 访问

**后续**：
- Electron 桌面打包
- 本地热更新 + 离线能力
- 移动端适配（次要）

---

## 7. 验收标准

- 用户可通过浏览器或桌面应用进入 Deep Agent。
- 清晰切换 Agent / Code 模式。
- Code 模式下指令能被正确路由到内置研发工具链（初期可 mock）。
- 体验不劣于现有 TUI + WebUI 组合。

---

## 8. 后续行动

1. ~~在 `web/` 或 `desktop/` 下 fork 现有 DeepAgent WebUI 代码~~ ✅ 已完成
2. ~~完成品牌替换 + 双模式路由骨架~~ ✅ 已完成（最小品牌替换）
3. 定义前端与后端 Code Mode 的 API 契约
4. 部署到 deepagent-tech.skysea.uk 验证

**备注**：本子文档聚焦客户端形态与选型，具体实现细节放在后续实施计划中。

---

## 9. WebUI 集成状态（2026-07-01）

### 已完成
- [x] WebUI 源码克隆到 `webui/` 目录（来自 `https://github.com/EKKOLearnAI/hermes-web-ui.git`）
- [x] DEEPAGENT-README.md 说明文档
- [x] 最小品牌替换（页面标题、登录文案 → "Deep Agent"）
- [x] `scripts/setup-webui.sh` — 安装和构建脚本
- [x] `scripts/start-webui.sh` — 启动/停止/状态管理脚本
- [x] `setup-deepagent.sh` 集成（安装流程自动调用）
- [x] `deepagent webui` 子命令（start/stop/status/restart）
- [x] 数据目录: `~/.deepagent-webui/`（独立于 `~/.hermes-web-ui/`）
- [x] 默认端口: 8648

### 配置说明

```yaml
# ~/.deepagent-webui/config.yaml
port: 8648
webui_dir: ./webui
agent_bridge:
  enabled: true
  socket_path: /tmp/deepagent-ipc.sock
  auto_connect: true
```

### 用户使用流程

```bash
# 安装时自动完成
./setup-deepagent.sh

# 手动管理
deepagent webui start    # 启动 WebUI (port 8648)
deepagent webui status   # 查看运行状态
deepagent webui stop     # 停止 WebUI
deepagent webui restart  # 重启 WebUI

# 浏览器访问
# http://localhost:8648
# 默认账号: admin / 123456
```