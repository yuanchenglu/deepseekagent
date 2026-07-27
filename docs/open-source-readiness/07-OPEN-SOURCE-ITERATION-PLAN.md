# DeepSeekAgent 最终开源执行计划

> **已归档：本文件自三阶段计划生效后不再作为执行依据。** 许可证、安全、发布契约和 CLI 首发工作迁移到 [07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md](./07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md)；WebUI、Code Mode 与 Runtime 工作迁移到 [08-PHASE-2-WEBUI-STABLE-BETA.md](./08-PHASE-2-WEBUI-STABLE-BETA.md)；新 Electron 工作迁移到 [09-PHASE-3-DUAL-MODE-ELECTRON.md](./09-PHASE-3-DUAL-MODE-ELECTRON.md)。以下内容仅保留为历史审计记录。

> 工作分支：`develop`
> 文档状态：Final Plan，待产品确认后执行
> 唯一目标：不扩张非核心功能，以最小改造把项目收敛为普通用户可用、默认安全、可验证发布的开源 Agent 产品。

---

## 1. 最终产品决策

### 1.1 核心原则

DeepSeekAgent 的认证与网络策略统一为：

> **本地无感，远程设防。**

这意味着：

- 普通用户在本机使用 Desktop 时，不需要输入用户名、密码或查找随机 Token。
- 本地服务默认仅监听 `127.0.0.1`，不暴露给局域网。
- 用户主动开启局域网访问时，才进入远程访问设置流程并创建独立凭据。
- 首个开源版本不默认支持公网直接暴露；公网访问必须通过受支持的 TLS 反向代理或安全隧道方案。
- 模型能力、默认密码和“这是上游代码”都不能替代最终产品的安全边界。

### 1.2 默认密码最终决策

不采用“让用户到文件中寻找随机密码”的方案，也不继续把 `admin/123456` 作为 DeepSeekAgent 的用户登录方式。

最终处理方式：

1. **Desktop 本地模式**：无登录页、无用户可见密码，由 Desktop 主进程建立本机设备会话。
2. **本机浏览器模式**：通过 `deepagent webui open` 或 Desktop 的“在浏览器中打开”生成一次性登录 Ticket。
3. **局域网模式**：用户首次开启时在图形化向导中自行创建密码；不得沿用固定默认密码。
4. **已有安装迁移**：发现 `admin/123456` 时，本地模式自动迁移，不打断用户；若要开启远程模式，必须先设置新凭据。
5. **服务端改密状态**：不得再由 Preload 篡改或隐藏。

### 1.3 上游问题处理原则

DeepSeekAgent 不承担“重写所有 Hermes、Hermes Studio 和 OpenCode 安全实现”的任务，但必须保证最终交付产品的默认使用路径成立。

所有上游问题按以下四类处理：

| 类型 | 处理方式 | 示例 |
|---|---|---|
| 集成层可覆盖 | DeepSeekAgent 通过启动参数、配置或 Adapter 覆盖 | 监听地址、CORS、Gateway allow-all |
| 上游缺陷且影响默认路径 | 本项目先维护最小补丁，同时向上游提 Issue/PR | 默认认证、Token 处理 |
| 非默认高级功能风险 | 默认关闭，用户开启时给出向导和风险说明 | LAN WebUI、Web Terminal |
| 不影响首版核心路径 | 记录限制并暂缓，不为此扩大 Fork | 复杂多用户、公开 SaaS |

原则：**不因上游存在缺陷而忽略最终产品风险，也不为追求理论完美而大规模重写上游。**

---

## 2. 首个开源版本的产品范围

### 2.1 必须稳定交付

- Desktop 本地无感启动与使用。
- CLI 安装、配置、会话和 Agent 主链路。
- 本机浏览器一次性无感登录。
- Provider 配置与凭据保护。
- Agent 对话、工具调用、中断、失败反馈。
- Workspace 授权边界。
- Code Mode 真实任务状态闭环。
- 高风险操作确认。
- 可验证的构建、安装、升级和回滚。
- 完整测试门禁和开源治理文档。

