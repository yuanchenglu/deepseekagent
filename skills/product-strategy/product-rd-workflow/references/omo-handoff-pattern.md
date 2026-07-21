# OMO 交接手顺模式

> 当需要把代码任务交给 OMO/OpenCode 执行时，按照本模式编写手顺并启动。

## 手顺文档结构

手顺文档写入 `.hermes/plans/` 目录，包含以下章节：

### 1. 背景上下文 & 环境绑定
- 项目位置（绝对路径）
- 当前状态（已做了什么、跑通了什么）
- 相关凭证/配置信息
- ⚠️ **架构上下文 / 环境绑定** — 明确这个工作属于**哪个项目/环境**，避免 OMO 绑错对象。
  - 示例：`deepcode 是一个独立项目，gateway 应该绑定 deepcode 自身的 CLI，不是这台机器上全局的 ~/.opencode/bin/opencode`
  - 示例：`这个是 deepseekagent 的配置，不是 ucolorclaw 的`
  - 如果不写清楚，OMO 可能会用全局的、上一项目的、或默认的工具/配置来执行当前任务

### 2. 核心阻塞或待解决问题
- 一句话描述问题
- 详细现象（错误信息、日志片段）
- 已知的诊断信息

### 3. 期望结果（验收标准）
- 可验证的验收项，每项用具体命令测量
- 示例：
  ```
  curl http://localhost:3099/health → 200
  bun run typecheck → 0 errors
  ```

### 4. 诊断线索
- 可用的诊断命令
- 已知的错误原因或方向
- 备选方案（如果主路径走不通）

### 5. 约束条件
- 不改哪些文件/目录
- 不引入什么依赖
- 不改变什么架构

## 启动指令

手顺文档写好之后，用一行指令启动 OMO。

### 推荐方式：`--command`（新任务）

对于**首次启动**（无前 session 可继续），使用 `--command` 明确指定 prompt：

```
opencode run --command "详细任务描述" -f .hermes/plans/手顺.md --model opencode-go/deepseek-v4-flash --variant max
```

`--command` 参数明确告诉 CLI 哪个是 prompt，避免与文件路径参数混淆。`-f` 附加手顺文档作为上下文。

### 不推荐：`-c` + 长 prompt（仅限有前 session 时）

```
# ❌ 无前 session 时用 -c + 长 prompt → 报 "File not found: <prompt text>"
opencode run -c "详细任务描述" --model ...

# ✅ 有前 session 才用 -c（continue）
opencode run -c "继续完成剩下步骤" --model ...
```

**为什么 `-c` + 长 prompt 会失败**：`-c`（continue last session）逻辑会尝试用所有 positional args 定位上一个 session。当 prompt 文本含空格时，CLI 将其解析为多个 positional arg，第一个被当作文件路径。而新的 task 根本没有前 session 可 continue，导致解析混乱。

**规则**：
- **新任务/First run** → `--command "prompt" -f 手顺.md`（不用 `-c`）
- **继续已有 session** → `-c "简要指令"`（不 `-f`，sessions 已有上下文）
- 指令里不要重复手顺文档的全部内容。简要说明目标即可。

## 多轮 OMO 调试模式

当 OMO 第一次执行失败时，不要自己动手修。遵循**诊断 → 更新手顺 → 再交 OMO** 的三步循环：

```
第1轮：OMO 执行 → 失败（exit code != 0）
  ↓
我：分析错误输出 → 找到根因
  ↓
我：更新 .hermes/plans/ 手顺文档（加入诊断结论和新方案）
  ↓
我：用一行指令重新启动 OMO
  ↓
第2轮：OMO 执行 → 成功 / 又失败（循环继续）
```

**关键原则**：
- 即使知道怎么修，也不自己动手 — 交给 OMO 执行
- 每轮都更新手顺文档而不是重复在指令里写
- 保持 OMO 的执行视角：给足上下文，让它能独立判断
- 如果连续 3 轮 OMO 都失败在同一问题上，说明手顺缺关键信息 — 重新诊断再交

## 环境隔离诊断技巧

当 `opencode web` 在项目目录启动失败时，从临时目录启动来隔离问题：

```
cd /tmp && opencode web --port 4098 --pure
```

对比两种模式：
- `/tmp` 成功 → 问题在项目目录（`.opencode/` 配置不对、git 状态异常等）
- `/tmp` 也失败 → 问题在全局配置或 opencode 二进制本身

**已知的目录级故障原因**：
- `.opencode/opencode.jsonc` 中 `"plugin"` 数组格式不对（必须用字符串，不支持 `{package, options}` 对象格式）
- 插件引用路径不存在或 typecheck 不通过
- 项目缺少必要的初始化数据（workspace、database schema 等）

## 配置格式注意事项

