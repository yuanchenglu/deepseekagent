# DeepSeekAgent 开源版 PRD

## 1. 文档信息

- 产品：DeepSeekAgent
- 版本目标：首个可公开开源版本
- 工作分支：`develop`
- 发布原则：少加功能，优先安全、可安装、可执行、可验证、可维护

## 2. 背景与问题

现有项目已经具备 Agent Runtime、工具系统、WebUI、Electron、Harness、Code Mode、Gateway、Skills 和发布脚本，但存在三类根本问题：

1. 产品主路径不清晰，多套入口和品牌并存。
2. 核心执行闭环不完整，部分状态和测试只能证明“已派发”或“不崩溃”。
3. 安全与发布默认值不足以支撑公开开源。

本 PRD 的目标不是扩张功能，而是将现有能力收敛为一个可信的最小完整产品。

## 3. 产品目标

### 3.1 用户价值

用户可以在自己的电脑上安全安装 DeepSeekAgent，配置模型，创建会话，让 Agent 使用受控工具完成任务，并在 Code Mode 中获得真实、可追踪的执行结果。

### 3.2 版本目标

- CLI 主链路稳定。
- Desktop 使用同一 Runtime。
- 默认仅本机访问。
- Agent Loop、Tool Loop、Session、Task、Artifact 闭环完整。
- Code Mode 有真实状态机。
- Release 可验证、可升级、可回滚。
- 文档、许可证和贡献流程完整。

### 3.3 非目标

- 公网 SaaS。
- 企业多租户。
- 移动端。
- 大规模 Multi-Agent 平台。
- 复杂社交、宠物窗口和非核心视觉玩法。
- 无人确认的高风险生产自动化。

## 4. 用户与场景

### Persona A：开发者用户

需要本地 Agent 完成代码阅读、修改、测试和文档任务，关注可控性、日志、成本和可恢复性。

### Persona B：Agent 研究者

需要观察 Context、Harness、Model Routing 和 Tool Execution 行为，关注诊断和扩展接口。

### Persona C：开源贡献者

需要清晰架构、开发环境、测试门禁、Issue 模板和模块边界。

## 5. 产品范围

### P0 必须交付

1. CLI 安装与启动。
2. Desktop 启动与本地服务管理。
3. Provider 配置和安全凭据存储。
4. Session 创建、恢复、删除和导出。
5. Agent 基础对话和工具调用。
6. Workspace 权限边界。
7. Code Mode Task 状态机。
8. 高风险操作确认。
9. Release Manifest、签名和校验。
10. 完整测试和开源文档。

### P1 可以保留但不得阻断

- Browser Tools。
- MCP。
- Skills 安装。
- Gateway 平台连接。
- 多 Provider Fallback。

### 暂缓

- Remote WebUI。
- 多用户 Web 管理。
- Desktop Pet。
- 自动生成长期免疫 Skill。
- 复杂 Multi-Agent 编排。

## 6. 功能需求

## FR-01 安装、升级与卸载

### 需求

- 支持 macOS、Linux；Windows 可通过 WSL 或独立 Desktop 包声明支持级别。
- 安装器从签名 Manifest 获取产物。
- 强制验证签名、SHA-256、平台与架构。
- 安装失败不得留下“半成功”状态。
- 升级前备份配置和数据库。
- 支持回滚到上一可用版本。
- 支持完整卸载和保留用户数据两种模式。

### 验收

- 干净机器安装后可执行 `deepagent doctor` 和首轮对话。
- 摘要错误、签名错误或下载中断时安装失败。
- 升级失败后旧版本仍可启动。

## FR-02 首次启动与配置

### 需求

- 不存在默认账号和默认密码。
- 用户选择 Provider、模型和凭据。
- 凭据写入系统安全存储。
- 提供连接测试。
- 提供 Local-only 默认模式。
- 配置文件记录非 Secret 设置，Secret 不进入普通 YAML/JSON。

### 验收

- 日志、数据库、前端存储中没有明文 API Key。
- Provider 测试失败时给出明确原因。

## FR-03 Session 管理

### 需求

