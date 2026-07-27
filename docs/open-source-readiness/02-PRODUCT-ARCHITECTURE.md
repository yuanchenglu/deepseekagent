# DeepSeekAgent 产品架构

## 1. 产品定义

DeepSeekAgent 是一款面向个人开发者和小型团队的本地优先 Agent 产品，目标是通过针对 DeepSeek 模型特性的 Harness Engineering，把模型能力转化为可持续执行任务、使用工具、维护上下文并交付可验证结果的桌面与 CLI Agent。

核心公式：

> Model + Harness + Tools + Runtime + Safety = Usable Agent

产品不应被定义为“功能集合”，而应被定义为一套可信执行系统。

## 2. 开源版本目标用户

### 2.1 主要用户

- 希望在本地运行通用 Agent 的开发者。
- 希望使用 DeepSeek 模型进行代码、研究和日常任务的技术用户。
- 希望研究 Context Engineering、Harness Engineering 和 Agent Runtime 的开源贡献者。

### 2.2 非目标用户

首个开源版本不服务：

- 企业多租户 SaaS。
- 无人值守的高风险生产自动化。
- 需要合规认证的政企场景。
- 大规模多 Agent 调度平台。
- 移动端完整产品。

## 3. 核心用户任务

1. 配置模型供应商并启动 Agent。
2. 与 Agent 连续对话并保持任务上下文。
3. 允许 Agent 使用有限、可审计的工具完成任务。
4. 在代码模式中创建任务、查看状态、获得结果和产物。
5. 查看 Agent 使用了什么模型、工具、Token 和成本。
6. 安全安装、更新、回滚和卸载。
7. 通过文档和扩展接口参与二次开发。

## 4. 产品能力分层

### L0：发行与运行基础

- 安装、升级、回滚、卸载。
- 配置目录和版本管理。
- Release Manifest、签名、校验和、SBOM。
- CLI 与 Desktop 启动入口。

### L1：Agent 核心

- 会话创建和恢复。
- 模型调用与 Provider 适配。
- Tool Calling Loop。
- 错误分类、重试、Fallback。
- Token、缓存和成本观测。

### L2：Harness

- 稳定前缀管理。
- 工具 Schema 稳定。
- 模型路由。
- Reasoning 配置。
- 任务 Anchor 和上下文压缩。
- 用户约束的来源化管理。

### L3：执行能力

- 文件读取、搜索和受控写入。
- 终端执行。
- 浏览器和 Web 工具。
- Code Mode 任务系统。
- MCP/Skills 扩展。

### L4：安全与治理

- 本地优先网络边界。
- 认证与凭据存储。
- 工具权限与风险分级。
- 不可逆操作确认。
- Sandbox、资源配额和审计。
- Secret 防泄漏。

### L5：交互层

- CLI。
- Desktop Shell。
- WebUI。
- 状态、日志、任务和设置界面。

## 5. 产品形态决策

### 5.1 主形态

首个开源版本只保留两个主入口：

1. CLI：功能最完整、可调试、作为工程基线。
2. Desktop：本地壳层，调用同一 Runtime 和 API。

WebUI 是 Desktop 的界面实现，不作为默认远程服务产品。

### 5.2 暂缓形态

- 公网 Web 服务。
- 多用户管理后台。
- 移动端。
- 大规模 Gateway 平台。
- 宠物窗口等非核心视觉功能，可保留实验标记但不得影响主链路。

## 6. 核心产品对象

| 对象 | 定义 |
|---|---|
| Workspace | Agent 可访问的工作目录与权限边界 |
| Session | 一次连续对话与执行上下文 |
| Task | 有明确状态、输入、输出和生命周期的执行单元 |
| Tool | 具有 Schema、权限、风险级别和审计信息的能力 |
| Artifact | Agent 产生的文件、报告、补丁或结构化结果 |
| Model Profile | Provider、模型、Reasoning、上下文和成本配置 |
| Skill | 可安装、可审查、带来源信息的扩展能力 |
| Checkpoint | 高风险操作前的可恢复状态 |

## 7. 关键用户流程

### 7.1 首次启动

安装验证 → 创建本地配置 → 选择 Provider → 安全保存凭据 → 健康检查 → 创建首个 Session。

禁止默认账号和固定密码。

### 7.2 普通 Agent 任务

输入目标 → 解析任务与权限 → 构建上下文 → 选择模型 → 调用模型 → 工具执行 → 结果验证 → 交付输出 → 保存 Session。

### 7.3 Code Mode

创建任务 → 选择 Workspace → 生成执行计划 → 用户确认高风险权限 → 启动隔离 Worker → 持续更新状态 → 收集日志与产物 → 验证 → 完成或失败。

### 7.4 高风险操作

识别风险 → 生成影响预览 → 建立 Checkpoint → 显式确认 → 执行 → 验证结果 → 写入审计日志 → 支持回滚。

## 8. 产品边界

### 8.1 必须保证

- 默认本地安全。
- 每次高权限操作可解释、可确认、可审计。
- 任务状态真实反映执行状态。
- 失败不会伪装成成功。
- 安装包与源码来源可验证。
- 用户可删除全部本地数据。

### 8.2 不保证

- 模型输出绝对正确。
- 所有第三方 Tool 和 Skill 安全。
- 无 Sandbox 情况下任意代码绝对隔离。
- 所有 Provider 的接口行为完全一致。

## 9. 成功指标

首个开源版本使用工程指标而非增长指标：

- Clean-machine 安装成功率 ≥ 95%。
- 核心 E2E 测试通过率 100%。
- 默认配置下远程攻击面为 0。
- 认证绕过、固定凭据、明文 Secret 为 0。
- Code Mode 任务终态准确率 100%。
- Release 校验与签名覆盖率 100%。
- P0/P1 已知缺陷为 0。
- 文档覆盖核心用户流程和扩展接口。

## 10. 产品原则

1. Local-first，而不是先做远程平台。
2. Safe-by-default，而不是依靠用户正确配置。
3. Truthful state，而不是“看起来成功”。
4. One runtime contract，避免多套产品路径漂移。
5. Minimal open-source scope，减少非核心功能。
6. Model-aware but model-independent safety。
