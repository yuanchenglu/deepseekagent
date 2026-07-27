# DeepSeekAgent 开源准备文档集

> 分支：`develop`
> 状态：三阶段执行基线
> 目标：先交付 CLI Alpha，再交付 WebUI Beta，最终交付双模式 Electron。

## 文档目录

1. [01-CODE-REVIEW.md](./01-CODE-REVIEW.md) — 当前代码审查结论、风险等级与证据。
2. [02-PRODUCT-ARCHITECTURE.md](./02-PRODUCT-ARCHITECTURE.md) — 产品定位、用户、能力边界与产品分层。
3. [03-TECHNICAL-ARCHITECTURE.md](./03-TECHNICAL-ARCHITECTURE.md) — 运行时、Harness、工具、桌面端、WebUI、任务系统与安全架构。
4. [04-PRD.md](./04-PRD.md) — 完整产品需求文档与开源版本验收标准。
5. [05-TEST-PLAN-AND-CASES.md](./05-TEST-PLAN-AND-CASES.md) — 测试策略、测试矩阵、完整核心测试用例。
6. [06-FUNCTIONAL-TEST-REPORT.md](./06-FUNCTIONAL-TEST-REPORT.md) — 当前功能验证报告、已验证结论和未执行项。
7. [07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md](./07-PHASE-1-OPEN-SOURCE-CLI-ALPHA.md) — 第一阶段：公开、可安装、可用的 CLI Alpha。
8. [08-PHASE-2-WEBUI-STABLE-BETA.md](./08-PHASE-2-WEBUI-STABLE-BETA.md) — 第二阶段：浏览器 WebUI Beta 与完整本地共存。
9. [09-PHASE-3-DUAL-MODE-ELECTRON.md](./09-PHASE-3-DUAL-MODE-ELECTRON.md) — 第三阶段：DeepAgent / DeepCode 双模式 Electron。
10. [10-ELECTRON-PREVIEW-STATUS.md](./10-ELECTRON-PREVIEW-STATUS.md) — PR #1 合入后的 Electron Preview 继续开发状态、无签名发布边界和剩余真实环境门禁。

原 [07-OPEN-SOURCE-ITERATION-PLAN.md](./07-OPEN-SOURCE-ITERATION-PLAN.md) 仅作历史审计记录，不再是执行依据。

## 决策原则

- 不以功能数量衡量版本完成度，以默认安全、安装成功率、核心闭环和可维护性衡量。
- 不把模型能力当成权限控制、安全控制或一致性保证。
- 不接受“失败后打印 warning 但流程继续”的发布门禁。
- 不接受默认账号、固定密码、弱认证、隐式超级管理员或无签名远程执行。
- 所有核心功能必须具备明确状态机、错误边界、可观测性和可测试性。
- `develop` 作为后续默认开发分支；`master` 仅接收通过发布门禁的版本。

## 开源版本定义

首个可开源版本不是“功能最多”的版本，而是满足以下条件的最小完整版本：

- CLI 是第一阶段唯一正式入口；WebUI 与 Desktop 不阻塞仓库公开。
- Agent 基础循环、工具调用和会话持久化可用。
- 安装、运行和卸载不读写 Hermes 或用户 OpenCode 的数据目录。
- 安装、升级、卸载和回滚可验证。
- 第一阶段 Release 产物具备 SHA-256、版本 Manifest 和可追溯 Commit。
- Electron Preview 在没有 Apple Developer 账号期间允许无签名发布，但 Manifest、CI 和 Release Notes 必须明确 `signed=false`、`notarized=false`、Gatekeeper 人工批准要求；不得标记 Stable。
- 文档与代码一致，第三方许可证清晰。
- CI 对失败严格阻断。
