# DeepSeekAgent 开源迭代计划

## 1. 唯一目标

用最少的新增功能，把项目收敛到一个可以安全、真实、可维护地公开开源的版本。

不以功能数量作为目标，不在开源前新增非核心玩法。

## 2. 总体策略

顺序不可颠倒：

1. 固化产品范围和架构契约。
2. 关闭安全与供应链阻断项。
3. 补齐核心执行闭环。
4. 统一产品主路径。
5. 建立严格测试和发布门禁。
6. 完成开源治理与发布。

## 3. 明确冻结的功能

在首个开源版本发布前，暂停新增：

- Desktop Pet 或其他非核心桌面玩法。
- 公网 WebUI 和多用户后台。
- 新 Gateway 平台。
- 新 Provider，除非用于修复现有核心兼容性。
- 新 Multi-Agent 编排能力。
- 新自动记忆系统。
- 新“免疫 Skill”生成能力。
- 与发布无关的 UI 大改。

## 4. Milestone 0：文档与基线冻结

### 目标

所有开发围绕统一 PRD、架构和测试基线开展。

### 任务

- 将本目录文档作为开源基线。
- 标记旧 PRD、旧架构和旧 Release 文档的状态：current、superseded、historical。
- 建立术语表：DeepSeekAgent、Workspace、Session、Task、Artifact、Harness、Skill。
- 确认 CLI 和 Desktop 为唯一主入口。
- 确认统一目录为 `~/.deepagent`。

### 出口条件

- 产品、技术和测试负责人对 P0 范围无冲突。
- 不存在两份同时声称 current 的 PRD。

## 5. Milestone 1：安全止血

### 目标

消除当前可组合成宿主机接管的默认风险链。

### 任务

1. 撤销泄露凭据，清洗 Git 历史。
2. 默认绑定 `127.0.0.1`。
3. 删除未认证首用户注入。
4. 删除固定 `admin/123456`。
5. 删除 Preload 认证响应篡改。
6. Token 不进入 URL、localStorage 和日志。
7. 默认关闭 Web Terminal 和 Gateway allow-all。
8. 删除自动 `curl | sh`。
9. 收紧 CSP、Origin 和 CSRF。
10. 建立 `SECURITY.md` 和威胁模型。

### 出口条件

- AUTH 测试全部通过。
- Secret scan 全历史为 0。
- 默认启动无局域网监听。
- Renderer 无法获得根 Token。

## 6. Milestone 2：Release Contract 重建

### 目标

构建、安装、Desktop Runtime 和更新器只使用一个可信契约。

### 任务

- 创建 `release-manifest.schema.json`。
- 统一 Core、Embedded、WebUI、Desktop 产物命名。
- 修复 Core 包清单，包含 Harness 和 Code Mode。
- 修复 Embedded 包目录结构和当前平台提取。
- 签名 Manifest，强制 SHA-256。
- 生成 SBOM 和 provenance。
- 安装器和更新器 Fail closed。
- 增加 clean-machine install、upgrade、rollback 测试。

### 出口条件

- REL-001 至 REL-010 全部通过。
- 无任何校验失败后继续执行的代码。

## 7. Milestone 3：Code Mode 真正闭环

### 目标

Code Mode 从“启动脚本”升级为真实任务系统。

### 任务

- 建立 Task SQLite 表和事件表。
- 实现完整状态机。
- 记录 PID、退出码、stdout/stderr、Artifact。
- 支持超时、取消、崩溃恢复和进程树回收。
- OpenCode 缺失时返回明确 unavailable。
- 多任务日志隔离。
- task_id 使用严格 UUID。
- 增加 Worker 环境 allowlist 和独立 Workspace。

### 出口条件

- CODE-001 至 CODE-012 全部通过。
- 不再存在永久 `dispatched` 或 simulated success。

## 8. Milestone 4：权限 Gate 与最小 Sandbox

### 目标

把高风险操作控制从模型提示迁移到确定性执行层。

### 任务