- 创建、重命名、恢复、归档、删除 Session。
- Session 绑定 Workspace 和 Model Profile。
- 消息、工具调用、Artifact 和 Usage 可查询。
- 删除 Session 时可选择是否删除 Artifact。
- 支持导出 JSON/Markdown。

### 验收

- 重启后 Session 可恢复。
- 不同 Session 的上下文、Task 和文件权限不串扰。

## FR-04 Agent 对话

### 需求

- 支持流式输出、中断、重试和继续。
- 显示模型、Reasoning、Provider 和 Fallback 状态。
- 模型错误、上下文超限和限流有明确分类。
- 最终结果与中间工具事件分离。
- 不允许失败事件被包装为成功。

### 验收

- 用户中断后停止后续工具调用。
- Provider 故障时按策略 Fallback，并记录原因。

## FR-05 Workspace

### 需求

- 用户显式选择 Workspace。
- 默认只允许访问 Workspace 内部。
- 路径规范化并阻止 `..`、符号链接逃逸和绝对路径越界。
- 支持只读和读写模式。
- Workspace 权限变化需要重新确认。

### 验收

- 文件工具无法访问未授权 Home、SSH、系统配置和其他 Workspace。

## FR-06 Tool 系统

### 需求

每个 Tool 必须声明：

- Schema。
- 权限。
- 风险等级。
- 副作用类型。
- 并发范围。
- 是否支持 dry-run、checkpoint、rollback。

执行前必须完成参数、权限、风险和并发检查。

### 风险等级

- Low：纯读取。
- Medium：Workspace 内可恢复写入。
- High：外部网络写入、执行命令、发布。
- Irreversible：删除、部署、覆盖远程资源、付款等。

### 验收

- High/Irreversible 工具未经确认不执行。
- Tool 失败保留结构化错误和审计记录。

## FR-07 Terminal

### 需求

- 默认关闭 Web Terminal。
- CLI Terminal 只在用户当前终端上下文执行。
- Desktop Terminal 使用受控 Worker。
- Shell 和参数由服务端 allowlist 控制。
- 设置连接数、并发进程、空闲超时和最大时长。
- Token 不进入 URL。

### 验收

- 未授权用户无法创建 PTY。
- 资源超限后 Worker 被终止并记录原因。

## FR-08 Code Mode

### 需求

- 用户输入开发任务并选择 Workspace。
- 创建 Task，返回唯一 task_id。
- Task 状态：queued、preparing、awaiting_approval、running、succeeded、failed、timed_out、cancelled。
- 记录 PID、退出码、日志、进度、Artifact、权限快照。
- 支持取消和超时。
- OpenCode 缺失时明确 `unavailable`，不得返回 simulated success。
- 多任务日志和结果隔离。

### 验收

- 每个 Task 最终只有一个终态。
- 进程退出后状态和退出码一致。
- 重启后能恢复未完成 Task 的可解释状态。

## FR-09 Harness

### 需求

- Stable Prefix：同一 Session 内可检测 drift。
- Constraint：保留来源和优先级，不把用户文本提升为 System Policy。
- Model Router：只处理成本与质量。
- Context Engine：真实 token budget、Anchor、压缩和检索。
- Tool Schema：跨轮次字节稳定。
- 每个模块可独立启停和健康检查。

### 验收

- 配置关闭 Harness 后确实关闭。
- 单模块失败不会静默改变整个系统行为。
- 诊断可查看每次模型和上下文决策原因。

## FR-10 高风险操作

### 需求

执行链：风险识别 → 影响预览 → Checkpoint → 用户确认 → 执行 → 验证 → 审计 → 可选回滚。

确认界面必须显示：

- 将执行的工具和参数。
- 影响文件、服务或远程资源。
- 是否可回滚。
- 最坏后果。

### 验收

- 仅提高模型等级不能跳过确认。
- 用户拒绝后无副作用。

## FR-11 Artifact

### 需求

- Task 输出文件必须登记 Artifact Manifest。
- 包含路径、类型、大小、摘要、创建者和时间。
- UI/CLI 可打开、导出和删除。
- Artifact 不得指向 Workspace 外部未授权路径。

## FR-12 Desktop

### 需求

