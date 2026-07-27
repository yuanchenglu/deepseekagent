# 第三阶段：DeepAgent + DeepCode 双模式 Electron

> 状态：产品与架构基线已锁定，实施依赖第二阶段 Runtime  
> 应用名：DeepAgent  
> Bundle ID：`org.starseas.deepagent`  
> 首发制品：签名并经 Apple 公证的 Apple Silicon DMG  
> 阶段产物：Electron Preview，外测通过后升 Stable

## 1. 产品结果

用户启动 DeepAgent 后默认进入 DeepAgent 模式；左上角可以无重启切换到 DeepCode。两个模式共享当前项目和公共设置，但对话、任务、布局与运行状态相互隔离。模式切换不终止后台任务，一个 Runtime 崩溃也不关闭客户端或另一个 Runtime。

## 2. 信息架构

公共层：项目选择、模型/提供商、Keychain、主题、语言、更新渠道、通知、日志、诊断、权限、工作区和后台任务状态。

DeepAgent：对话、会话、Agent 任务、工具/Skills/授权、文件与工作区上下文、恢复与历史。

DeepCode：编码任务、仓库/文件上下文、变更查看、终端结果、Diff 审核/接受/回退、独立任务历史。

左上角模式切换器固定存在；左侧导航随模式变化；公共设置入口固定。每个模式分别保存最后页面、选中项目和任务状态。

## 3. 进程与安全边界

```text
Electron Main
├── Window / Update / Keychain / Permission / Process Supervisor
├── DeepAgent Runtime  ── 独立 IPC、状态目录、环境白名单
└── DeepCode Runtime   ── 独立 IPC、状态目录、内置 OpenCode
        └── Renderer 只通过类型化 IPC 使用能力，不持有根 Secret
```

- Main Process 只负责安全边界和系统能力，不实现 Agent/DeepCode 业务逻辑。
- 两个 Runtime 是独立子进程，使用不同 IPC 命名空间和状态目录。
- DeepCode 只使用项目内置 OpenCode，不解析 PATH 中的全局版本。
- Keychain 凭据按提供商和 Runtime 白名单注入；Renderer、日志和无关子进程不可见。
- 同一工作区同一时间只允许一个写任务；只读任务可并行。
- Runtime 监督器独立重启故障 Runtime，并把状态传给全局状态栏。

## 4. 工作包与执行顺序

| 编号 | 工作包 | 实施要求 | 完成证据 |
|---|---|---|---|
| P3-01 | 统一领域协议 | 从第二阶段 Runtime 固化类型化命令、事件、状态和错误协议 | 契约测试 |
| P3-02 | Main 安全壳 | 窗口、进程监督、IPC、权限、更新、Keychain | Main 单元/集成测试 |
| P3-03 | 双 Runtime | 独立生命周期、状态目录、环境白名单、崩溃恢复 | 故障注入测试 |
| P3-04 | 模式与路由 | 默认 DeepAgent、左上角切换、模式级导航和持久状态 | UI E2E |
| P3-05 | 后台任务 | 切换后持续运行、全局可见、通知和恢复 | 长任务 E2E |
| P3-06 | 工作区锁 | 单写互斥、只读并行、崩溃后的租约回收 | 并发/故障测试 |
| P3-07 | DeepAgent UI | 对话、任务、工具、Skills、授权、历史 | 用户流程 E2E |
| P3-08 | DeepCode UI | 任务、文件、终端、Diff、接受/回退、历史 | 仓库夹具 E2E |
| P3-09 | 数据迁移 | 迁移第二阶段配置/会话/项目；旧 Desktop 一次性读取；版本备份与回滚 | 迁移矩阵 |
| P3-10 | DMG 发布 | Apple Silicon 构建、签名、公证、自动更新和失败回滚 | 干净机验证 |
| P3-11 | Preview 门禁 | 安全、迁移、共存、P0/P1 | 检查表全绿 |

依赖顺序：P3-01 → P3-02/03 → P3-04/05/06 → P3-07/08 → P3-09/10/11。不得在 Renderer 先复制 Runtime 业务逻辑来绕过协议设计。

## 5. 数据与迁移

- Electron 与 CLI/WebUI 共用 `~/.deepagent` 产品根，但每个 Runtime 和界面模式使用独立子目录。
- 从第二阶段升级时迁移配置、会话和项目记录；旧 Desktop 设置只读一次。
- 迁移前创建带模式和版本号的备份；迁移事务失败则恢复备份，CLI/WebUI 仍可启动。
- 新客户端稳定后停止分发旧 Electron；浏览器 WebUI 保留为恢复与备用入口。
- 卸载只删除 Manifest 登记的应用文件；用户数据遵循保留/完全卸载的明确选择。

## 6. 验收矩阵

- 默认进入 DeepAgent，左上角无重启切换 DeepCode；
- 两个模式分别恢复页面与任务，项目共享但会话不串用；
- 切换后后台任务继续；同工作区写任务互斥；
- 任一 Runtime 崩溃不影响另一个 Runtime 或 Electron 窗口；
- Keychain 凭据不进入 Renderer、日志或无关子进程环境；
- 安装、自动更新、失败回滚、卸载；
- 第二阶段 CLI/WebUI/旧 Electron 数据迁移；
- Hermes 与用户 OpenCode 继续运行；
- 签名、公证、Gatekeeper 和干净机器安装通过。

## 7. Go/No-Go 门禁

上述场景全部通过且 P0/P1 为零后发布 Electron Preview。Preview 必须经过真实用户测试，且发布周期内无阻断问题，才可升为 Stable。未公证、凭据可到达 Renderer、两个模式复制业务逻辑、或工作区写任务无互斥，任一情况都必须 No-Go。
