# 03 - Code 模式实现（Code Mode Implementation）

**版本**：v0.1  
**日期**：2026-07-01  
**状态**：草案  
**关联 Overview**：MVP-PRD-Overview.md

---

## 1. 核心问题

Deep Agent 的最大差异化在于 **“CEO + 内置研发小组”** 模式。

用户（董事长）通过 Deep Agent 下达研发指令，Deep Agent 作为 CEO 指挥**内置的、深度配置好的 OpenCode 团队**完成任务。

**关键约束**（铁律）：
- 用户**不感知** OpenCode 的存在。
- 内置 OpenCode 与用户本地任何 OpenCode **完全隔离**（配置、模型、技能、MCP、状态）。
- 不提供切换到用户本地 OpenCode 的选项。

---

## 2. 目标

1. 在 Deep Agent 项目内**嵌入**一套完整的 OpenCode + OpenSpec + Superpowers + 技能体系。
2. 提供隔离的执行环境和配置。
3. 实现从 Deep Agent 对话到内置 OpenCode 任务的分发与结果回传。
4. 支持多任务并行（子代理机制）。

---

## 3. 架构设计

### 3.1 推荐目录结构（项目内嵌入）

```
DeepAgent/
├── embedded/                    # 内置研发小组（不暴露给最终用户）
│   ├── opencode/                # clone 或 submodule 一个配置好的 OpenCode
│   ├── open-spec/               # OpenSpec 配置
│   ├── superpowers/             # Superpowers 插件
│   └── skills/                  # 预装的 DeepAgent 专用技能
├── deepagent/
│   ├── code_mode/               # Code 模式核心逻辑
│   │   ├── dispatcher.py        # 指令翻译 + 任务分发
│   │   ├── session_manager.py   # 隔离会话管理
│   │   └── result_collector.py  # 结果收集与总结
│   └── ...
├── docs/specs/03-Code-Mode-Implementation.md
└── ...
```

### 3.2 隔离机制

- **配置隔离**：内置 OpenCode 使用独立的 `~/.deepagent-embedded-opencode/` 或项目内 `embedded/config/`
- **模型隔离**：强制使用特定模型（DeepSeek V4 Flash/Pro），独立 API Key 配置。
- **状态隔离**：独立 SQLite / 向量存储。
- **工具隔离**：内置版本只暴露对 Deep Agent 友好的工具集。
- **进程隔离**：通过子进程 / Docker / worktree 运行，避免污染主进程。

### 3.3 通信机制

Deep Agent → Code Mode Dispatcher：
- 自然语言指令 → 结构化任务（使用 prompt engineering 或小模型分类）。
- 任务通过 RPC / 文件 / API 交给 embedded OpenCode。
- OpenCode 执行过程通过 WebSocket / log tail 实时回传。
- 完成后由 Deep Agent 做最终总结与用户汇报。

---

## 4. 实施步骤（MVP）

1. **阶段 3.1**：创建 `embedded/` 目录，添加 OpenCode 作为 git submodule 或 script 拉取。
2. **阶段 3.2**：实现最小 dispatcher（将用户指令包装成 OpenCode 任务）。
3. **阶段 3.3**：实现隔离启动脚本（`embedded/start.sh`）。
4. **阶段 3.4**：结果回传 + 总结循环。
5. **阶段 3.5**：与桌面客户端 Code 模式 UI 对接。

---

## 5. 技术选型建议

- **嵌入方式**：git submodule（推荐，便于独立更新）或 `scripts/setup-embedded-opencode.sh`
- **启动方式**：`opencode run --config embedded/opencode-config.yaml --workdir embedded/workspace`
- **任务协议**：使用 OpenCode 的 ACP 或自定义 task JSON。
- **实时反馈**：结合现有 terminal_tool + process_registry 实现 log streaming。

---

## 6. 风险与缓解

| 风险                     | 影响 | 缓解措施                     |
|--------------------------|------|------------------------------|
| 嵌入体积过大             | 高   | 使用 worktree / 精简 clone   |
| 配置泄露 / 污染          | 高   | 严格路径隔离 + 环境变量控制  |
| 性能开销                 | 中   | 异步 + 后台运行              |
| OpenCode 版本漂移        | 中   | 锁定特定 commit + 同步脚本   |

---

## 7. 验收标准（MVP）

- [ ] 用户可在 Deep Agent 中说“帮我实现 XXX 功能”，系统自动启动内置 OpenCode 执行。
- [ ] 执行过程对用户透明（只看到高级总结 + 必要关键步骤）。
- [ ] 内置 OpenCode 的任何修改不影响用户本机环境。
- [ ] 支持中断 + 结果回传。

---

## 8. 后续行动

1. 编写 `scripts/setup-embedded-opencode.sh`
2. 实现 `deepagent/code_mode/dispatcher.py` 最小版本
3. 在 `run_agent.py` 或 skill 中增加 Code Mode 路由
4. 配合 02 文档完成前端对接

**备注**：这是 Deep Agent 技术护城河的核心实现，必须优先保证隔离性和用户无感知体验。