OpenCode 的 `opencode.jsonc` 中 `"plugin"` 字段：
- 字段名是 `"plugin"`（单数），不是 `"plugins"`（复数）
- 值必须是字符串数组，不支持对象格式
  ```json
  // ✅ 正确
  "plugin": ["oh-my-openagent@latest", "./packages/my-plugin"]
  
  // ❌ 不支持
  "plugin": [{"package": "./packages/my-plugin", "options": {...}}]
  ```
- 插件配置通过环境变量传递（插件内部读取 `process.env`）

## 单 session 原则

**不要为 OMO 的每轮迭代启动新的后台进程（terminal background）。** 用户明确反感"开新 session"。正确做法：

```
❌ 错误：每轮 OMO 跑一次 opencode run，开一个新 background 进程
✅ 正确：一轮 OMO 的完整 prompt 包含所有要做的事，等它完成后一次性验收
```

如果 OMO 执行过程中需要调整方向：
- 让当前 OMO session 自然完成（不要中途 kill）
- 分析它的输出后，用手顺文档承接下一轮
- 新的一轮 OMO 仍然是同一个 terminal 命令（新 `opencode run`），但手顺文档是增量迭代的

### 背景 Session 的管理边界

作为**监工**（不是研发），我的职责边界：

| 阶段 | 我做的事 | 我不做的事 |
|------|---------|-----------|
| 执行前 | 写手顺文档、确认验收标准 | 自己写代码 |
| 执行中 | 定期 poll 进程、看日志 | 自己动手改代码 |
| 执行后 | 运行验收命令、汇报结果 | 信任 OMO 的自检报告 |
| 失败时 | 分析错误、更新手顺、再交 OMO | 自己修了再交 |

**禁止写代码** — 即使知道怎么修，即使只是改一行。手顺缺信息就更新手顺再交。

## 先查现有实现，不重复造轮子

当需要对接新平台/API 时，**先查已有实现**再决定是否有现成的参考：

```
查找顺序：
1. 检查 Hermes Agent 中同平台的实现（Python，在 ~/Code/deepseekagent/plugins/ 或 ~/Code/deepseekagent/gateway/）
2. 检查同一项目依赖中是否有官方 SDK（如 @larksuiteoapi/node-sdk）
3. 查看项目配置中已有的 MCP / Plugin 配置（如 opencode.json 中的 lark MCP）
4. 最后才考虑从头实现
```

示例：对接飞书长连接时，Hermes Agent 的 `gateway/platforms/feishu.py` 使用了 `lark_oapi.ws.Client`（飞书官方 Python SDK 的内置 WebSocket 客户端），TypeScript 版对应的官方包是 `@larksuiteoapi/node-sdk`。

## 背景进程生命周期管理

当 OMO 需要启动一个长时间运行的服务（HTTP Server、Gateway、后台守护进程等）：

### 启动阶段
1. 在手顺中明确：进程用 `background=true` 启动，**必须设置 `notify_on_complete=true`**（对 bounded 任务）或定期 poll（对 server）
2. 进程启动后立即验证：`curl` 健康检查、`lsof -i` 确认监听、`ps aux | grep` 确认 PID
3. 设置环境变量要在同一行命令中（`export VAR=val && command`），否则 background 进程读不到

### 保持运行
- 对于 Effect-based 项目（如 deepcode），用 `Effect.runFork(program.pipe(Effect.scoped))` + `Effect.never` 模式保持 Scope 不关闭
  - 常见错误：`Effect.runPromise(Effect.scoped(...))` 会在 `startGateway` 返回后关闭 Scope，导致 `forkScoped` 的后台 Fiber 被中断
- 如果进程意外退出，检查日志的第一个错误（不要只看最后的 exit code）

### 重启动
- 如果进程退出，检查环境变量是否传入、端口是否被占用、工作目录是否正确
- 用 `process(action='log', session_id='...')` 查看完整退出前输出
- 修复问题后重新启动

| 阶段 | 我做的事 |
|------|---------|
| OMO 运行时 | 不中断，定期 poll 进程 |
| OMO 完成后 | 检查 exit code |
| 验收 | 运行验收命令验证结果（不能只信 OMO 的报告） |
| 反馈 | 向用户汇报通过/失败 + 原因 |

## 常见陷阱

- **手顺太简略**：缺少诊断线索和验收标准 → OMO 走弯路
- **手顺太详细**：在指令里重复手顺全文 → 浪费 token
- **没有设置 notify_on_complete**：不知道 OMO 跑完了
- **验收不充分**：OMO 说完成了就信了 → 必须自己验证
- **第一轮 OMO 失败就放弃** → 可能是 OMO 遇到配置错误或漏了信息，更新手顺再试
- **OMO 当一次性工具** → OMO 应该多轮使用，每轮迭代
