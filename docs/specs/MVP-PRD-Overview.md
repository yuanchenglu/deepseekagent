# Deep Agent MVP PRD - 总览（Overview）

**版本**：v0.2  
**日期**：2026-07-01  
**状态**：文档基本完成，进入开发阶段  
**作者**：小路 + DeepAgent 数字分身

---

## 1. 产品最高愿景

Deep Agent 是一款**从 Harness 底层针对国产 DeepSeek 模型进行深度优化的产品**。

### 核心公式
> **Modern + Harness + Scene = Agent**

- Modern（基础模型）只决定**下限**
- Harness 层的深度优化决定**上限**

### 量化目标
- DeepSeek V4 Flash 的任务完成度 → 达到 GLM-5 水平（≈ Claude 4.6）
- DeepSeek V4 PRO 的任务完成度 → 达到 GLM-5.1 水平（≈ Claude 4.7）

**成功标准**：通过真实场景任务（尤其是硬任务）的完成度与达标率来验证，而非仅靠 benchmark 分数。

---

## 2. MVP 核心理念

Deep Agent 是用户的**数字分身（CEO）**。

- **研发类任务**：由 Deep Agent 作为 CEO，指挥其内置的 OpenCode 研发小组完成。
- **非研发类任务**：由 Deep Agent 自身直接处理。
- OpenCode 不是被指挥的对象，而是被**深度配置好的工具**（已配好 OpenSpec、Superpowers、MCP、Skills 等）。

**关键约束**：用户在使用 Deep Agent 时，**不需要感知到 OpenCode 的存在**，也不应被用户本地已安装的 OpenCode 配置所干扰。

---

## 3. 当前核心问题（MVP 必须解决）

按优先级排序：

### 3.1 上游同步与品牌统一（已启动）
- 已完成 PRD 子文档
- 开发中：品牌替换脚本（scripts/brand-replace.py）

### 3.2 桌面客户端
- 已完成 PRD 子文档（02-Desktop-Client.md）
- 基础资产：联想笔记本上的 deepagent-web-ui（已同步访问）

### 3.3 Code 模式实现（核心）
- 已完成 PRD 子文档（03-Code-Mode-Implementation.md）
- 已落地：
  - `embedded/` 目录结构 + 启动脚本
  - `deepagent_code_mode/` 模块骨架（dispatcher + session）

### 3.4 稳定性与工程质量
- 已完成 PRD 子文档（04-Engineering-and-Harness.md）

---

## 4. MVP 五大方向与文档导航（已全部完成）

| 方向               | 文档                                      | 状态     | 开发进度          |
|--------------------|-------------------------------------------|----------|-------------------|
| 上游同步 + 品牌统一 | [01-Upstream-Sync-and-Branding.md](./01-Upstream-Sync-and-Branding.md) | 已完成 | 脚本已创建，dry-run 完成 |
| 桌面客户端         | [02-Desktop-Client.md](./02-Desktop-Client.md) | 已完成 | 待启动改造       |
| Code 模式实现      | [03-Code-Mode-Implementation.md](./03-Code-Mode-Implementation.md) | 已完成 | 结构 + 骨架代码已落地 |
| 工程质量与 Harness  | [04-Engineering-and-Harness.md](./04-Engineering-and-Harness.md) | 已完成 | 待系统落地       |
| **Release 安装系统** 🔥 | **[05-Release-Installation.md](./05-Release-Installation.md)** | **新增** | **待开发（Phase 1-7）** |

---

## 5. 阶段划分（当前状态）

- **阶段 0**：PRD 撰写 → **已基本完成**
- **阶段 1**：上游同步机制 + 品牌统一 → **开发启动中**
- **阶段 2**：桌面客户端原型
- **阶段 3**：Code 模式后端完整实现 + 内置工具集成 → **骨架已就位**
- **阶段 4**：稳定性收尾 + Harness 层深度优化启动

---

## 6. 立即开发优先级（按我的规划）

1. **品牌统一（高可见度）**：保守替换关键文件 + CLI 入口。
2. **Code Mode 骨架增强**：实现真实 dispatcher 与 embedded 启动对接。
3. **隔离配置**：完善 embedded/ 下的独立 config。
4. **入口统一**：强化 `deepagent` 命令 + 文档。
5. **桌面客户端对接准备**：与现有 WebUI 资产打通。

---

## 7. 成功标准（MVP）

- 用户能通过 `deepagent` 启动，具有明显 DeepAgent 品牌。
- 可以下达研发指令，系统自动使用内置研发小组执行。
- 不污染用户任何本地 OpenCode / DeepAgent 配置。
- 文档完整，易于继续迭代。

---

**当前状态（2026-07-01）**：文档已全部补齐，开发已启动多个高价值模块。接下来将持续推进实现。