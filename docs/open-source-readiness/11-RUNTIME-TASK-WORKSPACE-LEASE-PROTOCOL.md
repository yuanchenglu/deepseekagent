# Runtime Task / Workspace Lease 协议

> 状态：协议与状态机实现候选  
> 适用范围：Electron Main、DeepAgent Runtime、DeepCode Runtime  
> 当前边界：本文件固化类型、状态机、幂等和故障语义；真实 task/PID/进程树接入属于下一独立工作单元。

## 1. 目标

同一 Workspace 允许多个只读任务并行，但任何写任务必须与其他读写任务互斥。该约束不能依赖 Renderer 自愿调用，也不能由 UI 根据页面或按钮猜测任务访问级别。

协议以 Electron Main 为唯一权威租约协调器：

- DeepAgent Runtime 与 DeepCode Runtime 必须显式声明任务身份和 `read` / `write` 访问级别。
- Runtime 只能通过固定 Runtime 身份适配器发送事件，不能冒充另一 Runtime。
- Renderer 不直接改变权威租约状态。
- 底层 `WorkspaceLockManager` 只负责多读单写资源互斥；任务状态、租约 TTL、幂等和故障恢复由 `RuntimeTaskLeaseCoordinator` 负责。

## 2. 非目标

本工作单元不实施：

- 真实 Runtime 子进程消息通道。
- task 与 PID/进程树的实际绑定。
- 心跳定时器和 OS 进程存活探测。
- Main 重启后的磁盘持久化与进程重建。
- 双 Runtime 真实任务 E2E。

这些必须在本协议合入后按计划顺序继续，不得在本 PR 中并行扩张。

## 3. 身份模型

每个租约身份由以下字段构成：

| 字段 | 约束 |
|---|---|
| `runtime` | 只能是 `deepagent` 或 `deepcode` |
| `workspace` | 非空路径，进入协调器时规范化为绝对路径 |
| `taskId` | Runtime 内唯一且不可复用的稳定任务标识 |
| `access` | 必须显式为 `read` 或 `write` |
| `process.pid` | 可选，正安全整数；当前仅进入协议快照，不做真实存活判断 |
| `process.treeId` | 可选，未来用于进程树归属和恢复 |

唯一任务键为：

```text
(runtime, taskId)
```

同一 `taskId` 可以分别存在于 DeepAgent 和 DeepCode，但不能在同一 Runtime 中重新绑定到不同 Workspace、访问级别或进程身份。

## 4. 命令与结果

所有命令必须包含：

- `eventId`：事件幂等键。
- `type`：事件类型。
- `observedAt`：Main 接受的单调时间证据，使用毫秒数。

协议命令：

| 命令 | 作用 |
|---|---|
| `acquire` | 创建 pending 租约并尝试获取 Workspace 读写锁 |
| `heartbeat` | 延长 active 租约 TTL；不得复活过期或 orphaned 租约 |
| `release` | 正常结束任务并释放租约 |
| `cancel` | 取消任务并释放租约 |
| `timeout` | TTL 到期后把 active 租约转为 expired 并释放 |
| `process-exit` | 记录真实进程退出；对 orphaned 租约可作为恢复释放证据 |
| `runtime-crash` | 将该 Runtime 的非终态租约标记为 orphaned |
| `recover` | 明确确认 orphaned 任务已被安全回收并释放锁 |

`acquire` 的结果通过 `code=acquired` 或 `code=conflict` 表达 `acquired` / `denied`。其他失败使用稳定错误码，不依赖自由文本解析。

## 5. 状态机

状态集合：

```text
pending
active
releasing
released
expired
orphaned
recovered
```

允许的核心转换：

```text
acquire accepted:   ∅ → pending → active
normal release:     active → releasing → released
cancel:             active → releasing → released(cancelled)
timeout:            active → expired
process exit:       active → releasing → released(process-exit)
runtime crash:      active|pending|releasing → orphaned
explicit recovery:  orphaned → recovered
exit after crash:   orphaned → recovered(process-exit)
```

终态：

- `released`
- `expired`
- `recovered`

`pending` 和 `releasing` 当前是同步状态机中的可审计瞬时状态；真实 Runtime 接入后可以跨异步边界存在。

## 6. 并发不变量

对同一规范化 Workspace，始终满足：

1. `read + read` 可以并行。
2. `read + write` 双向互斥。
3. `write + write` 互斥。
4. `access` 在租约生命周期内不可升级或降级；需要不同访问级别时必须创建新 taskId。
5. 同一 Runtime/taskId 只能对应一个 leaseId 和一个不可变身份。
6. 只有 Main 协调器可以驱动权威状态转换。
7. 返回给调用方的快照是副本，外部修改不能改变内部状态。