### 2.2 保留但降级为非阻断功能

- Gateway 已有平台。
- MCP。
- Browser Tools。
- Skills 安装。
- 多 Provider Fallback。
- LAN WebUI。

这些功能不得影响本地核心链路；存在风险或不完整时可以默认关闭、标记 Experimental。

### 2.3 首版明确不做

- 公网直接暴露 WebUI。
- 企业多租户和复杂 RBAC。
- Passkey、扫码登录、云账户体系。
- 新 Gateway 平台。
- 新 Provider。
- 新 Multi-Agent 编排。
- Desktop Pet 和非核心视觉玩法。
- 新记忆系统或自动生成长期 Immune Skill。
- 与开源发布无关的大规模 UI 重构。
- 对 Hermes/OpenCode 的全面重写。

---

## 3. 目标使用模式

### 3.1 Mode A：Desktop Local，默认模式

用户流程：

```text
安装 DeepSeekAgent
→ 双击启动
→ 自动启动本地 Runtime
→ 自动建立本机设备会话
→ 直接进入工作台
```

产品要求：

- 服务仅监听 `127.0.0.1`。
- 用户不接触内部 Token。
- Desktop Main Process 保存设备级 Secret。
- Renderer 只获得短时会话，不获得根 Token。
- Secret 优先存入操作系统安全存储；无法使用时至少以 `0600` 权限保存，并明确降级状态。
- `contextIsolation=true`、`nodeIntegration=false`，Preload 只暴露最小 IPC。

### 3.2 Mode B：Local Browser

用户流程：

```text
点击“在浏览器中打开”
或执行 deepagent webui open
→ 系统浏览器打开
→ 一次性 Ticket 自动换取本地会话
→ 直接进入工作台
```

要求：

- Ticket 一次性使用。
- 有效期短。
- 使用后立即失效。
- 不进入长期日志。
- 只能从本机回环地址使用。

### 3.3 Mode C：LAN Remote，显式开启

用户流程：

```text
设置 → 远程访问
→ 阅读风险说明
→ 创建远程用户名/密码
→ 系统执行安全检查
→ 开启局域网访问
→ 显示访问地址和关闭按钮
```

要求：

- 默认关闭。
- 只有完成凭据设置后才能绑定非回环地址。
- 固定默认密码存在时禁止开启。
- 远程会话与 Desktop 本地设备会话分离。
- 认证失败限流，写操作有 CSRF/Origin 校验。
- Web Terminal 默认仍关闭，需二次独立开启。
- 明确标记为可信局域网功能，不声称公网安全。

### 3.4 Mode D：Public Remote

首个开源版本不提供“直接开放公网端口”的产品承诺。

仅允许：

- TLS 反向代理；或
- Tailscale、ZeroTier 等受支持安全隧道；或
- 用户自行部署并承担高级运维责任。

文档必须明确：直接将端口暴露到公网不在支持范围内。

---

## 4. 执行顺序

执行严格按照以下顺序，不在计划确认前修改代码。

```text
M0 产品决策与文档冻结
 └→ M1 本地无感认证与网络边界
      └→ M2 远程设防与迁移
           └→ M3 Release Contract
                ├→ M4 Code Mode 真实闭环
                ├→ M5 Workspace / Tool Gate / 最小 Sandbox
                └→ M6 Harness 收敛
                     └→ M7 Desktop 与 Runtime 统一
                          └→ M8 测试门禁与开源治理
                               └→ RC
```

M4、M5、M6 可在 M3 契约稳定后并行开发，但各自未通过出口条件时不得进入 RC。

---

## 5. Milestone 0：产品与文档冻结

### 目标

使全项目只遵循一套产品目标、认证模型、架构和测试标准。

### 工作项