- Tool Metadata 增加权限、风险和副作用。
- 实现 Workspace Policy。
- 路径穿越与符号链接防护。
- High/Irreversible 操作影响预览和确认。
- Checkpoint 与 rollback 接口。
- Worker 资源限制、网络策略和环境变量 allowlist。
- 将 Model Router 与安全 Gate 解耦。

### 出口条件

- TOOL、TERM 和高风险攻击用例全部通过。
- 用户拒绝确认后零副作用。

## 9. Milestone 5：Harness 收敛

### 目标

保留真正有价值、可验证的 DeepSeek 优化，移除夸大或无法证明的安全承诺。

### 任务

- 修复 Harness enabled 逻辑。
- Prefix freeze 变为真正不可覆盖或可检测 drift。
- Constraint 保留来源和优先级。
- 使用真实 tokenizer 管理预算。
- Context Anchor 支持更新和版本。
- 每个 Harness 模块有独立健康状态。
- Immune System 重新定位为质量诊断，不作为安全控制。
- 建立 Harness E2E 和 cache diagnostics。

### 出口条件

- HAR-001 至 HAR-010 全部通过。
- 文档不再声称启发式文本检查能确定性防止副作用。

## 10. Milestone 6：统一 Desktop 与 Runtime

### 目标

删除或降级重复实现，保证 Desktop 是同一 Runtime 的安全壳层。

### 任务

- 确定唯一 Electron 实现。
- 补齐 Mode IPC 契约。
- `sandbox=true` 或记录必要例外。
- Preload 使用最小 allowlist。
- Local API 崩溃恢复。
- 删除旧 Hermes 安装入口或明确标记为 upstream historical。
- 统一品牌、目录和命令。

### 出口条件

- DESK-001 至 DESK-010 全部通过。
- CLI 与 Desktop 的 Agent 行为契约一致。

## 11. Milestone 7：测试门禁和开源治理

### 目标

任何失败版本都不能被误发布。

### 任务

- Python format/lint/typecheck/unit/integration。
- TypeScript lint/typecheck/unit/component/E2E。
- Secret scan、SAST、dependency audit、license scan。
- Release Contract test。
- 全平台 E2E。
- CI 关键步骤严格非零退出。
- README、Quickstart、CONTRIBUTING、SECURITY、NOTICE、Code of Conduct。
- Issue 和 PR 模板。
- 第三方源码和二进制许可证审计。

### 出口条件

- develop 分支保护生效。
- 发布只能由通过全部门禁的 commit 触发。
- P0/P1 缺陷为 0。

## 12. 发布候选与开源

### RC1

- 内部和邀请测试。
- 只支持 CLI + macOS/Linux Desktop 核心流程。
- 收集安装和任务失败日志。

### RC2

- 完成故障注入、升级和回滚。
- 冻结 API 和目录结构。
- 完成许可证复核。

### v1.0.0-alpha

仅当以下全部满足时发布：

- Code Review 中 Critical/High 阻断项清零。
- 测试计划所有 P0 用例通过。
- 功能测试报告由 No-Go 更新为 Go。
- Release 产物可验证。
- 安全文档和漏洞报告渠道可用。

## 13. 优先级与依赖

```text
M0 文档基线
 └→ M1 安全止血
     └→ M2 Release Contract
         ├→ M3 Code Mode
         ├→ M4 Policy/Sandbox
         └→ M5 Harness
              └→ M6 Desktop 统一
                   └→ M7 CI/开源治理
                        └→ RC
```

## 14. 不应做的事情

- 不要一边修安全一边继续扩功能。
- 不要用增加测试数量掩盖测试断言宽松。
- 不要把 warning 当作可接受的发布结果。
- 不要把更强模型视为权限审批。
- 不要继续维持多套安装器、目录和桌面入口。
- 不要在无法真实执行测试时声称“完整测试通过”。

## 15. 最终衡量标准

项目是否准备好开源，只看五件事：

1. 默认是否安全。
2. 用户是否能成功安装和升级。
3. Agent 和 Code Mode 状态是否真实。
4. 核心任务是否有自动化端到端证明。
5. 外部贡献者是否能理解、运行、测试和审查项目。
