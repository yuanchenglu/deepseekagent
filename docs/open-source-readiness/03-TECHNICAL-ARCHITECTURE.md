# DeepSeekAgent 技术架构

## 1. 架构目标

技术架构必须同时满足：

- 本地优先和默认安全。
- CLI、Desktop、WebUI 共用一个 Runtime Contract。
- Agent 执行状态真实、可恢复、可审计。
- Harness 模块可独立开启、关闭、测试和观测。
- 高风险工具由确定性策略控制，而不是依赖模型自律。
- Release、安装和 Runtime 下载形成单一供应链契约。

## 2. 目标总体架构

```text
CLI / Desktop UI
        │
        ▼
Local API Gateway
  ├─ Auth & Session
  ├─ Workspace Policy
  ├─ Task API
  └─ Observability API
        │
        ▼
Agent Runtime
  ├─ Session Controller
  ├─ Context Engine
  ├─ Model Runtime
  ├─ Harness Pipeline
  ├─ Tool Executor
  └─ Artifact Manager
        │
        ├─────────────┐
        ▼             ▼
Sandbox Worker     Persistence
Code/Terminal      SQLite + Files
Browser/Tools      Audit + Logs
```

## 3. 组件职责

### 3.1 Local API Gateway

- 默认监听 `127.0.0.1`。
- 管理本地 Session、Task、配置和健康检查。
- Desktop 使用一次性 bootstrap handshake 获取本地会话。
- 不向 Renderer 暴露根 Token。
- Remote Mode 是独立、显式的高级功能。

### 3.2 Session Controller

负责：

- Session 生命周期。
- 消息持久化。
- 中断与恢复。
- 模型切换。
- 任务级配置快照。
- Session 所有权与 Workspace 绑定。

### 3.3 Context Engine

内部子模块：

- Stable Prefix Store。
- Constraint Registry。
- Task Anchor Builder。
- Message Budgeter。
- Compressor。
- Retrieval Index。
- Prompt Cache Diagnostics。

约束必须携带：`source`、`priority`、`scope`、`created_at`、`expires_at`。

### 3.4 Model Runtime

- Provider Adapter。
- Model Profile。
- Reasoning 参数映射。
- Context Limit 探测。
- Retry 与 Fallback。
- Usage/Cost 归一化。

Model Router 只负责质量与成本选择，不承担安全决策。

### 3.5 Harness Pipeline

建议拆为明确阶段：

```text
Pre-turn
  → Intent Classification
  → Constraint Resolution
  → Risk Assessment
  → Context Assembly
  → Model Selection

Execution
  → Model Call
  → Tool Proposal
  → Policy Gate
  → Tool Execution
  → Observation

Post-turn
  → Output Validation
  → Artifact Validation
  → Metrics
  → Persistence
```

每个阶段输出结构化诊断，禁止宽泛异常后静默关闭整套 Harness。

### 3.6 Tool Executor

每个 Tool 必须声明：

```yaml
name: write_file
risk: medium
permissions:
  - workspace.write
side_effects: filesystem
supports_dry_run: true
supports_rollback: true
concurrency_scope: path
```

执行前经过 Policy Gate：

- 身份与 Session 校验。
- Workspace 范围校验。
- 参数 Schema 校验。
- 风险分级。
- 并发冲突检查。
- 必要时用户确认。
- 必要时创建 Checkpoint。

### 3.7 Task Service

统一 Code Mode、后台任务和长任务。

状态机：

```text
queued
  → preparing
  → awaiting_approval
  → running
  → succeeded | failed | timed_out | cancelled
```

Task 表至少包含：

- task_id、session_id、workspace_id。
- state、progress、created/started/finished。
- worker_pid、exit_code、heartbeat。
- input、result、error。
- artifact manifest。
- permission snapshot。

### 3.8 Sandbox Worker

首个开源版本最低标准：