1. 将本计划标记为当前唯一执行计划。
2. 修改 PRD：把“无默认密码”细化为“本地无感设备认证、远程单独建凭据”。
3. 修改 Code Review：删除“用户获取随机 bootstrap 密码”的误导性表述。
4. 产品架构增加四种运行模式及边界。
5. 技术架构增加 Desktop Device Session、One-time Ticket、Remote Credential Realm。
6. 对旧 PRD、旧架构和旧计划标记 `superseded`、`historical` 或 `current`。
7. 建立上游补丁登记表：来源、风险、覆盖方式、是否向上游提交。

### 出口条件

- 不存在两份同时声称 current 的 PRD 或 Plan。
- 本地模式、浏览器模式、LAN 模式、公网模式定义无冲突。
- 团队确认首版冻结范围。

---

## 6. Milestone 1：本地无感认证与网络边界

### 目标

普通用户零登录负担，同时消除默认局域网暴露和根 Token 泄漏。

### 工作项

1. Desktop 启动 WebUI 时强制绑定 `127.0.0.1`。
2. 删除未认证请求自动注入数据库第一个用户的逻辑。
3. 增加 Desktop Device Session：
   - Main Process 生成并持有设备 Secret；
   - 通过受限 IPC 请求一次性 Ticket；
   - 服务端换取短时 Session；
   - Renderer 不可读取根 Secret。
4. 增加 `deepagent webui open`，支持本机浏览器无感登录。
5. Token 不进入 query、`localStorage` 或普通日志；一次性 Ticket 例外仅用于本机瞬时跳转，使用后即销毁，并避免进入访问日志。
6. 删除 Preload 对认证结果的篡改。
7. 默认关闭 Web Terminal、Gateway allow-all 和外部网络监听。
8. 增加本地认证健康检查与诊断。

### 验收用例

- Desktop 首次启动不出现登录页。
- 用户无需查看任何文件或复制 Token。
- 另一台局域网设备无法连接默认服务。
- 未认证保护 API 返回 `401`。
- Renderer 无法读取根 Secret。
- 本机浏览器 Ticket 重复使用失败。
- Ticket 过期后失败。
- XSS 场景无法获取长期根凭据。

### 出口条件

- AUTH-LOCAL 全部通过。
- 默认启动仅存在 loopback 监听。
- 不再依赖 `admin/123456` 完成本地登录。

---

## 7. Milestone 2：远程设防与旧安装迁移

### 目标

允许用户主动开启 LAN 访问，同时确保固定默认密码不能成为远程入口。

### 工作项

1. 增加 Remote Access 设置页和开启向导。
2. 开启前强制创建远程凭据。
3. 远程凭据使用 scrypt 或 Argon2id，不能明文保存。
4. 增加登录限流、会话撤销、CSRF、Origin allowlist。
5. 显示当前监听地址、活跃远程会话和“一键关闭远程访问”。
6. 本地设备会话与远程账户会话使用不同认证域。
7. 旧安装迁移：
   - 本地启动自动迁移到设备会话；
   - 不要求用户输入旧默认密码；
   - 检测到固定默认密码时，远程开关锁定；
   - 设置新凭据后才允许开启 LAN。
8. 公网访问在 UI 和文档中标记为不支持直接暴露。

### 首版不增加

- Passkey。
- 扫码配对。
- 云账户。
- 邮箱找回密码。

### 验收用例

- 未设置远程凭据时无法绑定 `0.0.0.0`。
- `admin/123456` 无法开启远程模式。
- 错误密码连续尝试触发限流。
- 关闭远程模式后现有远程会话立即失效。
- 本地 Desktop 使用不受远程密码变化影响。

### 出口条件

- AUTH-REMOTE 全部通过。
- 远程访问始终为显式 opt-in。
- 固定默认凭据不再出现在任何支持路径中。

---

## 8. Milestone 3：Release Contract 重建

### 目标

保证用户安装的内容与仓库、文档和测试完全一致。

### 工作项

