# DeepSeekAgent Code Review 报告

## 1. 结论

当前版本判定为 **No-Go**：不适合直接公开发布、远程部署或作为可信生产 Agent 使用。

根因不是单一缺陷，而是以下问题可组合形成完整风险链：

1. WebUI 默认可能暴露至局域网。
2. 默认认证路径存在绕过和隐式用户注入。
3. 桌面端使用固定管理员凭据并隐藏强制改密状态。
4. Terminal、文件、Agent、配置和工作流等高权限能力依赖上述弱认证边界。
5. 安装、Runtime 下载和发布流程未形成强校验闭环。
6. Code Mode 仅完成“派发”，未完成任务生命周期。
7. Harness 部分能力停留在提示或启发式检查层，却被文档描述为确定性控制。

## 2. 审查范围

- Agent Runtime：`run_agent.py`、模型适配、工具调用、并发、会话与压缩。
- Harness：Prefix、Model Router、Hard Constraint、Immune System、Context Layout。
- Code Mode：Dispatcher、Handler、`embedded/run_task.sh`、OpenCode 集成。
- WebUI：服务监听、认证、JWT、CORS/CSP、Terminal WebSocket。
- Electron：Main、Preload、Mode Manager、Runtime Manager。
- Release：构建脚本、安装器、GitHub Actions、Runtime 下载。
- Tests：Harness、Code Mode、Release smoke test。

本报告为静态源码审查。由于当前环境未完成仓库本地构建和全量动态执行，所有动态测试项在测试报告中单独标记。

## 3. Critical 问题

### C-01 默认认证边界不成立

**现象**：服务默认暴露范围、认证中间件默认行为和首用户注入机制组合后，可能使未认证请求获得高权限用户上下文。

**影响**：文件、终端、配置、Agent、Gateway、MCP、Workflow 等接口可能被越权访问。

**必须满足的修复标准**：

- 默认监听 `127.0.0.1`。
- 所有保护接口未认证一律返回 `401`。
- 删除“认证关闭时选择数据库第一个用户”的逻辑。
- 远程模式必须显式开启，并强制 TLS、Origin、CSRF、速率限制和审计。

### C-02 固定管理员密码与认证响应篡改

**现象**：Electron Preload 使用固定 `admin/123456` 自动登录；Token/JWT 写入 `localStorage`；同时修改 `/api/auth/me` 返回值，隐藏强制修改默认密码标记。

**影响**：任何 Renderer XSS、恶意依赖或调试注入都可能获取管理员会话。

**修复标准**：

- 删除固定账号密码。
- 首次启动使用一次性随机 bootstrap token。
- Token 不进入 URL 和 `localStorage`。
- 使用 HttpOnly Cookie 或系统凭据存储。
- Preload 不得修改服务端认证结果。

### C-03 自动执行远程安装脚本

**现象**：Electron 在后端缺失时执行 `curl | sh`。

**影响**：下载域、DNS、CDN 或脚本被攻击即可导致宿主机任意代码执行。

**修复标准**：固定版本、下载到本地、验证签名和 SHA-256、展示来源、用户确认后执行。

### C-04 校验失败仍继续安装

**现象**：安装器对校验函数使用 `|| true`；校验文件缺失或校验工具缺失时继续安装；Runtime manifest 的摘要不是强制字段。

**修复标准**：摘要或签名缺失、错误时必须失败；Manifest 必须签名；生产环境禁止无签名自定义 Runtime URL。

### C-05 构建器、安装器和运行时协议断裂

**主要问题**：

- 构建产物命名与安装器下载命名不一致。
- Core 包显式清单可能遗漏 `deepagent_harness/` 和 `deepagent_code_mode/`。
- Embedded 解压路径可能产生 `embedded/embedded/`。
- 安装器只提取二进制，未保证 `run_task.sh`、配置和工作区契约完整。

**修复标准**：所有组件共同读取一个签名的 Release Manifest；禁止各脚本独立硬编码文件名和目录结构。