- 独立工作目录。
- 环境变量 allowlist。
- 默认无宿主 Home 目录访问。
- CPU、内存、进程数、文件数和超时限制。
- 网络默认关闭或按域名 allowlist。
- 只允许访问选定 Workspace。
- Worker 与主进程通过结构化 IPC 通信。

平台实现可分别使用：Linux bubblewrap/容器、macOS sandbox-exec 替代方案或受控子进程、Windows Job Object/AppContainer。无法提供强隔离的平台必须明确标记安全等级。

## 4. 数据架构

### 4.1 目录

统一为：

```text
~/.deepagent/
  config/
  credentials/
  sessions/
  tasks/
  artifacts/
  logs/
  runtime/
  skills/
  cache/
```

禁止 `.hermes` 与 `.deepagent` 双写。

### 4.2 SQLite

建议表：

- sessions
- messages
- tasks
- task_events
- artifacts
- model_usage
- tool_audit
- workspaces
- installed_skills
- schema_migrations

写入必须使用事务和迁移版本。

### 4.3 Secret

- macOS Keychain、Windows Credential Manager、Linux Secret Service。
- 无系统凭据服务时，使用用户口令加密的 Secret Store。
- 日志、Trajectory、Error 和 Artifact 中执行统一 Secret Redaction。

## 5. Desktop 架构

### 5.1 Main Process

- 启动和监管 Local API。
- 管理更新、窗口和系统凭据。
- IPC 使用严格 allowlist 和调用方校验。
- `sandbox: true`，除非有经过审计的必要例外。

### 5.2 Preload

只暴露最小 API：

- 应用版本。
- 窗口控制。
- 一次性认证握手。
- 安全设置读取。

不得：

- 暴露根 Token。
- 修改网络响应。
- 自动使用固定密码。
- 提供任意命令执行接口。

### 5.3 Renderer

- CSP nonce/hash。
- 不存储长期凭据。
- 外部 URL 全部交由系统浏览器。
- 所有 API 请求绑定当前本地 Session。

## 6. Release 架构

### 6.1 单一 Manifest

```json
{
  "schema": 1,
  "version": "0.9.0",
  "artifacts": [],
  "sbom": {},
  "provenance": {},
  "signature": {}
}
```

Artifact 字段：平台、架构、文件名、大小、SHA-256、下载 URL、最低系统版本、组件版本。

### 6.2 供应链

- 锁定依赖。
- GitHub Actions 使用 commit SHA 固定第三方 Action。
- 生成 SBOM。
- 生成 SLSA provenance。
- Cosign/Sigstore 或项目签名密钥签名。
- 安装器内置公钥，只信任签名 Manifest。

## 7. 可观测性

必须区分：

- 用户可见事件。
- Debug 日志。
- 安全审计。
- 模型 Usage。
- Task Event。

日志默认本地，不上传；提供数据清理和导出；所有 Secret 必须脱敏。

## 8. 错误处理原则

- 安全失败：Fail closed。
- 发布校验失败：Fail closed。
- 可选能力缺失：明确 Degraded，不伪装成功。
- Task 子进程失败：进入 `failed`，保留退出码和错误摘要。
- Harness 单模块失败：记录模块健康状态，按配置决定阻断或降级。

## 9. 建议模块拆分

将 `run_agent.py` 拆为：

- `runtime/session_controller.py`
- `runtime/model_runtime.py`
- `runtime/tool_executor.py`
- `runtime/harness_pipeline.py`
- `runtime/context_engine.py`
- `runtime/task_service.py`
- `runtime/persistence.py`
- `runtime/observability.py`

## 10. 架构验收标准

- CLI 与 Desktop 使用同一 Agent Runtime。
- 所有保护 API 无认证返回 `401`。
- Renderer 无法读取长期根凭据。
- Task 每次执行都有唯一终态。
- 安装器拒绝无签名或摘要错误产物。
- 高风险工具必须经过 Policy Gate。
- 默认无公网或局域网监听。
- 所有状态容器有容量和保留策略。