## 7. 幂等与重放

- 相同 `eventId` 和完全相同的命令载荷返回第一次结果，不重复改变状态。
- 相同 `eventId` 携带不同载荷返回 `replay-conflict`。
- 对同一 active 身份重复 `acquire` 返回 `already-acquired` 和原 leaseId。
- 重复 `release` / `cancel` / `timeout` / `recover` 对已到达相应终态的租约返回稳定终态结果，不重复释放底层锁。
- 同一 Runtime/taskId 尝试修改 Workspace、访问级别或进程身份返回 `owner-mismatch`。

## 8. TTL 与心跳

默认 TTL 为 30 秒，允许范围为 1 秒至 5 分钟；测试和后续监督器可以显式覆盖。

- active 租约接受不早于上次心跳的 `heartbeat`。
- 心跳把 `expiresAt` 更新为 `observedAt + ttlMs`。
- 在 `observedAt >= expiresAt` 后到达的心跳不会复活任务，而是先把租约转为 `expired`，再返回 `expired-lease`。
- 提前到达的 `timeout` 失败关闭为 `invalid-state`。

## 9. Runtime 崩溃与恢复

Runtime 崩溃采用失败关闭策略：

1. `runtime-crash` 将该 Runtime 的 active/pending/releasing 租约转为 `orphaned`。
2. orphaned 租约继续持有底层 Workspace 锁。
3. 其他 Runtime 对冲突 Workspace 的 acquire 继续被拒绝。
4. orphaned 租约拒绝 heartbeat、普通 release 和 cancel，防止不可信旧连接改变状态。
5. 只有以下证据允许释放：
   - Main 发出的显式 `recover`；
   - 已确认对应进程树退出的 `process-exit`。
6. 恢复后状态为 `recovered`，底层锁释放。

该策略优先避免双写。未来 PID 接入必须提供自动恢复证据，不能通过缩短 TTL 绕过 orphaned 锁。

## 10. 错误语义

| 错误码 | 含义 |
|---|---|
| `invalid-request` | 字段、Runtime、访问级别、PID、时间或 TTL 不合法 |
| `conflict` | Workspace 当前读写状态拒绝 acquire |
| `unknown-task` | Main 中不存在对应 Runtime/taskId |
| `expired-lease` | 调用试图操作已过期租约或迟到心跳 |
| `owner-mismatch` | leaseId 或不可变任务身份不匹配 |
| `invalid-state` | 当前状态不允许该转换 |
| `replay-conflict` | eventId 已用于不同载荷 |
| `recovery-failed` | 非 orphaned 租约收到 recover |

所有错误均失败关闭，不隐式创建、释放或复活租约。

## 11. Runtime 适配边界

`RuntimeTaskLeaseAdapter` 在构造时固定 `deepagent` 或 `deepcode`：

- 调用方提交的 acquire 身份不包含 runtime。
- 其他命令也不接受调用方自填 runtime。
- Adapter 在进入 Main 协调器前强制写入自身 Runtime 身份。
- 即使不可信调用方通过动态对象夹带 runtime，适配器也会覆盖它。

下一工作单元应分别把 DeepAgent Runtime 和 DeepCode Runtime 的真实任务事件连接到各自 Adapter，不得让 Runtime 直接持有或修改 `WorkspaceLockManager`。

## 12. 契约测试

`runtime-task-lease.test.ts` 至少覆盖：

- 非法 Runtime、访问级别、PID 和 TTL 失败关闭。
- reader-reader、reader-writer、writer-writer。
- acquire 幂等、eventId 重放与冲突重放。
- 心跳续租、迟到心跳过期和不可复活。
- 未知任务、leaseId 所有者不匹配和提前 timeout。
- cancel/release 终态幂等。
- Runtime 崩溃后 orphaned 锁继续阻断其他任务。
- 显式 recover 和 process-exit 恢复释放。
- DeepAgent/DeepCode Adapter 身份隔离。
- 状态转换历史和快照不可变性。

## 13. 下一工作单元入口

本协议合入后，下一任务只能是：

1. Main 实例化单一 `RuntimeTaskLeaseCoordinator`。
2. DeepAgent/DeepCode Runtime 启动任务前通过固定 Adapter acquire。
3. 任务进程创建后绑定 PID/进程树。
4. Main 监督 heartbeat、timeout、process-exit 和 runtime-crash。
5. Main 重启时从持久状态和存活进程重建或回收租约。

在以上真实接入完成前，不得把本协议单元测试描述为 Runtime Lease 闭环或双 Runtime E2E 已完成。