1. 建立签名的 Release Manifest Schema。
2. 统一 Core、Embedded、WebUI、Desktop 产物命名。
3. Core 包明确包含 `deepagent_harness/` 和 `deepagent_code_mode/`。
4. Embedded 按平台打包或正确提取，避免 `embedded/embedded/`。
5. 强制 SHA-256，校验缺失或失败时立即终止。
6. 删除或替换自动 `curl | sh`。
7. 安装、升级和回滚共用同一 Manifest。
8. 生成 SBOM、NOTICE 和 provenance。
9. 修复 smoke test：任一核心命令失败则 Job 失败。
10. 完成 clean-machine 安装、升级、回滚测试。

### 出口条件

- 无任何 `|| true` 吞掉关键校验。
- 构建器、安装器和更新器使用同一契约。
- 干净环境可完成安装和首轮本地无感启动。

---

## 9. Milestone 4：Code Mode 真实任务闭环

### 目标

将当前“已派发”升级为可追踪、可取消、可恢复的任务系统。

### 工作项

- Task 和 Task Event 持久化。
- 状态机：`queued → preparing → awaiting_approval → running → succeeded/failed/timed_out/cancelled`。
- 记录 PID、退出码、stdout、stderr、Artifact、开始与完成时间。
- 超时、取消、进程树回收和崩溃恢复。
- 多任务日志隔离。
- OpenCode 缺失返回 `unavailable`，不再 simulated success。
- 严格 UUID 与路径校验。
- 环境变量 allowlist 和独立 Workspace。

### 出口条件

- 每个任务最终只有一个终态。
- 不存在永久 `dispatched`。
- 任务重启恢复、取消、超时和失败用例全部通过。

---

## 10. Milestone 5：Workspace、Tool Gate 与最小 Sandbox

### 目标

把安全控制放在确定性执行层，而不是依赖更强模型或 Prompt。

### 工作项

- 用户显式选择 Workspace。
- 默认只允许 Workspace 内部访问。
- 防止 `..`、绝对路径和符号链接逃逸。
- Tool Metadata 声明权限、风险、副作用和回滚能力。
- High/Irreversible 操作显示影响预览并请求确认。
- 用户拒绝后零副作用。
- Worker 使用环境变量 allowlist、资源限制和独立工作目录。
- 首版最小 Sandbox 以“文件边界 + 环境边界 + 资源边界”为准；平台级强隔离可分阶段增强。

### 出口条件

- Workspace 越界测试全部失败关闭。
- 高风险操作未经确认不能执行。
- Code Mode 不继承无关 API Key 和宿主敏感环境变量。

---

## 11. Milestone 6：Harness 收敛

### 目标

保留能够验证的 DeepSeek 优化，删除无法证明的安全承诺。

### 工作项

- 修复 Harness enabled 永真问题。
- Prefix freeze 真正不可覆盖或可检测 drift。
- Constraint 保留来源和优先级。
- Model Router 只负责成本与质量，不承担授权。
- Immune System 定位为质量诊断，不作为副作用安全控制。
- 使用真实 tokenizer 管理 Context Budget。
- Context Anchor 可版本化和更新。
- 每个 Harness 模块有独立健康状态、测试和降级策略。

### 出口条件

- Harness 开关真实有效。
- 模块失败不会静默改变整体语义。
- 文档陈述与代码能力一致。

---

## 12. Milestone 7：Desktop 与 Runtime 统一

### 目标

Desktop 只做安全壳层，CLI 与 Desktop 共享同一 Agent Runtime 和行为契约。

### 工作项

- 确认唯一 Electron 实现。
- 补齐 App/Code Mode IPC 契约。
- 修复 Mode Broadcast 参数和 spawn error。
- Preload 使用最小 allowlist。
- 本地服务启动、崩溃和退出可恢复。
- 删除或隔离旧 Hermes 安装入口。
- 统一 DeepSeekAgent 品牌、命令和 `~/.deepagent` 数据目录。

### 出口条件

