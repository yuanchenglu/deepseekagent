# DeepSeekAgent 当前功能测试报告

## 1. 报告结论

当前版本功能验证结论：**不通过，不具备开源发布条件。**

本报告区分三种证据：

- `STATIC-CONFIRMED`：通过源码和调用链可确认。
- `TEST-DESIGN-DEFECT`：现有测试代码无法证明功能正确。
- `NOT-EXECUTED`：需要本地构建、运行或多平台环境，本次未实际执行。

由于当前审查环境未能完整 clone 并运行仓库，本报告不是伪造的“全量测试通过报告”；它是基于源码、现有测试和发布流程的功能验证报告。动态测试必须在后续迭代中按测试计划执行并回填结果。

## 2. 摘要

| 模块 | 结论 | 证据等级 |
|---|---|---|
| Agent 基础架构 | 有较完整基础，但主文件耦合严重 | STATIC-CONFIRMED |
| Harness | 多模块已接入，但配置、优先级和确定性边界有缺陷 | STATIC-CONFIRMED |
| Code Mode | 仅派发闭环，任务完成闭环不成立 | STATIC-CONFIRMED |
| Desktop | 安全认证与 Mode IPC 存在阻断问题 | STATIC-CONFIRMED |
| WebUI/Auth | 默认安全边界不满足发布要求 | STATIC-CONFIRMED |
| Terminal | 高权限能力，默认策略不足 | STATIC-CONFIRMED |
| Release/Installer | 产物命名、清单、路径和校验存在协议问题 | STATIC-CONFIRMED |
| 自动化测试 | 存在测试，但部分测试放宽到无法证明正确性 | TEST-DESIGN-DEFECT |
| 多平台真实安装 | 未执行 | NOT-EXECUTED |

## 3. 已验证失败项

### FT-001 未认证保护接口

- 状态：FAIL
- 原因：认证关闭路径存在首用户注入行为；默认配置不能证明未认证请求一律返回 401。
- 严重级别：Critical。

### FT-002 Desktop 默认凭据

- 状态：FAIL
- 原因：Preload 硬编码管理员用户名和密码，并自动登录。
- 严重级别：Critical。

### FT-003 强制改密流程

- 状态：FAIL
- 原因：Preload 修改认证响应，隐藏 `requiresCredentialChange`。
- 严重级别：Critical。

### FT-004 Release 完整性校验

- 状态：FAIL
- 原因：校验失败可被 `|| true` 吞掉；摘要缺失时继续。
- 严重级别：Critical。

### FT-005 Release 产物契约

- 状态：FAIL
- 原因：构建器和安装器命名规则不一致；核心目录清单可能遗漏；Embedded 解压路径不一致。
- 严重级别：Critical。

### FT-006 Code Mode 正常完成

- 状态：FAIL
- 原因：现有流程只写入 `dispatched`，没有等待、退出码、终态回写和 Artifact 收集。
- 严重级别：High。

### FT-007 OpenCode 缺失

- 状态：FAIL
- 原因：缺失时使用 simulated result 并以成功方式退出，状态不真实。
- 严重级别：High。

### FT-008 Code Mode 超时和取消

- 状态：FAIL
- 原因：没有超时、取消和进程树回收的完整实现。
- 严重级别：High。

### FT-009 Code Mode 隔离

- 状态：FAIL
- 原因：仅设置配置目录，仍继承宿主环境、文件系统、网络和工作目录。
- 严重级别：High。

### FT-010 Desktop Mode IPC

- 状态：FAIL
- 原因：Client 预期 API、Preload 暴露 API 和 Main Process broadcast 契约不一致。
- 严重级别：High。

### FT-011 Harness 开关

- 状态：FAIL
- 原因：`configured_value or True` 导致开关永远为真。
- 严重级别：High。

### FT-012 Release Smoke Test

- 状态：FAIL
- 原因：`deepagent --version` 失败后仍输出 PASSED；构建跳过多个关键检查。
- 严重级别：High。

## 4. 现有测试设计缺陷

### Code Mode 测试

现有用例允许 `completed/dispatched/simulated` 均视为成功；结果文件不存在也可能通过。这只能证明 API 返回了结构化字典，不能证明任务执行成功。

缺失验证：

- 真实 OpenCode 执行。
- 终态和退出码。
- stdout/stderr。
- 超时、取消、崩溃恢复。
- 并发和日志隔离。
- Sandbox。
- 恶意输入。

### Harness 测试

已有模块级用例和历史通过记录，但仍缺少：

- 与真实 Agent Loop 的契约测试。
- 配置开关测试。
- 模块失败的可观测性测试。
- 真实 tokenizer 的长上下文测试。
- 用户约束优先级冲突测试。
- 高风险操作与 Policy Gate 分离测试。

### Release 测试

Smoke Test 允许关键命令失败，不能作为门禁。还缺少：

- 构建器与安装器 Manifest 契约测试。
- 干净机器安装。
- 升级和回滚。
- 多架构包内容检查。
- 签名、SBOM 和 provenance 验证。

## 5. 未执行动态测试

以下测试必须在可运行环境中执行：

1. Python 全量 pytest。
2. WebUI unit/component/E2E。
3. Electron build 与启动。
4. macOS ARM64/x64 DMG 安装。
5. Ubuntu clean-machine 安装。
6. Provider 真机调用。
7. Terminal WebSocket 安全测试。
8. Code Mode OpenCode 真执行。
9. Worker 资源限制和网络隔离。
10. 升级、回滚和故障注入。

## 6. 建议的正式测试报告格式

每次 Release Candidate 必须生成：

- commit SHA。
- Release Manifest SHA。
- OS/架构矩阵。
- 自动测试总数、通过、失败、跳过。
- 失败用例和日志链接。
- P0/P1 缺陷清单。
- Secret、SAST、依赖和 License 扫描结果。
- 安装、升级、回滚结果。
- 最终 Go/No-Go 签字。

## 7. 当前 Go/No-Go

**No-Go**。

解除条件：

- Critical 和 High 发布阻断项全部关闭。
- 完成动态测试矩阵。
- 所有 P0 E2E 通过。
- Release 校验与安装链路通过故障注入。
- 不再存在“warning 后继续并宣称成功”的门禁。
