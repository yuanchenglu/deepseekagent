# DeepSeekAgent 测试计划与测试用例

## 1. 测试目标

证明首个开源版本在默认配置下：安全、可安装、可运行、状态真实、失败可解释、数据可恢复。

## 2. 测试层级

1. Static：Lint、Type Check、Secret Scan、SAST、License。
2. Unit：纯函数、状态机、策略、序列化、路径和 Token。
3. Contract：Provider、Tool、Release Manifest、IPC、API。
4. Integration：Runtime + DB + Tool + Worker。
5. E2E：CLI、Desktop、安装升级、Code Mode。
6. Security：认证、路径逃逸、命令执行、XSS/CSRF、供应链。
7. Reliability：崩溃恢复、超时、并发、磁盘满、网络异常。

## 3. 支持矩阵

| 维度 | 最低覆盖 |
|---|---|
| OS | macOS ARM64、macOS x64、Ubuntu x64 |
| Python | 项目声明的最低版、最高支持版 |
| Node | 锁定 LTS 版本 |
| 入口 | CLI、Desktop |
| Provider | DeepSeek、OpenAI-compatible mock、至少一个真实沙箱账号 |
| Workspace | 只读、读写、非法路径、符号链接 |

## 4. 核心测试用例

### A. 安装与发布

| ID | 场景 | 预期 |
|---|---|---|
| REL-001 | 干净机器安装 | 安装成功，doctor 通过 |
| REL-002 | Manifest 签名错误 | 立即失败，无文件覆盖 |
| REL-003 | SHA-256 错误 | 立即失败 |
| REL-004 | 下载中断 | 不进入已安装状态 |
| REL-005 | 架构不匹配 | 拒绝安装 |
| REL-006 | 升级成功 | 配置和 Session 保留 |
| REL-007 | 升级后启动失败 | 自动或手动回滚成功 |
| REL-008 | Core 包清单 | 包含 Harness、Code Mode 和入口 |
| REL-009 | Embedded 包路径 | 不产生双重 embedded 目录 |
| REL-010 | SBOM/签名/Provenance | 每个产物均存在且可验证 |

### B. 认证与网络

| ID | 场景 | 预期 |
|---|---|---|
| AUTH-001 | 默认启动监听地址 | 仅 127.0.0.1 |
| AUTH-002 | 未认证访问保护 API | 401 |
| AUTH-003 | 数据库存在首用户但无 Token | 仍为 401 |
| AUTH-004 | 固定 admin/123456 登录 | 不存在该默认凭据 |
| AUTH-005 | Token 出现在 URL | 测试失败，产品禁止 |
| AUTH-006 | Renderer 读取根 Token | 无对应 IPC 能力 |
| AUTH-007 | CSRF 写请求 | 被拒绝 |
| AUTH-008 | 非允许 Origin | 被拒绝 |
| AUTH-009 | Access Token 过期 | 401，可安全刷新 |
| AUTH-010 | 日志搜索 API Key | 无明文匹配 |

### C. Session

| ID | 场景 | 预期 |
|---|---|---|
| SES-001 | 创建 Session | 返回唯一 ID |
| SES-002 | 重启恢复 | 消息和设置完整 |
| SES-003 | 删除 Session | 数据按选择删除 |
| SES-004 | 两 Session 并发 | 上下文不串扰 |
| SES-005 | 导出 Markdown/JSON | 内容完整、Secret 已脱敏 |
| SES-006 | 数据库锁 | 重试或明确失败，不损坏数据 |

### D. Agent Runtime

| ID | 场景 | 预期 |
|---|---|---|
| AGT-001 | 普通对话 | 正常完成 |
| AGT-002 | 流式中断 | 停止模型和后续工具 |
| AGT-003 | Provider 401 | 明确鉴权错误 |
| AGT-004 | Provider 429 | 按策略退避/Fallback |
| AGT-005 | Context 超限 | 压缩或明确提示 |
| AGT-006 | 模型切换 | Context 与 Provider 状态一致 |
| AGT-007 | Fallback | 记录触发原因和模型 |
| AGT-008 | 最大迭代数 | 安全终止，不无限循环 |

### E. Tool 与 Workspace

| ID | 场景 | 预期 |
|---|---|---|
| TOOL-001 | 读取 Workspace 内文件 | 成功 |
| TOOL-002 | `../` 路径逃逸 | 拒绝 |
| TOOL-003 | 符号链接逃逸 | 拒绝 |
| TOOL-004 | 绝对路径越界 | 拒绝 |
| TOOL-005 | 只读 Workspace 写入 | 拒绝 |
| TOOL-006 | 两个重叠路径并发写 | 串行或冲突 |
| TOOL-007 | High 风险工具 | 等待确认 |
| TOOL-008 | 用户拒绝确认 | 零副作用 |
| TOOL-009 | 工具超时 | 终止并记录 timeout |
| TOOL-010 | 工具输出过大 | 持久化并返回摘要 |

