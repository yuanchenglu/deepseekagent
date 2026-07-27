# DeepSeekAgent 开源准备文档集

> 分支：`develop`
> 状态：产品与工程基线
> 目标：以“能够安全、可验证、可维护地开源”为唯一发布标准。

## 文档目录

1. [01-CODE-REVIEW.md](./01-CODE-REVIEW.md) — 当前代码审查结论、风险等级与证据。
2. [02-PRODUCT-ARCHITECTURE.md](./02-PRODUCT-ARCHITECTURE.md) — 产品定位、用户、能力边界与产品分层。
3. [03-TECHNICAL-ARCHITECTURE.md](./03-TECHNICAL-ARCHITECTURE.md) — 运行时、Harness、工具、桌面端、WebUI、任务系统与安全架构。
4. [04-PRD.md](./04-PRD.md) — 完整产品需求文档与开源版本验收标准。
5. [05-TEST-PLAN-AND-CASES.md](./05-TEST-PLAN-AND-CASES.md) — 测试策略、测试矩阵、完整核心测试用例。
6. [06-FUNCTIONAL-TEST-REPORT.md](./06-FUNCTIONAL-TEST-REPORT.md) — 当前功能验证报告、已验证结论和未执行项。
7. [07-OPEN-SOURCE-ITERATION-PLAN.md](./07-OPEN-SOURCE-ITERATION-PLAN.md) — 以最少新增功能完成开源的迭代路线。

## 决策原则

- 不以功能数量衡量版本完成度，以默认安全、安装成功率、核心闭环和可维护性衡量。
- 不把模型能力当成权限控制、安全控制或一致性保证。
- 不接受“失败后打印 warning 但流程继续”的发布门禁。
- 不接受默认账号、固定密码、弱认证、隐式超级管理员或无签名远程执行。
- 所有核心功能必须具备明确状态机、错误边界、可观测性和可测试性。
- `develop` 作为后续默认开发分支；`master` 仅接收通过发布门禁的版本。

## 开源版本定义

首个可开源版本不是“功能最多”的版本，而是满足以下条件的最小完整版本：

- CLI 与桌面端至少有一种稳定主入口。
- Agent 基础循环、工具调用、会话持久化和 Code Mode 核心闭环可用。
- 默认仅本地访问，认证、凭据和终端功能安全。
- 安装、升级、卸载和回滚可验证。
- 所有 Release 产物具备校验、签名、SBOM 和来源证明。
- 文档与代码一致，第三方许可证清晰。
- CI 对失败严格阻断。