- Main Process 负责本地服务生命周期。
- Renderer 不持有根 Token。
- Preload 仅暴露最小 IPC。
- `contextIsolation=true`、`nodeIntegration=false`、优先 `sandbox=true`。
- 外部链接使用系统浏览器。
- 自动更新遵循签名 Release Contract。

### 验收

- Renderer XSS 无法直接调用 Node、读取系统凭据或获取根服务 Token。

## FR-13 WebUI 与认证

### 需求

- 默认 `127.0.0.1`。
- 保护 API 未认证返回 `401`。
- Web 模式使用短期 Access Token 或 HttpOnly Cookie。
- 写操作具备 CSRF 防护。
- 严格 CSP，禁止不必要的 inline script。
- Remote Mode 单独开启。

## FR-14 日志、诊断和隐私

### 需求

- `deepagent doctor` 检查版本、Runtime、Provider、数据库、Workspace、Sandbox 和更新状态。
- 日志分为应用、Task、模型 Usage 和安全审计。
- 默认只保存在本地。
- 所有 Secret 统一脱敏。
- 用户可一键导出诊断包，并预览其中内容。

## FR-15 Skills 与 MCP

### 需求

- Skill 显示来源、版本、权限和摘要。
- 安装前显示权限。
- 支持禁用、卸载和更新。
- 第三方 Skill 不得自动获得高权限。
- MCP Server 具有独立 allowlist。

## FR-16 开源工程

必须包含：

- README、Quickstart、Architecture、Security Policy。
- CONTRIBUTING、Code of Conduct。
- Issue/PR 模板。
- License、NOTICE、第三方许可证。
- Development setup。
- Release process。
- Threat model。

## 7. 非功能需求

### NFR-01 安全

- Safe-by-default。
- Fail closed。
- Secret 零明文泄漏。
- 依赖和产物可验证。
- 高风险操作有确定性 Gate。

### NFR-02 可靠性

- Task 状态不能丢失或伪造。
- 数据写入使用事务或原子替换。
- 崩溃后 Session 与 Task 可恢复。

### NFR-03 性能

- CLI 冷启动目标 < 3 秒，不含首次 Runtime 下载。
- 本地 API 健康检查 < 500ms。
- 普通 UI 操作 < 200ms。
- 日志和历史使用分页，避免全量加载。

### NFR-04 可维护性

- 核心模块单一职责。
- Python 和 TypeScript 均开启格式、Lint、类型检查。
- 核心模块单元覆盖率目标 ≥ 80%。
- P0 流程必须有 E2E。

### NFR-05 兼容性

- Python 版本和 Node 版本统一声明。
- macOS/Linux 明确最低版本。
- Provider Adapter 通过契约测试。

### NFR-06 可观测性

- 每个 Task、Tool Call、Model Call 有 correlation id。
- 用户可查看关键决策，不暴露私有推理链。

## 8. 数据与权限模型

### 角色

首个本地版本只有本机用户，不引入复杂 RBAC。但仍区分：

- App Process。
- Renderer。
- Agent Runtime。
- Sandbox Worker。
- External Skill/MCP。

每层遵循最小权限。

## 9. 异常与边界场景

必须覆盖：

- 网络断开。
- Provider 限流、鉴权失败和超时。
- 模型上下文超限。
- 工具参数非法。
- Workspace 被删除或权限变化。
- Task Worker 崩溃。
- 数据库锁和迁移失败。
- 磁盘满。
- Runtime 下载中断或摘要错误。
- 更新后启动失败。
- 用户在高风险确认前关闭应用。

## 10. 发布门禁

以下任一项不满足则不得发布：

- P0/P1 安全缺陷为 0。
- Secret scan 为 0。
- 所有核心 E2E 通过。
- Clean-machine 安装、升级、回滚通过。
- Code Mode 各终态通过。
- 所有 Release 产物签名与校验通过。
- License 和 NOTICE 完整。
- 文档与实际命令一致。

## 11. 版本成功标准

- 用户在 15 分钟内完成安装、配置和首轮 Agent 任务。
- 默认配置不监听局域网。
- 用户不需要理解内部 Token 或管理员账号。
- Code Mode 不再出现永久 `dispatched`。
- 安装器不再吞掉校验或依赖失败。
- 贡献者能在一份文档内完成开发环境搭建和测试。