### F. Terminal

| ID | 场景 | 预期 |
|---|---|---|
| TERM-001 | 默认 Web Terminal | 关闭 |
| TERM-002 | 未授权创建 PTY | 拒绝 |
| TERM-003 | 客户端指定任意 Shell | 拒绝 |
| TERM-004 | 超过连接数 | 拒绝新连接 |
| TERM-005 | 空闲超时 | 自动终止 |
| TERM-006 | 命令访问 Workspace 外 | 按 Sandbox 策略拒绝 |

### G. Code Mode 状态机

| ID | 场景 | 预期 |
|---|---|---|
| CODE-001 | 创建任务 | queued，唯一 task_id |
| CODE-002 | Worker 启动 | preparing→running |
| CODE-003 | 正常完成 | succeeded，exit_code=0 |
| CODE-004 | 子进程非零退出 | failed，保留 stderr |
| CODE-005 | 二进制缺失 | unavailable/failed，不得 simulated success |
| CODE-006 | 超时 | timed_out，进程被回收 |
| CODE-007 | 用户取消 | cancelled，无残留进程 |
| CODE-008 | 应用崩溃重启 | 状态恢复或标记 interrupted |
| CODE-009 | 并发任务 | 日志、PID、Artifact 隔离 |
| CODE-010 | 恶意 task_id | Schema 校验拒绝 |
| CODE-011 | 环境变量泄漏 | Worker 只收到 allowlist |
| CODE-012 | 网络默认策略 | 未授权网络请求失败 |

### H. Harness

| ID | 场景 | 预期 |
|---|---|---|
| HAR-001 | Harness enabled=false | 模块真实关闭 |
| HAR-002 | Prefix 首次冻结 | 指纹稳定 |
| HAR-003 | 重复 freeze | 拒绝或明确 drift |
| HAR-004 | Injection 请求失败 | 不丢失未提交变更 |
| HAR-005 | 用户约束 | 保留 user priority，不提升为 system |
| HAR-006 | Router 高风险 | 选模与安全 Gate 独立 |
| HAR-007 | 模块初始化失败 | 健康状态可见，不静默 |
| HAR-008 | 中文长上下文 | token budget 使用真实 tokenizer |
| HAR-009 | Tool Schema 多轮 | 字节指纹一致 |
| HAR-010 | Anchor 更新 | 新目标能够替换旧目标 |

### I. Desktop/Electron

| ID | 场景 | 预期 |
|---|---|---|
| DESK-001 | contextIsolation | true |
| DESK-002 | nodeIntegration | false |
| DESK-003 | sandbox | true 或有审计例外 |
| DESK-004 | 外部链接 | 系统浏览器打开 |
| DESK-005 | Preload API | 仅 allowlist |
| DESK-006 | 自动登录 | 不使用固定密码 |
| DESK-007 | Mode IPC | get/set/event 契约一致 |
| DESK-008 | Local API 崩溃 | UI 展示故障并可重启 |
| DESK-009 | 更新包签名错误 | 拒绝更新 |
| DESK-010 | Renderer XSS 模拟 | 无法读取系统凭据或执行 Node |

### J. Secret、License 与开源工程

| ID | 场景 | 预期 |
|---|---|---|
| OSS-001 | Git 全历史 Secret Scan | 0 |
| OSS-002 | 当前工作树 Secret Scan | 0 |
| OSS-003 | 第三方依赖 License | 清单完整 |
| OSS-004 | NOTICE | 包含所有必要归属 |
| OSS-005 | README 命令 | 全部可执行 |
| OSS-006 | CONTRIBUTING | 新贡献者可完成环境搭建 |
| OSS-007 | CI 失败 | 阻止合并和发布 |

## 5. 安全攻击用例

- 使用 query token、伪造 Origin、重放 JWT。
- XSS 读取 localStorage、调用 Preload、访问 IPC。
- 路径穿越、符号链接、大小写路径绕过。
- 命令分隔符、Heredoc、任务 ID 注入。
- 恶意 Skill/MCP 请求高权限。
- Runtime Manifest 指向 HTTP、重定向到非允许域。
- 压缩包路径穿越和软链接覆盖。
- 日志注入和 Secret 外泄。

## 6. 可靠性与并发

- 100 个 Session 顺序创建与恢复。
- 10 个 Task 并发，资源配额正确。
- Worker 强杀后状态一致。
- 磁盘满时不损坏 SQLite 和配置。
- 日志轮转和任务保留策略生效。
- 多进程同时启动时单实例锁正确。

## 7. CI 门禁

每个 PR：format、lint、typecheck、unit、contract、secret scan、dependency audit。

合并 develop：integration、security、package contract。

Release：全平台 build、E2E、clean-machine install、upgrade/rollback、SBOM、sign、verify。

任何核心步骤失败必须返回非零退出码，不得以 warning 继续。
