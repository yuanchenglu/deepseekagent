# 第二阶段：WebUI 稳定 Beta

> 状态：技术准备允许开始，公开发布必须等待第一阶段 Go  
> 主入口：浏览器 WebUI  
> 旧 Electron：可选预览，仅做安全、路径和启动修复  
> 阶段产物：公开 WebUI Beta

## 1. 产品结果

Alpha 用户原地升级后，可以通过 CLI 启动、打开、检查和停止本地 WebUI；不需要固定密码，不需要手工找 Token，CLI 与 WebUI 看到同一份配置、会话、任务和 Runtime 状态。Hermes、用户 OpenCode 与 DeepAgent WebUI 可以同时运行。

```bash
deepagent webui start
deepagent webui open
deepagent webui status
deepagent webui stop
```

## 2. 冻结行为

- 默认只监听 `127.0.0.1`，不接受“开发方便”作为 `0.0.0.0` 的理由。
- `open` 生成短时、一次性 Ticket；Ticket 过期、重放或服务重启后都不可复用。
- 端口占用时寻找本地可用端口并写入 `~/.deepagent/runtime/webui/`，不结束占用端口的其他进程。
- 浏览器持久存储、URL、日志和错误报告中不得出现根 Secret 或模型 API Key。
- LAN/公网默认关闭且不属于 Beta 承诺。

## 3. 工作包与执行顺序

| 编号 | 工作包 | 实施要求 | 完成证据 |
|---|---|---|---|
| P2-01 | 单一 Runtime | CLI/WebUI 共用 Agent Runtime、配置、会话和任务状态，不复制业务逻辑 | 架构测试 + 会话互通 E2E |
| P2-02 | CLI 生命周期 | 实现 start/open/status/stop；PID、锁、端口和日志独立命名 | CLI 集成测试 |
| P2-03 | 本地认证 | 一次性 Ticket、过期、重放防护、服务重启失效 | 安全测试 |
| P2-04 | WebUI 产品化 | 配置、会话、Agent 任务、授权、日志、错误恢复；清理用户可见 Hermes 名称 | UI E2E + 文案扫描 |
| P2-05 | 数据隔离 | 所有 WebUI 数据位于 `~/.deepagent/`；不再使用 `~/.hermes-web-ui` | 路径单测 + VM 对比 |
| P2-06 | 子进程隔离 | 使用环境变量白名单，只向目标 Runtime 注入所需凭据 | 环境快照测试 |
| P2-07 | 旧 Electron 安全修复 | 唯一应用名、`org.starseas.deepagent.legacy`、只连接 Agent Runtime | 启停/崩溃恢复测试 |
| P2-08 | Experimental Code Mode | 内置 OpenCode、独立目录、真实任务状态机、不调用全局 `opencode` | 状态机 + 共存 E2E |
| P2-09 | Alpha 数据升级 | 配置、会话原地升级；失败回滚 | 迁移夹具 + VM |
| P2-10 | Beta 发布门禁 | 端到端、许可证、卸载、共存、P0/P1 | 检查表全绿 |

依赖顺序：P2-01 → P2-02/03/04；P2-01 → P2-08；P2-05/06 是所有服务与子进程工作的前置安全条件。旧 Electron 不得阻塞浏览器 WebUI Beta。

## 4. Code Mode 状态契约

每个任务只能处于以下真实状态之一：`queued`、`running`、`succeeded`、`failed`、`cancelled`、`timed_out`、`interrupted`。`started` 事件不是成功终态；子进程退出码、超时、取消信号与错误摘要必须保存并展示。

内置 OpenCode 位于 `~/.deepagent/runtime/deepcode/<version>/`，配置、缓存、状态和日志均位于 DeepAgent 命名空间。测试必须在 PATH 前部放置会失败的假 `opencode`，证明系统未调用全局版本。

## 5. 验收矩阵

- CLI 四个 WebUI 命令的幂等、异常与重启行为；
- 首次登录、Ticket 过期、重放、服务重启；
- 监听地址不是 `0.0.0.0`；连续多个端口占用；
- Hermes、OpenCode、DeepAgent WebUI 同时运行；
- Agent 与 Code Mode 全部终态；
- 刷新、断线重连、会话恢复；
- 旧 Electron 启动、退出、崩溃恢复；
- Alpha 数据升级与失败回滚；
- 卸载 WebUI/旧 Electron 后 CLI、Hermes、OpenCode 正常。

## 6. Go/No-Go 门禁

WebUI 核心流程端到端全绿；无固定默认密码；无未授权 LAN 监听；三个产品可同时运行；Code Mode 不读取用户 OpenCode 配置；Secret 不进入浏览器与日志；P0/P1 为零。满足后发布 WebUI Beta；经过一个完整外部测试周期且没有发布阻断问题后，才能评估 Stable。