- CLI 与 Desktop 同一任务得到一致状态语义。
- Desktop 不包含第二套独立 Agent 业务逻辑。
- 本地无感认证在所有支持平台通过。

---

## 13. Milestone 8：测试门禁与开源治理

### 目标

任何核心链路失败的版本都不能被发布。

### 必须建立的门禁

- Python：format、lint、typecheck、unit、integration。
- TypeScript：lint、typecheck、unit、component、E2E。
- Authentication Mode Matrix。
- Release Contract Test。
- Clean-machine install/upgrade/rollback。
- Code Mode 全状态 E2E。
- Workspace 和 Tool 安全攻击用例。
- Secret scan、SAST、dependency audit、license scan。
- SBOM、签名和 provenance 验证。
- macOS、Linux 以及声明支持的 Windows 路径测试。

### 开源治理产物

- README、Quickstart、Architecture。
- SECURITY、Threat Model。
- CONTRIBUTING、Code of Conduct。
- License、NOTICE、第三方清单。
- Issue/PR 模板。
- Release Process。
- Upstream Patch Ledger。

### 出口条件

- `develop` 分支保护生效。
- 发布只能由全部门禁通过的 Commit 触发。
- P0/P1 阻断缺陷为 0。
- 功能测试报告从 No-Go 更新为 Go。

---

## 14. 测试验收矩阵

| 能力 | 核心验收 |
|---|---|
| Desktop Local | 无登录、仅 loopback、根 Secret 不进入 Renderer |
| Local Browser | 一次性 Ticket、过期/重放失败 |
| LAN Remote | 显式开启、先建凭据、限流、可立即关闭 |
| Migration | 老用户无需查密码；固定密码不能进入远程模式 |
| Release | 签名与摘要错误强制失败 |
| Agent | 中断、重试、Fallback 和错误状态真实 |
| Code Mode | 完整终态、取消、超时、恢复 |
| Workspace | 越界、符号链接逃逸被拒绝 |
| High-risk Tool | 未确认零副作用 |
| Harness | 可启停、可诊断、无夸大安全声明 |
| Desktop/CLI | 同一 Runtime、同一状态契约 |

---

## 15. 发布阶段

### RC1

- 本地 Desktop 与 CLI 核心路径。
- Local Browser 一次性登录。
- LAN Remote 标记 Experimental。
- 邀请测试，重点收集安装、认证和 Code Mode 失败信息。

### RC2

- 完成迁移、故障注入、升级与回滚。
- 完成许可证复核。
- 冻结 Release Contract、数据目录和核心状态机。

### 首个公开 Alpha

仅当以下全部满足时发布：

- Desktop 本地模式真正无感。
- 默认无局域网监听。
- 固定默认密码不属于任何支持路径。
- Critical/High 发布阻断项清零。
- 所有 P0 测试通过。
- Release 产物可验证。
- Code Mode 有真实终态。
- 安全边界、上游来源和限制文档完整。

---

## 16. 执行期间的禁止事项

- 不在本计划确认前开始代码整改。
- 不把随机密码文件暴露给普通用户。
- 不以保留 `admin/123456` 换取本地易用性。
- 不为解决上游全部问题而建立不可维护的大型 Fork。
- 不在开源前新增非核心功能。
- 不将更强模型视为权限审批。
- 不允许 warning 后继续发布关键失败。
- 不在未运行测试时声称测试通过。
- 不直接把 WebUI 端口暴露到公网。

---

## 17. 最终衡量标准

首个开源版本是否成功，只看以下六点：

1. 普通用户是否可以安装后直接使用，不接触内部密码和 Token。
2. 默认状态是否只允许本机访问。
3. 用户主动开启远程访问时是否有明确、独立且可关闭的安全边界。
4. Agent 与 Code Mode 的状态是否真实、可追踪、可恢复。
5. 安装、升级和 Release 是否可验证、失败关闭。
6. 外部贡献者是否能够理解、运行、测试和审查项目。