### C-06 Secret 已进入 Git 历史

**修复标准**：吊销全部相关凭据；清洗 Git 历史；重新 clone；启用 GitHub Secret Scanning 与 CI secret scan。

## 4. High 问题

### H-01 Code Mode 没有完成态

当前流程只写入 `dispatched`，缺少：

- `running/succeeded/failed/timed_out/cancelled` 状态。
- 退出码和标准输出回写。
- 取消、超时、重试、心跳、进程回收。
- 多任务日志隔离。

### H-02 所谓隔离并非 Sandbox

仅切换配置目录，子进程仍继承宿主环境、文件系统、网络和当前工作目录。必须引入环境变量 allowlist、独立工作区、资源限制、网络策略和平台级 Sandbox。

### H-03 Electron 双模式链路不完整

Client 需要的 mode IPC 与 Preload 暴露接口不一致；broadcast 回调签名不一致；OpenCode spawn 缺少 `error` 处理和真实二进制检测。

### H-04 Terminal 是宿主机 Shell

Token 可通过 query 传输；Shell executable 可由客户端指定；缺少连接、PTY、运行时长和资源配额。默认应关闭。

### H-05 JWT 与浏览器安全边界过弱

长时效 JWT、localStorage、query token、宽松 CSP 和弱 Origin 处理会扩大 XSS/CSRF 攻击面。

## 5. Harness 设计问题

### 5.1 更强模型不等于安全控制

不可逆操作路由到 Pro Max 只能提升推理质量，不能替代：权限校验、影响预览、checkpoint、用户确认、执行审计与回滚。

### 5.2 Immune System 是事后启发式文本检查

它无法确认数据库、文件、Git 或云资源的真实副作用；关键词出现也不代表要求已满足。应定位为“质量提示器”，不能定位为安全控制器。

### 5.3 用户约束被提升到 System 区域

正则提取后的用户文本直接进入冻结前缀，可能造成优先级提升。必须保留约束来源和优先级：System > Developer > Workspace > User。

### 5.4 Prefix 冻结未被强制

`freeze()` 可重复覆盖；Injection 队列无界且非线程安全；请求失败时可能丢失已消费变更。

### 5.5 Context Layout 主要是模板拼接

没有真实 token 预算控制、压缩、索引或检索闭环；中文 token 估算偏差较大；Anchor 更新检测可能误判。

### 5.6 Harness 开关逻辑错误

`routing_config.get("enabled", False) or True` 永远为真；另一方面初始化异常又会静默关闭全部 Harness。需要显式配置、模块级健康状态和可观测错误。

## 6. 测试与发布问题

- Code Mode 测试只验证“不崩溃”和产生 task id，不验证真实任务成功。
- `simulated` 和无结果文件也可能被测试接受。
- Release smoke test 即使命令失败仍打印 PASSED。
- 构建过程显式跳过 WebUI、OpenCode、Skills 检查。
- 缺少 secret scan、SAST、依赖审计、SBOM、签名和 clean-machine 安装测试。

## 7. 维护性问题

- Hermes/DeepAgent 品牌、目录、安装脚本和仓库地址混杂。
- React/Vue、轻量 Electron/完整 Desktop 两套形态并存，主路径不清晰。
- `run_agent.py` 责任过重。
- 多个状态日志和任务目录无界增长。
- 第三方源码、二进制和许可证清单不完整。

## 8. 正向评价

- 已有随机 Token 和 `0600` 文件权限基础。
- Electron 已启用 context isolation 并关闭 node integration。
- 已有 SHA-256、临时目录解压、迭代预算锁和部分路径冲突检测。
- Harness 已开始输出路由原因和诊断信息。
- Release 拆分 Core/Embedded/WebUI 的方向合理。

## 9. 发布判定

在 P0 安全问题、Release Contract、Code Mode 状态机和真实发布门禁完成之前，禁止标记为公开 Beta 或 Production Ready。
