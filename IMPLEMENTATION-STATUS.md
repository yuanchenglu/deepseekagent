# Deep Agent MVP 实施状态（实时更新）

**最后更新**：2026-07-01 04:05

---

## 已完成文档（5/5）

- [x] MVP-PRD-Overview.md (v0.2) — 总览
- [x] 01-Upstream-Sync-and-Branding.md — 上游同步 + 品牌统一方案
- [x] 02-Desktop-Client.md — 桌面客户端 / WebUI 工作台
- [x] 03-Code-Mode-Implementation.md — Code 模式核心技术方案
- [x] 04-Engineering-and-Harness.md — 工程质量 + Harness 层优化

---

## 开发进度总表

| 方向 | 状态 | 关键产出 |
|------|------|----------|
| **品牌统一** | ✅ 高优先级文件已替换 | `scripts/brand-replace.py`（支持 dry-run），19 个文件，360+ 行变更 |
| **Code 模式** | ✅ 最小可演示（7 项测试通过） | `deepagent_code_mode/` 包，`embedded/` 隔离环境，skill 注册 |
| **WebUI 工作台** | ✅ 源码集成 + 正在运行 | `webui/` 目录，`setup-webui.sh`，`start-webui.sh`，`deepagent webui` 子命令 |
| **工程质量 + Harness** | ⏳ 待系统落地 | PRD 已就绪 |

---

## 详细完成清单

### 1. 品牌与上游同步
- [x] 创建 `scripts/brand-replace.py`（支持 dry-run）
- [x] 执行保守替换（高优先级文件：docs、AGENTS.md、CONTRIBUTING.md、landingpage、入口、README、hermes-already-has-routines）
- [x] `hermes_constants.py` 新增 `get_deepagent_home()`，保留 `get_hermes_home()` 兼容别名
- [ ] 编写 `sync-hermes-upstream.sh`

### 2. Code 模式（核心差异化，MVP 支柱）
- [x] 创建 `embedded/` 目录（隔离研发小组环境）
- [x] 创建 `scripts/setup-embedded-opencode.sh`
- [x] 创建 `embedded/run_task.sh`（接收 JSON 任务、写入 workspace、输出结果）
- [x] 创建 `embedded/start.sh`（start/run-task/list 等子命令）
- [x] 创建 `embedded/config/opencode-config.yaml`
- [x] 创建 `deepagent_code_mode/` 包
  - [x] `dispatcher.py` — dispatch() 真实 subprocess 调用 + 非阻塞返回
  - [x] `collect_result()` / `check_status()` — 双向通信
  - [x] `handler.py` — 函数式高层接口
  - [x] `session.py` — 隔离会话管理
  - [x] `integration_example.py` — 三种集成方式示例
- [x] 注册 Code Mode skill 到 `~/.hermes/skills/code-mode/`
- [x] 创建 `tests/test_code_mode.py` — 7 个测试用例全部通过
- [ ] 与 run_agent 主循环深度集成（通过 skill 已可路由，后续可强化）

### 3. WebUI 默认工作台
- [x] 从 `https://github.com/EKKOLearnAI/hermes-web-ui.git` clone 到 `webui/`
- [x] 最小品牌替换：标题、登录页 alt、中英文文案
- [x] 创建 `webui/DEEPAGENT-README.md` 说明文档
- [x] 移除 webui/.git（统一仓库）
- [x] 创建 `scripts/setup-webui.sh`（检测 node → npm install → build → 写配置）
- [x] 创建 `scripts/start-webui.sh`（start/stop/status/restart）
- [x] 集成到 `deepagent` 入口（`deepagent webui start/status/stop`）
- [x] 集成到 `setup-deepagent.sh`（安装流程末尾自动安装）
- [x] 数据目录 `~/.deepagent-webui/`（独立于旧 `~/.hermes-web-ui/`）
- [x] **正在运行**：localhost:8648，HTTP 200，品牌可见

### 4. 工程质量与 Harness 优化
- [x] PRD 文档已就绪（04-Engineering-and-Harness.md）
- [x] **场景路由（Scene Router）— 已完成** ✅
  - [x] `deepagent_harness/scene_router.py` — 分类 + 路由 + 自动分发
  - [x] `deepagent_harness/__init__.py`
  - [x] `deepagent_harness/README.md`
  - [x] skill 注册到 `~/.hermes/skills/harness-scene-router/`
  - [x] 10 项测试全部通过
  - [x] 分类准确率 7/7 关键场景正确
- [ ] CI 流水线（GitHub Actions）
- [ ] Harness 14 篇文章落地

---

## 全部测试汇总

| 套件 | 用例数 | 通过率 |
|------|--------|--------|
| `tests/test_code_mode.py` | 7 | ✅ 100% |
| `tests/test_harness_scene_router.py` | 10 | ✅ 100% |
| **总计** | **17** | **✅ 100%** |

---

## 当前 Git 状态

| 指标 | 数值 |
|------|------|
| 跟踪中修改文件 | 19 个 |
| 新增未跟踪文件（除去 webui） | ~14 个 |
| 新增代码 | ~360 插入，~382 删除 |
| 运行中的服务 | WebUI on :8648 |

---

## 下一步（按优先级）

1. **Harness 场景路由** — 研发/非研发任务自动分类，路由到 Code Mode 或直接处理
2. **sync-hermes-upstream.sh** — 每周上游同步脚本
3. **Electron 打包**（可选） — 桌面应用
4. **补充测试** — 补齐 WebUI 集成和品牌替换的自动化验证

---

**备注**：本文档会随开发进度持续更新。当前状态对应三方子代理并行交付后的验收结果。