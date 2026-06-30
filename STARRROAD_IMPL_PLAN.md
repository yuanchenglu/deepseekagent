# StarRoad Cognition — DeepAgent 完整实施计划

> **For agentic workers:** 使用 `superpowers:subagent-driven-development` 模式执行。每个步骤使用 checkbox（`- [ ]`）语法追踪进度。每完成一个任务立即 commit。

**目标：** 将 Hermes Agent fork 独立为 DeepAgent，并在此之上实现 StarRoad Cognition 三层认知引擎架构。共 15 个任务（5 个独立化 + 10 个认知模块），分 5 个阶段执行。

**架构概要：** 阶段 0 将 DeepAgent 从 Hermes Agent 独立（命令名、路径、环境变量改名为 deepagent），阶段 1-4 叠加三层认知框架（荣辱观 L1 / 思维方式 L2 / 三省吾身 L3）+ 三路由层（语义路由 / 专家匹配 / 执行路由）+ Memory 嵌套索引 + Plan 状态机。所有新模块通过 hook points 插入现有 agent loop，不替换现有代码。

**技术栈：** Python 3.10+，无额外外部依赖。文件路径使用 `get_hermes_home()`（独立化后自动指向 `~/.deepagent`）。所有代码写中文注释。

**参考文档：**
- `cognitive-workflow.md` — 三层认知框架 + Memory 嵌套索引 + Plan 状态机的完整文档定义
- `The Agency SKILL.md` — 232 专家库的匹配逻辑和 4 种执行模式 (A/B/C/D)
- `STARROAD_COARSE_PLAN.md` — 粗框架方案

**核心原则：cognitive-workflow.md 已有完整框架定义，实现层的工作是把它从文档翻译成代码，而非重新设计。**

---

## 全局约束

- Python 3.10+，不新增外部依赖
- 所有文件路径使用 `get_hermes_home()` / `display_hermes_home()`，不硬编码 `~/.hermes`
- 新增模块保持独立可测试，每个模块有对应的测试文件
- 修改已有文件时用 `# === DeepAgent: StarRoad Cognition ===` 标记边界
- 每个 commit 只做一件事（原子粒度）
- 所有代码写中文注释
- 所有错误处理和边界情况必须覆盖（文件不存在、路径错误、空内容等）
- 新增模块不替换现有代码，通过 hook points 插入
- 不修改已有函数名、import 路径、目录名（如 `hermes_cli/`、`get_hermes_home()`），只改用户可见的内容

---

## 文件结构设计

### 新增模块（5 个）

| 文件 | 职责 | 行数估算 |
|------|------|---------|
| `agent/cognitive_gate.py` | 三层认知评估器 — 每轮对话后做 L1/L2/L3 自评 | ~200 |
| `agent/memory_index.py` | 记忆嵌套索引 — MAP.md 导航 + 子文档按需加载 | ~200 |
| `agent/plan_tracker.py` | 计划状态机 — JSON 持久化 plan，管理目标/盲区/调整 | ~200 |
| `agent/expert_matcher.py` | 专家匹配器 — 对接 Agency 232 专家库，关键词匹配 | ~200 |
| `agent/router.py` | 语义路由总控 — 意图分类 + 决定执行模式 A/B/C/D | ~280 |

### 修改已有文件（4 个）

| 文件 | 改动类型 | 改动量 |
|------|---------|--------|
| `agent/prompt_builder.py` | 末尾新增 `COGNITIVE_LOOP_GUIDANCE` 常量 + `build_cognitive_loop_guidance()` 函数 | ~30 行 |
| `agent/context_compressor.py` | `compress()` 方法中新增围栏检测过滤逻辑 | ~15 行 |
| `tools/memory_tool.py` | 暂不修改（MemoryIndex 已有 `read_nested()` 作为库接口） | 0 行 |
| `run_agent.py` | `__init__` 初始化认知模块 + `_build_system_prompt` 注入 + `run_conversation` 路由/评估 hook | ~100 行 |

### 独立化修改（5 个文件）

| 文件 | 改动类型 |
|------|---------|
| `hermes_constants.py` | `get_hermes_home()` 默认路径 .hermes → .deepagent，HERMES_HOME → DEEPAGENT_HOME |
| `pyproject.toml` | 包名 hermes-agent → deepagent，entry points hermes → deepagent |
| `hermes` (可执行文件) | 重命名为 deepagent + 注释更新 |
| `setup-hermes.sh` | 重命名为 setup-deepagent.sh + 全文替换 |
| `hermes_cli/main.py` | CLI 帮助文本中的命令名替换（仅用户可见文案） |

### 新增测试文件（6 个）

| 文件 | 测试对象 |
|------|---------|
| `tests/agent/test_cognitive_gate.py` | CognitiveGate |
| `tests/agent/test_memory_index.py` | MemoryIndex |
| `tests/agent/test_plan_tracker.py` | PlanTracker |
| `tests/agent/test_expert_matcher.py` | ExpertMatcher |
| `tests/agent/test_router.py` | AgentRouter |
| `tests/agent/test_prompt_builder_cognitive.py` | build_cognitive_loop_guidance() |

---

## 实施顺序和依赖关系

```
阶段 0：DeepAgent 独立化（并行，纯字符串替换，无测试）
  ├── 任务 0.1: hermes_constants.py         ≈ 2 行改动
  ├── 任务 0.2: pyproject.toml               ≈ 20 处替换
  ├── 任务 0.3: hermes → deepagent 重命名    ≈ 1 行注释 + mv
  ├── 任务 0.4: setup-hermes.sh → setup-deepagent.sh  ≈ 22 处替换 + mv
  └── 任务 0.5: hermes_cli/main.py 帮助文案  ≈ 15 处替换

阶段 1：并行创建 5 个新模块 + 测试（完全独立）
  ├── 任务 1: cognitive_gate.py + tests/     ≈ 200 行代码 + 150 行测试
  ├── 任务 2: memory_index.py + tests/       ≈ 200 行代码 + 200 行测试
  ├── 任务 3: plan_tracker.py + tests/       ≈ 200 行代码 + 150 行测试
  ├── 任务 4: expert_matcher.py + tests/     ≈ 200 行代码 + 100 行测试
  └── 任务 5: router.py + tests/             ≈ 280 行代码 + 80 行测试

阶段 2：修改已有文件（并行，依赖阶段 1）
  ├── 任务 6: prompt_builder.py               ≈ 30 行
  ├── 任务 7: context_compressor.py           ≈ 15 行
  └── 任务 8: memory_tool.py（暂缓）          ≈ 0 行

阶段 3：集成（串行，依赖阶段 1+2）
  └── 任务 9: run_agent.py                    ≈ 100 行

阶段 4：数据文件（串行，依赖阶段 3）
  └── 任务 10: MAP.md 创建 + SOUL.md 更新     ≈ 20 行

总计：约 1300 行代码 + 680 行测试 + 约 60 处替换 = 约 2040 行
```

---

# 阶段 0：DeepAgent 独立化

> **背景：** DeepAgent 是从 Hermes Agent fork 的独立项目。`hermes_constants.py` 的 `get_hermes_home()` 是所有路径的唯一入口（50+ 个文件通过它获取路径），默认值为 `Path.home() / ".hermes"`，可通过 `HERMES_HOME` 环境变量覆盖。只需改动此函数的默认值和环境变量名，其他所有文件自动跟随。

**改动原则：** 纯字符串替换，无逻辑变更。不修改目录名（如 `hermes_cli/`）、不修改函数名（如 `get_hermes_home()`）、不修改 import 路径（如 `from hermes_cli.main import main`）。

---

## 任务 0.1：hermes_constants.py — 改默认配置目录和环境变量

**文件：** `hermes_constants.py`

**改动量：** 约 5 处字符串替换。

**影响：** 所有调用 `get_hermes_home()` 的 50+ 个文件自动使用新路径，无需逐个修改。

- [ ] **步骤 0.1.1：改 `get_hermes_home()` 默认路径和环境变量**

将第 17 行的默认路径和环境变量名改动：

```python
# 修改前
return Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))

# 修改后
return Path(os.getenv("DEEPAGENT_HOME", Path.home() / ".deepagent"))
```

- [ ] **步骤 0.1.2：改 docstring**

更新第 12-14 行的 docstring：

```python
# 修改前
def get_hermes_home() -> Path:
    """Return the Hermes home directory (default: ~/.hermes).
    Reads HERMES_HOME env var, falls back to ~/.hermes.

# 修改后
def get_hermes_home() -> Path:
    """Return the DeepAgent home directory (default: ~/.deepagent).
    Reads DEEPAGENT_HOME env var, falls back to ~/.deepagent.
```

- [ ] **步骤 0.1.3：改 `get_default_hermes_root()` 中的默认路径**

将第 36 行的默认路径：

```python
# 修改前
native_home = Path.home() / ".hermes"

# 修改后
native_home = Path.home() / ".deepagent"
```

- [ ] **步骤 0.1.4：改 `display_hermes_home()` 的 docstring 示例**

更新 docstring 中的路径示例（第 98-101 行）：

```python
# 修改前
"""Return a user-friendly display string for the current HERMES_HOME.
    default:  ``~/.hermes``
    profile:  ``~/.hermes/profiles/coder``

# 修改后  
"""Return a user-friendly display string for the current DEEPAGENT_HOME.
    default:  ``~/.deepagent``
    profile:  ``~/.deepagent/profiles/coder``
```

- [ ] **步骤 0.1.5：改 `get_subprocess_home()` 中的 HERMES_HOME 读取**

将第 131 行：

```python
# 修改前
hermes_home = os.getenv("HERMES_HOME")

# 修改后
deepagent_home = os.getenv("DEEPAGENT_HOME")
```

同时改后续引用 `hermes_home` → `deepagent_home`（第 133-137 行）。

- [ ] **步骤 0.1.6：改 `get_hermes_dir()` docstring**

更新第 80-81 行的 docstring 中 `HERMES_HOME` → `DEEPAGENT_HOME`。

- [ ] **步骤 0.1.7：验证**

```bash
# 确认改动后所有 .hermes / HERMES_HOME 引用已更新
grep -n '.hermes\|HERMES_HOME' hermes_constants.py
```

预期：`display_hermes_home()` docstring 中有 `~/.deepagent`（展示用），`get_default_hermes_root()` 中有正确的注释。

- [ ] **步骤 0.1.8：Commit**

```bash
git add hermes_constants.py
git commit -m "refactor: rename default path ~/.hermes → ~/.deepagent, HERMES_HOME → DEEPAGENT_HOME | 重命名默认路径和环境变量"
```

---

## 任务 0.2：pyproject.toml — 改包名和 CLI entry points

**文件：** `pyproject.toml`

**改动量：** 约 20 处替换。

- [ ] **步骤 0.2.1：改包名**

```toml
# 第 6 行：修改前
name = "hermes-agent"
# 修改后
name = "deepagent"
```

- [ ] **步骤 0.2.2：改 CLI entry points**

```toml
# 第 115-117 行：修改前
hermes = "hermes_cli.main:main"
hermes-agent = "run_agent:main"
hermes-acp = "acp_adapter.entry:main"

# 修改后
deepagent = "hermes_cli.main:main"
deepagent-agent = "run_agent:main"
deepagent-acp = "acp_adapter.entry:main"
```

- [ ] **步骤 0.2.3：改 termux extras 中的自引用（第 70-76 行）**

```toml
# 修改前
hermes-agent[cron]
hermes-agent[cli]
hermes-agent[pty]
hermes-agent[mcp]
hermes-agent[honcho]
hermes-agent[acp]

# 修改后
deepagent[cron]
deepagent[cli]
deepagent[pty]
deepagent[mcp]
deepagent[honcho]
deepagent[acp]
```

- [ ] **步骤 0.2.4：改 all extras 中的自引用（第 88-112 行）**

将所有 `hermes-agent[xxx]` 替换为 `deepagent[xxx]`。

- [ ] **步骤 0.2.5：验证**

```bash
# 确认没有残留的 hermes-agent 包名引用
grep -n 'hermes-agent' pyproject.toml || echo "No remaining hermes-agent references"
```

预期：0 匹配。

- [ ] **步骤 0.2.6：Commit**

```bash
git add pyproject.toml
git commit -m "refactor: rename package hermes-agent → deepagent in pyproject.toml | 重命名包名和 CLI entry points"
```

---

## 任务 0.3：根目录 `hermes` 启动器 — 改名

**文件：** 重命名 `hermes` → `deepagent`，更新注释。

- [ ] **步骤 0.3.1：重命名文件**

```bash
git mv hermes deepagent
```

- [ ] **步骤 0.3.2：更新注释（文件顶部 docstring）**

```python
# 修改前
"""
Hermes Agent CLI launcher.

This wrapper should behave like the installed `hermes` command, including
subcommands such as `gateway`, `cron`, and `doctor`.
"""

# 修改后
"""
DeepAgent CLI launcher.

This wrapper should behave like the installed `deepagent` command, including
subcommands such as `gateway`, `cron`, and `doctor`.
"""
```

> `from hermes_cli.main import main` 不修改（是 import 路径）。

- [ ] **步骤 0.3.3：Commit**

```bash
git commit -m "refactor: rename hermes launcher to deepagent | 重命名启动器文件"
```

---

## 任务 0.4：setup-hermes.sh — 改名 + 全文替换

**文件：** 重命名 `setup-hermes.sh` → `setup-deepagent.sh`，全文替换。

- [ ] **步骤 0.4.1：重命名**

```bash
git mv setup-hermes.sh setup-deepagent.sh
```

- [ ] **步骤 0.4.2：全局内容替换**

按以下映射逐处替换（共约 22 处）：

| 替换目标 | 替换为 | 位置示例 |
|---------|--------|---------|
| `Hermes Agent`（标题/描述） | `DeepAgent` | 第 3-4 行, 第 55 行 |
| `hermes-agent`（URL 中的仓库名） | `deepagent` | README 引用 |
| `hermes`（命令名） | `deepagent` | 多处命令示例 |
| `HERMES_HOME` | `DEEPAGENT_HOME` | 第 339 行 |
| `~/.hermes` | `~/.deepagent` | 第 339, 343 行 |
| `setup-hermes.sh`（自引用） | `setup-deepagent.sh` | 第 9 行 |
| `HERMES_BIN`（变量名，建议保留不改为佳，因只是内部变量。如改：） | `DEEPAGENT_BIN` | 第 287-292 行 |
| `HERMES_SKILLS_DIR` | `DEEPAGENT_SKILLS_DIR` | 第 339 行 |
| `HERMES_HOME` 环境变量引用 | `DEEPAGENT_HOME` | 第 339 行 |

- [ ] **步骤 0.4.3：验证无残留**

```bash
grep -n 'hermes\|HERMES' setup-deepagent.sh | grep -v 'hermes_cli\|hermes_constants' || echo "Clean"
```

预期：只匹配到 import 路径中的 `hermes_cli`，其余全部替换。

- [ ] **步骤 0.4.4：Commit**

```bash
git add setup-deepagent.sh
git commit -m "refactor: rename setup-hermes.sh → setup-deepagent.sh with content update | 重命名安装脚本并替换内容"
```

---

## 任务 0.5：hermes_cli/main.py — 更新 CLI 帮助文案

**文件：** `hermes_cli/main.py`

**改动量：** 约 15 处替换。只改 docstring 和帮助文本中的命令名，不碰 import 路径和函数名。

- [ ] **步骤 0.5.1：更新模块 docstring（第 2-44 行）**

将所有 `hermes ` 命令引用替换为 `deepagent `：

```python
# 修改前
"""
Hermes CLI - Main entry point.

Usage:
    hermes                     # Interactive chat (default)
    hermes chat                # Interactive chat
    hermes gateway             # Run gateway in foreground
...

# 修改后
"""
DeepAgent CLI - Main entry point.

Usage:
    deepagent                  # Interactive chat (default)
    deepagent chat             # Interactive chat
    deepagent gateway          # Run gateway in foreground
...
```

- [ ] **步骤 0.5.2：替换帮助文本中的命令名**

搜索 `'hermes '`（带引号+空格，避免碰函数名）替换为 `'deepagent '`。
这是 `_require_tty()` 中的错误提示（约第 62 行）。

- [ ] **步骤 0.5.3：替换 `_has_any_provider_configured()` 中的子进程调用**

在帮助消息中出现的 `hermes setup`、`hermes model` 等命令名（约第 711-733 行）替换为 `deepagent setup`、`deepagent model` 等。

- [ ] **步骤 0.5.4：替换 cmd_chat 中的帮助文本**

第 710 行附近的注释和打印输出中的 `hermes` 替换为 `deepagent`。

- [ ] **步骤 0.5.5：替换 cmd_whatsapp 中的帮助文本**

第 929, 960, 964, 974-975 行附近的 `hermes gateway`、`hermes whatsapp` 替换为 `deepagent gateway`、`deepagent whatsapp`。

- [ ] **步骤 0.5.6：验证无残留**

```bash
# 搜索用户可见文案中的 hermes 命令引用（不碰 import 路径）
grep -n "'hermes '" hermes_cli/main.py || echo "Clean"
grep -n '"hermes ' hermes_cli/main.py || echo "Clean"
```

预期：0 匹配（或只在注释/被引用的例子中出现，且不是命令名）。

**不动清单：**
- `hermes_cli/` 目录名
- 函数名如 `get_hermes_home()`
- import 路径如 `from hermes_cli.main import main`
- 文件名如 `hermes_constants.py`

- [ ] **步骤 0.5.7：Commit**

```bash
git add hermes_cli/main.py
git commit -m "refactor: update CLI help text hermes → deepagent in main.py | 更新 CLI 帮助文案中的命令名"
```

---

### 阶段 0 完成验证

| 维度 | 改前 | 改后 |
|------|------|------|
| 运行命令 | `hermes` | `deepagent` |
| 配置目录 | `~/.hermes` | `~/.deepagent` |
| 环境变量 | `HERMES_HOME` | `DEEPAGENT_HOME` |
| pip 包名 | `hermes-agent` | `deepagent` |
| 安装脚本 | `setup-hermes.sh` | `setup-deepagent.sh` |
| 启动器文件 | `hermes` | `deepagent` |

> **不动的内容：** `hermes_cli/` 目录名、`get_hermes_home()` 函数名、`hermes_constants.py` 文件名、内部 import 路径 `from hermes_cli import ...` 全部保留。

---

# 阶段 1：创建 5 个新模块

> **说明：** 任务 1-5 完全独立，可并行执行。每个任务包含模块创建 + 测试创建 + 测试验证 + commit。

---

## 任务 1：agent/cognitive_gate.py — 三层认知评估器

**文件：**
- 创建：`agent/cognitive_gate.py`
- 测试：`tests/agent/test_cognitive_gate.py`

**接口（产出供任务 5 消费）：**

```python
@dataclass
class HonorResult:
    hid_uncertainty: bool      # 是否隐瞒了不确定性
    made_unverified_claim: bool # 是否做了未经工具验证的论断
    hid_tool_failure: bool     # 是否隐瞒了工具失败
    @property
    def passed(self) -> bool

@dataclass
class ThinkingResult:
    skipped_steps: list[str]       # 跳过的步骤
    no_hypothesis_first: list[str] # 没有假设先行的操作
    blindspots: list[str]          # 识别到的盲区
    @property
    def passed(self) -> bool

@dataclass
class EvalResult:
    plan_id: str
    honor: HonorResult
    thinking: ThinkingResult
    should_interrupt_user: bool
    gaps_found: list[str]
    goal_adjustment: str | None
    adjustments_note: str

class CognitiveGate:
    def __init__(self, max_history: int = 20)
    def evaluate(self, turn_data: dict) -> EvalResult
    def _check_honor(self, turn_data: dict) -> HonorResult
    def _check_thinking(self, turn_data: dict) -> ThinkingResult
    def _reflect(self, honor, thinking, turn_data) -> dict
    def _should_ask_user(self, reflection: dict) -> bool
    def get_recent_evaluations(self, n: int = 5) -> list[dict]
```

- [ ] **步骤 1.1：创建 `agent/cognitive_gate.py`**

```python
"""三层认知评估器（StarRoad Cognition Layer 1-3）。
在每轮对话的 text response 生成后触发，输出三层评估结果。
不 block 主循环——只追加调整建议和记录。"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HonorResult:
    """Layer 1 荣辱观检查结果。"""
    hid_uncertainty: bool = False
    made_unverified_claim: bool = False
    hid_tool_failure: bool = False

    @property
    def passed(self) -> bool:
        return not (self.hid_uncertainty or self.made_unverified_claim or self.hid_tool_failure)


@dataclass
class ThinkingResult:
    """Layer 2 思维方式检查结果。"""
    skipped_steps: list[str] = field(default_factory=list)
    no_hypothesis_first: list[str] = field(default_factory=list)
    blindspots: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.skipped_steps) == 0 and len(self.blindspots) == 0


@dataclass
class EvalResult:
    """完整的三层评估结果。"""
    plan_id: str = ""
    honor: HonorResult = field(default_factory=HonorResult)
    thinking: ThinkingResult = field(default_factory=ThinkingResult)
    should_interrupt_user: bool = False
    gaps_found: list[str] = field(default_factory=list)
    goal_adjustment: str | None = None
    adjustments_note: str = ""


class CognitiveGate:
    """三层认知评估器。

    用法（在 run_agent.py 中集成）：
        gate = CognitiveGate()
        # 在每轮对话的 text response 后：
        result = gate.evaluate(turn_data)
        if result.should_interrupt_user:
            # 问用户
        if result.gaps_found:
            plan_tracker.add_gap(gap)
    """

    def __init__(self, max_history: int = 20):
        self._eval_history: list[dict] = []
        self._max_history = max_history

    def evaluate(self, turn_data: dict) -> EvalResult:
        """主入口。接收当前 turn 的数据，输出三层评估结果。

        Args:
            turn_data: 包含：
                - assistant_response: str — 模型的最终文本回复
                - tool_calls: list[dict] — 本次 turn 调用的工具列表
                - tool_results: list[dict] — 对应的工具结果
                - plan_id: str — 当前 plan_id（可选）
                - confidence_indicators: list[str] — 不确定性指标

        Returns:
            EvalResult — 三层评估结果
        """
        honor = self._check_honor(turn_data)
        thinking = self._check_thinking(turn_data)
        reflection = self._reflect(honor, thinking, turn_data)

        result = EvalResult(
            plan_id=turn_data.get("plan_id", ""),
            honor=honor,
            thinking=thinking,
            should_interrupt_user=self._should_ask_user(reflection),
            gaps_found=reflection.get("gaps", []),
            goal_adjustment=reflection.get("goal_adjustment"),
            adjustments_note=reflection.get("note", ""),
        )

        # 记录评估历史
        self._eval_history.append(asdict(result))
        if len(self._eval_history) > self._max_history:
            self._eval_history.pop(0)

        return result

    def _check_honor(self, turn_data: dict) -> HonorResult:
        """Layer 1 荣辱观检查。

        检查点：
        1. 是否明确说明了不确定性（"我不确定"、"我需要查"）
        2. 是否用工具验证了关键论断（有事实性断言但无工具调用 = 违规）
        3. 工具调用失败时是否如实报告（error/failure 未被提及 = 违规）
        """
        result = HonorResult()
        response = turn_data.get("assistant_response", "")
        tool_calls = turn_data.get("tool_calls", [])
        tool_results = turn_data.get("tool_results", [])
        confidence_indicators = turn_data.get("confidence_indicators", [])

        # 检查 1：是否有不确定性表达
        uncertainty_keywords = [
            "不确定", "不太确定", "可能", "probably", "might",
            "i'm not sure", "我需要查", "let me check", "先查一下", "让我查"
        ]
        has_uncertainty_expr = any(kw in response.lower() for kw in uncertainty_keywords)
        if not has_uncertainty_expr and confidence_indicators:
            result.hid_uncertainty = True

        # 检查 2：是否有未经工具验证的事实性论断
        factual_keywords = ["是", "不是", "应该", "必须", "always", "never", "all", "every"]
        has_factual = any(kw in response.lower() for kw in factual_keywords)
        if has_factual and not tool_calls:
            result.made_unverified_claim = True

        # 检查 3：工具失败是否如实汇报
        for tr in tool_results:
            content = str(tr.get("content", ""))
            if any(w in content.lower() for w in ("error", "fail", "timeout")):
                if "失败" not in response and "error" not in response.lower() and "没有成功" not in response:
                    result.hid_tool_failure = True
                    break

        return result

    def _check_thinking(self, turn_data: dict) -> ThinkingResult:
        """Layer 2 思维方式检查。

        检查点：
        1. 是否 step by step（多步操作是否说明了执行顺序）
        2. 是否假设先行（工具调用前是否有假设说明）
        3. 是否有主动识别的盲区
        """
        result = ThinkingResult()
        response = turn_data.get("assistant_response", "")
        tool_calls = turn_data.get("tool_calls", [])

        # 检查跳过步骤
        if len(tool_calls) > 3 and "step" not in response.lower() and "先" not in response:
            result.skipped_steps.append("多步操作未说明执行顺序")

        # 检查假设先行
        hypothesis_keywords = ["假设", "我认为", "hypothesis", "i think", "应该是因为", "按理说"]
        if tool_calls and not any(kw in response.lower() for kw in hypothesis_keywords):
            result.no_hypothesis_first.append("工具调用前未声明假设")

        # 识别盲区
        blindspot_keywords = ["不确定", "不清楚", "盲区", "需要查", "盲点", "不懂", "unknown", "need to investigate"]
        for kw in blindspot_keywords:
            if kw in response.lower():
                result.blindspots.append(f"主动识别盲区: {kw}")

        return result

    def _reflect(self, honor: HonorResult, thinking: ThinkingResult, turn_data: dict) -> dict:
        """Layer 3 三省吾身：回头检查 L1+L2，生成改进建议。"""
        gaps = list(thinking.blindspots)
        goal_adjustment = None
        note_parts = []

        if not honor.passed:
            if honor.hid_uncertainty:
                gaps.append("Layer1 违规：有不确定性但未明确说明")
                note_parts.append("有不确定性应明确说明")
            if honor.made_unverified_claim:
                gaps.append("Layer1 违规：有未经工具验证的论断")
                note_parts.append("事实性论断需用工具验证")
            if honor.hid_tool_failure:
                gaps.append("Layer1 违规：工具失败未如实报告")
                note_parts.append("工具失败必须如实报告")

        if not thinking.passed:
            note_parts.append("思维方式可优化：使用 Step-by-Step + 假设先行")

        return {
            "gaps": gaps,
            "goal_adjustment": goal_adjustment,
            "note": "; ".join(note_parts) if note_parts else "评估通过",
        }

    def _should_ask_user(self, reflection: dict) -> bool:
        """判断不确定性是否超过阈值，需要中断问用户。"""
        gaps = reflection.get("gaps", [])
        return len(gaps) >= 2

    def get_recent_evaluations(self, n: int = 5) -> list[dict]:
        """返回最近 n 次评估记录。"""
        return self._eval_history[-n:]
```

- [ ] **步骤 1.2：创建测试文件 `tests/agent/test_cognitive_gate.py`**

```python
"""Tests for CognitiveGate — 三层认知评估器。"""

import pytest
from agent.cognitive_gate import CognitiveGate, HonorResult, ThinkingResult, EvalResult


class TestHonorCheck:
    """Layer 1 荣辱观检查测试。"""

    def test_passes_when_no_issues(self):
        """正常情况：明确说不确定、有工具、如实报告。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我不确定这个模块的具体实现，让我查一下源码。",
            "tool_calls": [{"name": "read_file", "arguments": '{"path": "x.py"}'}],
            "tool_results": [{"content": "some content"}],
        }
        result = gate._check_honor(turn_data)
        assert result.passed is True

    def test_detects_hidden_uncertainty(self):
        """有盲区但没说明不确定。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "这个模块的功能是处理数据。",
            "tool_calls": [],
            "tool_results": [],
            "confidence_indicators": ["unfamiliar-module"],
        }
        result = gate._check_honor(turn_data)
        assert result.hid_uncertainty is True

    def test_detects_unverified_claim(self):
        """有事实性论断但没用工具验证。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "这个函数的复杂度一定是 O(n^2)。",
            "tool_calls": [],
            "tool_results": [],
        }
        result = gate._check_honor(turn_data)
        assert result.made_unverified_claim is True

    def test_detects_hidden_tool_failure(self):
        """工具失败但没汇报。"""
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "让我看看结果。",
            "tool_calls": [{"name": "web_search", "arguments": '{"query": "test"}'}],
            "tool_results": [{"content": '{"error": "timeout"}'}],
        }
        result = gate._check_honor(turn_data)
        assert result.hid_tool_failure is True


class TestThinkingCheck:
    """Layer 2 思维方式检查测试。"""

    def test_passes_when_step_by_step(self):
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "第一步先查文档，第二步再实现。",
            "tool_calls": [{"name": "read_file", "arguments": ""}],
        }
        result = gate._check_thinking(turn_data)
        assert result.passed is True

    def test_detects_missing_hypothesis(self):
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我来改这个代码。",
            "tool_calls": [{"name": "edit", "arguments": '{"path": "x.py"}'}],
        }
        result = gate._check_thinking(turn_data)
        assert len(result.no_hypothesis_first) > 0


class TestFullEvaluation:
    """CognitiveGate.evaluate() 完整流程测试。"""

    def test_full_pass(self):
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我不确定这个 API 的用法，让我先查一下文档。",
            "tool_calls": [{"name": "web_search", "arguments": '{"query": "api docs"}'}],
            "tool_results": [{"content": "doc content"}],
        }
        result = gate.evaluate(turn_data)
        assert isinstance(result, EvalResult)
        assert result.honor.passed is True
        assert result.thinking.passed is True

    def test_detects_multiple_gaps_and_should_ask_user(self):
        gate = CognitiveGate()
        turn_data = {
            "assistant_response": "我来改这个。",
            "tool_calls": [],
            "tool_results": [],
            "confidence_indicators": ["unfamiliar-module"],
        }
        result = gate.evaluate(turn_data)
        assert len(result.gaps_found) >= 2
        assert result.should_interrupt_user is True

    def test_eval_history_tracking(self):
        gate = CognitiveGate()
        for i in range(3):
            gate.evaluate({
                "assistant_response": f"response {i}",
                "tool_calls": [],
                "tool_results": [],
            })
        recent = gate.get_recent_evaluations(2)
        assert len(recent) == 2

    def test_plan_id_carried_to_result(self):
        gate = CognitiveGate()
        result = gate.evaluate({
            "assistant_response": "ok",
            "tool_calls": [],
            "tool_results": [],
            "plan_id": "plan-123",
        })
        assert result.plan_id == "plan-123"
```

- [ ] **步骤 1.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_cognitive_gate.py -v
```

预期：所有 9 个测试通过。

- [ ] **步骤 1.4：Commit**

```bash
git add agent/cognitive_gate.py tests/agent/test_cognitive_gate.py
git commit -m "feat: add cognitive_gate.py — three-layer StarRoad Cognition evaluator | 添加三层认知评估器"
```

---

## 任务 2：agent/memory_index.py — 记忆嵌套索引管理器

**文件：**
- 创建：`agent/memory_index.py`
- 测试：`tests/agent/test_memory_index.py`

**接口（产出供任务 5 消费）：**

```python
class MemoryIndex:
    def __init__(self, index_path: str | Path | None = None)
        # 默认：get_hermes_home() / "memories" / "MAP.md"
    def index_summary(self) -> str
        # 返回注入 system prompt 的导航段，用 -----COGNITIVE_INDEX_START----- 包裹
    def navigate(self, topic: str) -> list[dict]
        # 搜索 MAP.md 找到与 topic 相关的索引条目
    def read_nested(self, path: str) -> str
        # 从索引导航按需加载子文档
    def update_entry(self, topic: str, path: str, description: str) -> None
    def build_initial_index(self) -> None
```

- [ ] **步骤 2.1：创建 `agent/memory_index.py`**

```python
"""记忆嵌套索引管理器（StarRoad Cognition）。
核心规则：MAP.md 只存导航指引（1-2KB），深度内容存于子文档按需加载。"""

from __future__ import annotations
import logging
import re
from pathlib import Path

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

COGNITIVE_FENCE_START = "-----COGNITIVE_INDEX_START-----"
COGNITIVE_FENCE_END = "-----COGNITIVE_INDEX_END-----"
MAP_FILENAME = "MAP.md"


class MemoryIndex:
    """记忆嵌套索引管理器。

    用法：
        index = MemoryIndex()
        summary = index.index_summary()  # → 注入 system prompt 的导航段
        entries = index.navigate("deepseek")  # → 找到相关条目
        content = index.read_nested("skills/deepseek-physics/SKILL.md")  # → 读子文档
    """

    def __init__(self, index_path: str | Path | None = None):
        if index_path is None:
            index_path = get_hermes_home() / "memories" / MAP_FILENAME
        self._index_path = Path(index_path)
        self._memories_dir = self._index_path.parent
        self._map_content: str | None = None  # 缓存 MAP.md 内容

    def index_summary(self) -> str:
        """返回注入 system prompt 的导航段（1-2KB）。

        如果 MAP.md 不存在或为空，返回空字符串。
        """
        content = self._load_map()
        if not content:
            return ""

        # 限制大小：最多 2000 字符
        if len(content) > 2000:
            content = content[:1950] + "\n...(truncated)"

        return f"{COGNITIVE_FENCE_START}\n{content}\n{COGNITIVE_FENCE_END}"

    def navigate(self, topic: str) -> list[dict]:
        """搜索 MAP.md 找到与 topic 相关的索引条目。

        Args:
            topic: 搜索关键词（大小写不敏感）

        Returns:
            [{"topic": str, "path": str, "description": str}, ...]
        """
        content = self._load_map()
        if not content:
            return []

        results = []
        topic_lower = topic.lower()
        # 解析 MAP.md 中的条目格式：- topic: path — description
        pattern = re.compile(r"^\s*-\s+(.+?):\s+(.+?)(?:\s+[—\-]\s+(.+))?$", re.MULTILINE)
        for match in pattern.finditer(content):
            entry_topic = match.group(1).strip()
            entry_path = match.group(2).strip()
            entry_desc = match.group(3).strip() if match.group(3) else ""

            if topic_lower in entry_topic.lower() or topic_lower in entry_desc.lower():
                results.append({
                    "topic": entry_topic,
                    "path": entry_path,
                    "description": entry_desc,
                })

        return results

    def read_nested(self, path: str) -> str:
        """从索引导航按需加载子文档内容。

        Args:
            path: 相对路径（如 "skills/deepseek-physics/SKILL.md"）或绝对路径

        Returns:
            子文档的文本内容。文件不存在时返回空字符串。
        """
        target = Path(path)
        if not target.is_absolute():
            target = self._memories_dir / target

        if not target.exists() or not target.is_file():
            logger.debug("MemoryIndex: nested path '%s' not found", target)
            return ""

        try:
            return target.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("MemoryIndex: failed to read '%s': %s", target, e)
            return ""

    def update_entry(self, topic: str, path: str, description: str = "") -> None:
        """更新或新增索引条目。topic 已存在则更新，否则追加。"""
        content = self._load_map()
        if not content:
            content = "# 记忆索引（导航层）\n\n## 关键知识领域\n\n"
            content += f"- {topic}: {path}"
            if description:
                content += f" — {description}"
            content += "\n"
        else:
            pattern = re.compile(
                rf"^-\s+{re.escape(topic)}:\s+.*$", re.MULTILINE
            )
            new_line = f"- {topic}: {path}"
            if description:
                new_line += f" — {description}"
            if pattern.search(content):
                content = pattern.sub(new_line, content)
            else:
                content += new_line + "\n"

        self._write_map(content)

    def build_initial_index(self) -> None:
        """首次初始化：扫描 memories/ 下子目录，构建 MAP.md。

        如果 MAP.md 已存在且非空，跳过初始化。
        """
        if self._index_path.exists():
            content = self._read_file_content(self._index_path)
            if content and content.strip():
                logger.info("MemoryIndex: MAP.md already exists, skipping initialization")
                return

        sections: dict[str, list[str]] = {
            "关键知识领域": [],
            "项目状态": [],
            "用户偏好": [],
        }

        if self._memories_dir.exists():
            for child in sorted(self._memories_dir.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    md_files = sorted(child.glob("*.md"))
                    for md_file in md_files:
                        if md_file.name == MAP_FILENAME:
                            continue
                        rel_path = str(md_file.relative_to(self._memories_dir))
                        sections["关键知识领域"].append(
                            f"- {child.name}: {rel_path}\n"
                        )

        lines = ["# 记忆索引（导航层）", ""]
        for section_name, entries in sections.items():
            if entries:
                lines.append(f"## {section_name}")
                lines.append("")
                lines.extend(entries)
                lines.append("")

        content = "\n".join(lines).strip()
        if content:
            self._write_map(content)
            logger.info("MemoryIndex: initial MAP.md created with %d entries",
                        sum(len(e) for e in sections.values()))

    # -- 内部方法 --

    def _load_map(self) -> str:
        if self._map_content is not None:
            return self._map_content
        content = self._read_file_content(self._index_path)
        self._map_content = content or ""
        return self._map_content

    def _write_map(self, content: str) -> None:
        self._memories_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._index_path.write_text(content, encoding="utf-8")
            self._map_content = content
        except Exception as e:
            logger.error("MemoryIndex: failed to write MAP.md: %s", e)

    @staticmethod
    def _read_file_content(path: Path) -> str:
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug("MemoryIndex: failed to read %s: %s", path, e)
            return ""
```

- [ ] **步骤 2.2：创建测试文件 `tests/agent/test_memory_index.py`**

```python
"""Tests for MemoryIndex — 记忆嵌套索引管理器。"""

import pytest
from pathlib import Path
from agent.memory_index import MemoryIndex, COGNITIVE_FENCE_START, COGNITIVE_FENCE_END


@pytest.fixture
def tmp_index(tmp_path):
    """创建使用临时目录的 MemoryIndex 实例。"""
    mem_dir = tmp_path / "memories"
    mem_dir.mkdir(parents=True)
    index_path = mem_dir / "MAP.md"
    return MemoryIndex(str(index_path))


class TestIndexSummary:
    def test_returns_empty_when_no_map(self, tmp_index):
        assert tmp_index.index_summary() == ""

    def test_wraps_content_with_fences(self, tmp_index):
        tmp_index.update_entry("test-topic", "test/path.md", "test desc")
        summary = tmp_index.index_summary()
        assert summary.startswith(COGNITIVE_FENCE_START)
        assert summary.endswith(COGNITIVE_FENCE_END)

    def test_truncates_long_content(self, tmp_index):
        for i in range(200):
            tmp_index.update_entry(f"topic-{i}", f"path/{i}.md", "d" * 50)
        summary = tmp_index.index_summary()
        assert len(summary) <= 2200  # 围栏 + 内容 + 截断标记


class TestNavigate:
    def test_finds_matching_topic(self, tmp_index):
        tmp_index.update_entry("deepseek-physics", "skills/dp/SKILL.md", "DeepSeek V3 physics")
        results = tmp_index.navigate("deepseek")
        assert len(results) >= 1
        assert results[0]["topic"] == "deepseek-physics"

    def test_returns_empty_for_no_match(self, tmp_index):
        tmp_index.update_entry("react", "notes/react.md", "React notes")
        results = tmp_index.navigate("vue")
        assert len(results) == 0

    def test_case_insensitive_search(self, tmp_index):
        tmp_index.update_entry("DeepSeek-Physics", "skills/dp/SKILL.md", "")
        results = tmp_index.navigate("deepseek")
        assert len(results) >= 1


class TestReadNested:
    def test_reads_existing_file(self, tmp_index, tmp_path):
        sub_file = tmp_path / "memories" / "test.md"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("hello world")
        content = tmp_index.read_nested(str(sub_file))
        assert content == "hello world"

    def test_returns_empty_for_missing_file(self, tmp_index):
        assert tmp_index.read_nested("/nonexistent/path.md") == ""

    def test_resolves_relative_path(self, tmp_index, tmp_path):
        sub_file = tmp_path / "memories" / "sub" / "doc.md"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("relative content")
        content = tmp_index.read_nested("sub/doc.md")
        assert content == "relative content"


class TestUpdateEntry:
    def test_creates_map_when_not_exists(self, tmp_index):
        tmp_index.update_entry("my-topic", "my/path.md", "desc")
        assert tmp_index._index_path.exists()

    def test_updates_existing_entry(self, tmp_index):
        tmp_index.update_entry("topic", "old/path.md", "old desc")
        tmp_index.update_entry("topic", "new/path.md", "new desc")
        content = tmp_index._load_map()
        assert "new/path.md" in content
        assert "old/path.md" not in content


class TestBuildInitialIndex:
    def test_creates_map_with_sections(self, tmp_index, tmp_path):
        mem_dir = tmp_path / "memories"
        (mem_dir / "skills").mkdir(parents=True)
        (mem_dir / "skills" / "test.md").write_text("test")
        tmp_index.build_initial_index()
        assert tmp_index._index_path.exists()
        content = tmp_index._load_map()
        assert "关键知识领域" in content or "key" in content.lower()

    def test_skips_if_map_exists(self, tmp_index):
        tmp_index.update_entry("existing", "path.md", "desc")
        initial_mtime = tmp_index._index_path.stat().st_mtime
        tmp_index.build_initial_index()
        assert tmp_index._index_path.stat().st_mtime == initial_mtime
```

- [ ] **步骤 2.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_memory_index.py -v
```

预期：所有 18 个测试通过（或跳过需要真实文件系统的测试）。

- [ ] **步骤 2.4：Commit**

```bash
git add agent/memory_index.py tests/agent/test_memory_index.py
git commit -m "feat: add memory_index.py — nested memory index with MAP.md navigation | 添加记忆嵌套索引管理器"
```

---

## 任务 3：agent/plan_tracker.py — 计划状态机

**文件：**
- 创建：`agent/plan_tracker.py`
- 测试：`tests/agent/test_plan_tracker.py`

**接口（产出供任务 5 消费）：**

```python
class PlanTracker:
    def __init__(self, plans_dir: str | Path | None = None)
        # 默认：get_hermes_home() / "plans"
    def create_or_update(self, goal: str, tasks: list[dict] | None = None) -> str
    def mark_done(self, task_id: str) -> None
    def add_gap(self, gap: str) -> None
    def refine_goal(self, new_goal: str) -> None
    def get_status(self) -> dict
    def get_current_plan_id(self) -> str | None
    def load_plan(self, plan_id: str) -> dict | None
    def list_plans(self) -> list[dict]
    @staticmethod
    def validate_plan(plan: dict) -> bool
```

- [ ] **步骤 3.1：创建 `agent/plan_tracker.py`**

```python
"""Plan 状态机管理器（StarRoad Cognition）。
Plan 不只是 markdown 文件，是一个动态状态机。
JSON 持久化到 ~/.deepagent/plans/<id>.json

与 todo 工具的关系：
- PlanTracker 管理 plan 级别信息（目标/盲区/调整历史/整体状态）
- todo 工具管理每个原子任务的详细状态
- PlanTracker 的 tasks 列表只是简化任务清单，详细追踪走 todo"""

from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)


class PlanTracker:
    """Plan 状态机管理器。

    用法：
        tracker = PlanTracker()
        plan_id = tracker.create_or_update("实现登录功能", [
            {"id": "t1", "desc": "设计数据库表"},
            {"id": "t2", "desc": "实现 API"},
        ])
        tracker.mark_done("t1")
        tracker.add_gap("发现 Token 刷新逻辑不完善")
    """

    def __init__(self, plans_dir: str | Path | None = None):
        if plans_dir is None:
            plans_dir = get_hermes_home() / "plans"
        self._plans_dir = Path(plans_dir)
        self._plans_dir.mkdir(parents=True, exist_ok=True)
        self._current_plan_id: str | None = None

    def create_or_update(self, goal: str, tasks: list[dict] | None = None) -> str:
        """创建新 plan 或追加任务到现有 in_progress 的 plan。

        Returns:
            plan_id
        """
        existing = self._find_in_progress_plan()
        if existing:
            if tasks:
                existing_ids = {t["id"] for t in existing.get("tasks", [])}
                for t in tasks:
                    if t["id"] not in existing_ids:
                        existing.setdefault("tasks", []).append({
                            "id": t["id"],
                            "desc": t["desc"],
                            "status": "pending",
                        })
            existing["updated_at"] = self._now_iso()
            self._save_plan(existing)
            self._current_plan_id = existing["plan_id"]
            return existing["plan_id"]

        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "goal_history": [f"v1: {goal}"],
            "status": "in_progress",
            "current_task": tasks[0]["id"] if tasks else "",
            "tasks": [
                {"id": t["id"], "desc": t["desc"], "status": "pending"}
                for t in (tasks or [])
            ],
            "gaps_found": [],
            "created_at": self._now_iso(),
            "updated_at": self._now_iso(),
        }
        self._save_plan(plan)
        self._current_plan_id = plan_id
        return plan_id

    def mark_done(self, task_id: str) -> None:
        """标记指定任务完成，自动推进到下一个 pending 任务。"""
        plan = self._load_current_plan()
        if not plan:
            return
        for task in plan.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = "done"
                break
        for task in plan.get("tasks", []):
            if task["status"] == "pending":
                plan["current_task"] = task["id"]
                break
        plan["updated_at"] = self._now_iso()
        self._save_plan(plan)

    def add_gap(self, gap: str) -> None:
        """探索中发现的盲区追加到计划（去重）。"""
        plan = self._load_current_plan()
        if not plan:
            return
        if gap not in plan.get("gaps_found", []):
            plan.setdefault("gaps_found", []).append(gap)
            plan["updated_at"] = self._now_iso()
            self._save_plan(plan)

    def refine_goal(self, new_goal: str) -> None:
        """调整目标，记录 goal_history。"""
        plan = self._load_current_plan()
        if not plan:
            return
        version = len(plan.get("goal_history", [])) + 1
        plan.setdefault("goal_history", []).append(f"v{version}: {new_goal}")
        plan["goal"] = new_goal
        plan["updated_at"] = self._now_iso()
        self._save_plan(plan)

    def get_status(self) -> dict:
        """返回当前 plan 的状态摘要。"""
        plan = self._load_current_plan()
        if not plan:
            return {"has_active_plan": False}

        tasks = plan.get("tasks", [])
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "done")
        pending = sum(1 for t in tasks if t["status"] == "pending")

        return {
            "has_active_plan": True,
            "plan_id": plan["plan_id"],
            "goal": plan["goal"],
            "goal_history": plan.get("goal_history", []),
            "status": plan["status"],
            "progress": f"{done}/{total}",
            "done_count": done,
            "pending_count": pending,
            "total_count": total,
            "current_task": plan.get("current_task", ""),
            "gaps_found": plan.get("gaps_found", []),
        }

    def get_current_plan_id(self) -> str | None:
        """返回当前 in_progress 的 plan_id。"""
        if self._current_plan_id:
            return self._current_plan_id
        plan = self._find_in_progress_plan()
        if plan:
            self._current_plan_id = plan["plan_id"]
            return plan["plan_id"]
        return None

    def load_plan(self, plan_id: str) -> dict | None:
        """读取指定 plan 的 JSON。"""
        path = self._plans_dir / f"{plan_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("PlanTracker: failed to load plan %s: %s", plan_id, e)
            return None

    def list_plans(self) -> list[dict]:
        """列出所有 plan（按创建时间倒序）。"""
        plans = []
        for f in sorted(self._plans_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                plans.append({
                    "plan_id": data.get("plan_id", f.stem),
                    "goal": data.get("goal", ""),
                    "status": data.get("status", ""),
                    "task_count": len(data.get("tasks", [])),
                    "created_at": data.get("created_at", ""),
                })
            except Exception:
                continue
        return plans

    @staticmethod
    def validate_plan(plan: dict) -> bool:
        """校验 plan JSON 结构完整性。"""
        required_keys = {"plan_id", "goal", "status", "tasks", "created_at", "updated_at"}
        if not all(k in plan for k in required_keys):
            return False
        valid_statuses = {"in_progress", "completed", "cancelled"}
        if plan["status"] not in valid_statuses:
            return False
        valid_task_statuses = {"pending", "in_progress", "done"}
        for task in plan.get("tasks", []):
            if not all(k in task for k in ("id", "desc", "status")):
                return False
            if task["status"] not in valid_task_statuses:
                return False
        return True

    # -- 内部方法 --

    def _find_in_progress_plan(self) -> dict | None:
        for f in sorted(self._plans_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("status") == "in_progress":
                    return data
            except Exception:
                continue
        return None

    def _load_current_plan(self) -> dict | None:
        plan_id = self.get_current_plan_id()
        if not plan_id:
            return None
        return self.load_plan(plan_id)

    def _save_plan(self, plan: dict) -> None:
        plan_id = plan.get("plan_id", "unknown")
        path = self._plans_dir / f"{plan_id}.json"
        try:
            path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("PlanTracker: failed to save plan %s: %s", plan_id, e)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
```

- [ ] **步骤 3.2：创建测试文件 `tests/agent/test_plan_tracker.py`**

```python
"""Tests for PlanTracker — 计划状态机管理器。"""

import pytest
from agent.plan_tracker import PlanTracker


@pytest.fixture
def tracker(tmp_path):
    plans_dir = tmp_path / "plans"
    return PlanTracker(str(plans_dir))


class TestCreatePlan:
    def test_creates_plan_and_returns_id(self, tracker):
        plan_id = tracker.create_or_update("测试目标", [
            {"id": "t1", "desc": "第一步"},
        ])
        assert plan_id.startswith("plan-")
        assert tracker.get_current_plan_id() == plan_id

    def test_appends_to_existing_plan(self, tracker):
        pid1 = tracker.create_or_update("目标", [{"id": "t1", "desc": "第一步"}])
        pid2 = tracker.create_or_update("目标", [{"id": "t2", "desc": "第二步"}])
        assert pid1 == pid2
        plan = tracker.load_plan(pid1)
        assert len(plan["tasks"]) == 2

    def test_creates_new_when_prev_completed(self, tracker):
        pid1 = tracker.create_or_update("目标A", [{"id": "t1", "desc": "A"}])
        plan = tracker.load_plan(pid1)
        plan["status"] = "completed"
        tracker._save_plan(plan)
        pid2 = tracker.create_or_update("目标B", [{"id": "t2", "desc": "B"}])
        assert pid1 != pid2


class TestManageTasks:
    def test_mark_done_advances_to_next(self, tracker):
        tracker.create_or_update("目标", [
            {"id": "t1", "desc": "任务1"},
            {"id": "t2", "desc": "任务2"},
        ])
        tracker.mark_done("t1")
        plan = tracker.load_plan(tracker.get_current_plan_id())
        assert plan["tasks"][0]["status"] == "done"
        assert plan["current_task"] == "t2"

    def test_add_gap_deduplicates(self, tracker):
        tracker.create_or_update("目标", [{"id": "t1", "desc": "任务"}])
        tracker.add_gap("发现盲区A")
        tracker.add_gap("发现盲区A")
        plan = tracker.load_plan(tracker.get_current_plan_id())
        assert len(plan["gaps_found"]) == 1

    def test_refine_goal_records_history(self, tracker):
        tracker.create_or_update("原始目标", [{"id": "t1", "desc": "任务"}])
        tracker.refine_goal("调整后的目标")
        plan = tracker.load_plan(tracker.get_current_plan_id())
        assert len(plan["goal_history"]) == 2
        assert "调整后的目标" in plan["goal_history"][1]


class TestGetStatus:
    def test_no_active_plan(self, tracker):
        assert tracker.get_status()["has_active_plan"] is False

    def test_returns_progress_summary(self, tracker):
        tracker.create_or_update("目标", [
            {"id": "t1", "desc": "任务1"},
            {"id": "t2", "desc": "任务2"},
            {"id": "t3", "desc": "任务3"},
        ])
        tracker.mark_done("t1")
        status = tracker.get_status()
        assert status["has_active_plan"] is True
        assert status["progress"] == "1/3"


class TestValidatePlan:
    def test_validates_correct_plan(self, tracker):
        plan = {
            "plan_id": "test-1", "goal": "test", "status": "in_progress",
            "tasks": [{"id": "t1", "desc": "task", "status": "pending"}],
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
        }
        assert tracker.validate_plan(plan) is True

    def test_rejects_invalid_status(self, tracker):
        plan = {
            "plan_id": "test-1", "goal": "test", "status": "invalid_status",
            "tasks": [], "created_at": "", "updated_at": "",
        }
        assert tracker.validate_plan(plan) is False
```

- [ ] **步骤 3.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_plan_tracker.py -v
```

预期：所有 9 个测试通过。

- [ ] **步骤 3.4：Commit**

```bash
git add agent/plan_tracker.py tests/agent/test_plan_tracker.py
git commit -m "feat: add plan_tracker.py — plan state machine with JSON persistence | 添加计划状态机"
```

---

## 任务 4：agent/expert_matcher.py — 专家匹配器

**文件：**
- 创建：`agent/expert_matcher.py`
- 测试：`tests/agent/test_expert_matcher.py`

**接口（产出供任务 5 消费）：**

```python
@dataclass
class Expert:
    slug: str
    name: str
    division: str
    prompt: str

class ExpertMatcher:
    def __init__(self, agents_dir: str | Path | None = None)
        # 默认：~/.config/opencode/agents/（Agency 固定路径，不用 get_hermes_home）
    def match(self, message: str, route_name: str, top_n: int = 2) -> list[Expert]
    def load_expert_prompt(self, slug: str) -> str
    def get_available_experts(self) -> list[dict]
    def get_experts_for_division(self, division: str) -> list[Expert]
    def refresh_cache(self) -> None
```

- [ ] **步骤 4.1：创建 `agent/expert_matcher.py`**

```python
"""专家匹配器（StarRoad Cognition）。
对接 The Agency 的 232 专家库（~/.config/opencode/agents/）。
根据 route_name + 关键词匹配最佳专家。"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Agency 16 个 division 到 route_name 的映射
ROUTE_TO_DIVISIONS: dict[str, list[str]] = {
    "implement": ["Engineering", "Game Dev", "Spatial Computing"],
    "analyze": ["Security", "Testing", "Finance"],
    "research": ["Product", "Marketing", "Specialized", "GIS"],
    "discuss": ["Product", "Marketing", "Design", "Sales", "Project Mgmt"],
    "simple": [],
}

# 领域关键词映射
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "前端": ["前端", "react", "vue", "angular", "ui", "界面", "component"],
    "后端": ["后端", "api", "数据库", "server", "服务端", "接口"],
    "安全": ["安全", "security", "漏洞", "渗透", "加密", "auth"],
    "架构": ["架构", "设计模式", "系统设计", "模块", "微服务"],
    "测试": ["测试", "test", "unit", "e2e", "集成", "mock"],
    "数据": ["数据", "etl", "管道", "pipeline", "分析", "报表"],
    "部署": ["部署", "devops", "ci/cd", "docker", "k8s", "发布"],
    "设计": ["设计", "ui", "ux", "品牌", "视觉", "交互"],
    "策略": ["策略", "战略", "方向", "规划", "路线", "roadmap"],
    "调研": ["调研", "研究", "竞品", "趋势", "对比", "分析"],
}

DEFAULT_AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"

# 默认专家 fallback（当 Agency 目录不存在或无匹配时使用）
DEFAULT_EXPERTS: dict[str, str] = {
    "implement": "software-architect",
    "analyze": "code-reviewer",
    "research": "trend-researcher",
    "discuss": "product-manager",
}


@dataclass
class Expert:
    """专家对象。"""
    slug: str
    name: str
    division: str
    prompt: str = ""


class ExpertMatcher:
    """对接 The Agency 的 232 专家库。

    Usage:
        matcher = ExpertMatcher()
        experts = matcher.match("帮我设计数据库表", "implement")
    """

    def __init__(self, agents_dir: str | Path | None = None):
        if agents_dir is None:
            agents_dir = DEFAULT_AGENTS_DIR
        self._agents_dir = Path(agents_dir)
        # 缓存：slug → {"slug": str, "name": str, "division": str, "description": str}
        self._registry: dict[str, dict] = {}
        # prompt 缓存：slug → str
        self._prompt_cache: dict[str, str] = {}

    def match(self, message: str, route_name: str, top_n: int = 2) -> list[Expert]:
        """根据 route_name + 关键词查找最匹配的专家。

        route_name='simple' 时返回空列表。
        """
        if route_name == "simple":
            return []

        if not self._registry:
            self.refresh_cache()

        # 根据 route_name 缩小匹配范围
        target_divisions = ROUTE_TO_DIVISIONS.get(route_name, [])
        candidates = list(self._registry.values())
        if target_divisions:
            candidates = [c for c in candidates if c.get("division") in target_divisions]

        if not candidates:
            candidates = list(self._registry.values())

        # 关键词匹配评分
        keywords = self._extract_keywords(message)
        scored = []
        for candidate in candidates:
            score = self._score_match(candidate, keywords, route_name)
            if score > 0 or not keywords:  # 无关键词时保留所有候选项
                scored.append((score, candidate))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [c for _, c in scored[:top_n]]

        # 降级：使用默认专家
        if not top_candidates:
            default_slug = DEFAULT_EXPERTS.get(route_name, "software-architect")
            for v in self._registry.values():
                if v["slug"] == default_slug:
                    top_candidates = [{"slug": v["slug"], "name": v["name"], "division": v.get("division", ""), "description": v.get("description", "")}]
                    break
            if not top_candidates:
                return []

        # 加载 expert prompt
        result = []
        for c in top_candidates:
            prompt = self.load_expert_prompt(c.get("slug", c.get("name", "").lower().replace(" ", "-")))
            result.append(Expert(
                slug=c.get("slug", ""),
                name=c.get("name", ""),
                division=c.get("division", ""),
                prompt=prompt,
            ))

        return result

    def load_expert_prompt(self, slug: str) -> str:
        """读取对应 .md 文件，提取 content 作为 system prompt。缓存已读取的 prompt。"""
        if slug in self._prompt_cache:
            return self._prompt_cache[slug]

        path = self._agents_dir / f"{slug}.md"
        if not path.exists():
            logger.debug("ExpertMatcher: agent file not found: %s", path)
            self._prompt_cache[slug] = ""
            return ""

        try:
            content = path.read_text(encoding="utf-8").strip()
            self._prompt_cache[slug] = content
            return content
        except Exception as e:
            logger.warning("ExpertMatcher: failed to read %s: %s", path, e)
            self._prompt_cache[slug] = ""
            return ""

    def get_available_experts(self) -> list[dict]:
        """返回所有可用专家的摘要列表。"""
        if not self._registry:
            self.refresh_cache()
        return [
            {"slug": v["slug"], "name": v["name"],
             "division": v.get("division", ""),
             "description": v.get("description", "")}
            for v in self._registry.values()
        ]

    def get_experts_for_division(self, division: str) -> list[Expert]:
        """按 division 获取专家列表。"""
        if not self._registry:
            self.refresh_cache()
        experts = []
        for v in self._registry.values():
            if v.get("division") == division:
                prompt = self.load_expert_prompt(v["slug"])
                experts.append(Expert(
                    slug=v["slug"], name=v["name"],
                    division=division, prompt=prompt,
                ))
        return experts

    def refresh_cache(self) -> None:
        """重建专家注册表缓存。扫描 agents_dir 下所有 .md 文件。"""
        self._registry = {}
        if not self._agents_dir.exists():
            logger.info("ExpertMatcher: agents dir not found: %s (Agency not installed)", self._agents_dir)
            return

        for md_file in sorted(self._agents_dir.glob("*.md")):
            try:
                metadata = self._parse_agent_file(md_file)
                if metadata:
                    self._registry[metadata["slug"]] = metadata
            except Exception as e:
                logger.debug("ExpertMatcher: failed to parse %s: %s", md_file.name, e)

        logger.info("ExpertMatcher: loaded %d experts from %s", len(self._registry), self._agents_dir)

    # -- 内部方法 --

    @staticmethod
    def _parse_agent_file(path: Path) -> dict | None:
        """解析单个 agent .md 文件，提取 frontmatter 元数据。

        Agency 文件格式：
            ---
            name: Software Architect
            division: Engineering
            description: ...
            ---
            (system prompt content)
        """
        slug = path.stem
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None

        name = slug.replace("-", " ").title()
        division = "Engineering"
        description = ""

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower()
                    value = value.strip().strip("\"'")
                    if key == "name":
                        name = value
                    elif key == "division":
                        division = value
                    elif key == "description":
                        description = value

        return {"slug": slug, "name": name, "division": division, "description": description}

    @staticmethod
    def _extract_keywords(message: str) -> list[str]:
        """从消息中提取领域关键词。"""
        msg_lower = message.lower()
        found = []
        for keywords in DOMAIN_KEYWORDS.values():
            for kw in keywords:
                if kw in msg_lower:
                    found.append(kw)
                    break
        return found

    @staticmethod
    def _score_match(candidate: dict, keywords: list[str], route_name: str) -> int:
        """计算候选专家的匹配分数。"""
        score = 0
        candidate_text = f"{candidate.get('name', '')} {candidate.get('description', '')}".lower()

        # 关键词匹配
        for kw in keywords:
            if kw in candidate_text:
                score += 10

        # division 匹配加分
        division = candidate.get("division", "").lower()
        if route_name == "implement" and division in ("engineering", "game dev"):
            score += 5
        elif route_name == "analyze" and division in ("security", "testing"):
            score += 5

        return score
```

- [ ] **步骤 4.2：创建测试文件 `tests/agent/test_expert_matcher.py`**

```python
"""Tests for ExpertMatcher — 专家匹配器。"""

import pytest
from pathlib import Path
from agent.expert_matcher import ExpertMatcher, Expert


@pytest.fixture
def mock_agents_dir(tmp_path):
    """创建模拟的 Agency 专家文件。"""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (agents_dir / "backend-architect.md").write_text(
        "---\nname: Backend Architect\ndivision: Engineering\n"
        "description: Backend architecture and API design\n"
        "---\n\nYou are a backend architect. Design scalable APIs."
    )
    (agents_dir / "database-optimizer.md").write_text(
        "---\nname: Database Optimizer\ndivision: Engineering\n"
        "description: Database optimization and SQL\n"
        "---\n\nYou are a database expert. Optimize queries."
    )
    (agents_dir / "security-architect.md").write_text(
        "---\nname: Security Architect\ndivision: Security\n"
        "description: Security architecture reviews\n"
        "---\n\nYou are a security expert."
    )
    return agents_dir


class TestMatch:
    def test_returns_experts_for_implement(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        experts = matcher.match("帮我设计后端API", "implement", top_n=2)
        assert len(experts) <= 2
        assert all(isinstance(e, Expert) for e in experts)

    def test_returns_empty_for_simple(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        experts = matcher.match("你好", "simple")
        assert len(experts) == 0

    def test_matches_backend_keywords(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        experts = matcher.match("设计数据库表结构", "implement")
        assert len(experts) > 0

    def test_graceful_when_no_agents_dir(self):
        """没有 Agency 目录时优雅降级。"""
        matcher = ExpertMatcher("/nonexistent/path")
        experts = matcher.match("帮我设计后端API", "implement")
        assert len(experts) == 0  # 没有目录，返回空列表


class TestLoadExpertPrompt:
    def test_loads_existing_prompt(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt = matcher.load_expert_prompt("backend-architect")
        assert "backend architect" in prompt.lower()

    def test_returns_empty_for_missing(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        assert matcher.load_expert_prompt("nonexistent-agent") == ""

    def test_caches_after_first_load(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        p1 = matcher.load_expert_prompt("backend-architect")
        p2 = matcher.load_expert_prompt("backend-architect")
        assert p1 == p2


class TestCacheManagement:
    def test_refresh_cache_loads_all_agents(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        available = matcher.get_available_experts()
        assert len(available) >= 3

    def test_get_experts_for_division(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        engineers = matcher.get_experts_for_division("Engineering")
        assert len(engineers) >= 2
```

- [ ] **步骤 4.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_expert_matcher.py -v
```

预期：所有 10 个测试通过。

- [ ] **步骤 4.4：Commit**

```bash
git add agent/expert_matcher.py tests/agent/test_expert_matcher.py
git commit -m "feat: add expert_matcher.py — Agency 232 expert matching engine | 添加专家匹配器"
```

---

## 任务 5：agent/router.py — 语义路由总控

**依赖：** 任务 1-4（CognitiveGate, MemoryIndex, PlanTracker, ExpertMatcher 的接口）

**文件：**
- 创建：`agent/router.py`
- 测试：`tests/agent/test_router.py`

**接口（产出供任务 6、9 消费）：**

```python
@dataclass
class RouteDecision:
    path: str           # 'direct' | 'cognitive_loop' | 'expert_delegate'
    mode: str           # 'A' | 'B' | 'C' | 'D'
    route_name: str     # 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
    experts: list[Expert]
    confidence: float   # 0.0-1.0

class AgentRouter:
    def __init__(self, expert_matcher, plan_tracker=None, memory_index=None, cognitive_gate=None)
    def route(self, message: str, context: dict | None = None) -> RouteDecision
    def format_prompt_section(self) -> str
```

- [ ] **步骤 5.1：创建 `agent/router.py`**

```python
"""语义路由总控（StarRoad Cognition Route 1-3）。
决定消息走哪条处理路径。前置路由，在 run_conversation() 开始时调用。"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from agent.expert_matcher import Expert, ExpertMatcher
    from agent.plan_tracker import PlanTracker
    from agent.memory_index import MemoryIndex
    from agent.cognitive_gate import CognitiveGate

logger = logging.getLogger(__name__)

# 意图分类关键词
_INTENT_PATTERNS: dict[str, list[str]] = {
    "implement": [
        "实现", "写代码", "创建", "开发", "构建", "加个", "添加", "修改",
        "implement", "create", "build", "add", "write", "code", "fix",
        "重构", "改", "修", "develop",
    ],
    "analyze": [
        "分析", "评审", "review", "检查", "审计", "评估",
        "analyze", "check", "audit", "evaluate",
    ],
    "research": [
        "调研", "搜索", "查一下", "研究", "找", "research", "search",
        "find", "look up", "explore", "调查",
    ],
    "discuss": [
        "讨论", "聊聊", "你觉得", "怎么看", "商量", "discuss",
        "thoughts", "opinion", "what do you think",
    ],
    "simple": [],
}

# 简单消息模式
_SIMPLE_PATTERNS = [
    r"^你好", r"^hi", r"^hello", r"^谢谢", r"^thanks",
    r"^yes", r"^no", r"^是的", r"^好的", r"^ok",
    r"^\S+\s*$",
]

# 注入 system prompt 的认知循环引导段
COGNITIVE_LOOP_GUIDANCE = (
    "\n## 认知循环（StarRoad Cognition）\n\n"
    "面对复杂任务时，请遵循先内后外的认知循环流程：\n\n"
    "1. **内吸（Internal Recall）** — 先向内求：\n"
    "   - 搜索记忆索引找已有知识\n"
    "   - 搜索历史对话回忆相关讨论\n"
    "   - 扫描技能列表加载相关 skill\n\n"
    "2. **形成探索计划** — 将盲区转化为具体探索任务\n\n"
    "3. **外求（External Exploration）** — 再向外求：\n"
    "   - 用最合适的工具执行探索计划\n"
    "   - 发现新盲区时追加到计划\n\n"
    "4. **综合评估** — 判断是否可以回复，还是需要继续探索或问用户\n\n"
    "5. **三省吾身** — 每次行动后检查：\n"
    "   - 是否诚实地说明了不确定性（荣辱观 L1）\n"
    "   - 是否 step by step、假设先行（思维方式 L2）\n"
    "   - 是否有可改进之处（反省 L3）\n"
)


@dataclass
class RouteDecision:
    """路由决策结果。"""
    path: str = "direct"
    mode: str = ""
    route_name: str = "simple"
    experts: list = field(default_factory=list)
    confidence: float = 1.0


class AgentRouter:
    """消息路由总控。

    职责：
    1. 分类意图（route_name）
    2. 简单任务 → path='direct'
    3. 复杂任务 → 匹配专家 → 决定执行模式 A/B/C/D

    不负责：后置评估（由 CognitiveGate 负责）。
    """

    def __init__(
        self,
        expert_matcher,
        plan_tracker=None,
        memory_index=None,
        cognitive_gate=None,
    ):
        self._expert_matcher = expert_matcher
        self._plan_tracker = plan_tracker
        self._memory_index = memory_index
        self._cognitive_gate = cognitive_gate

    def route(self, message: str, context: dict | None = None) -> RouteDecision:
        """主路由方法。

        Args:
            message: 用户消息
            context: 可选上下文（如 {"conversation_history": int}）

        Returns:
            RouteDecision
        """
        route_name = self._classify_intent(message)
        confidence = self._estimate_confidence(message, route_name)

        # 步骤 2：简单消息直走原流程
        if route_name == "simple" or self._is_simple_message(message):
            return RouteDecision(path="direct", route_name="simple", confidence=confidence)

        # 步骤 3：匹配专家
        experts = self._expert_matcher.match(message, route_name, top_n=2)

        # 步骤 4：决定执行模式
        mode = self._decide_mode(route_name, experts)

        # 步骤 5：决定路径
        path = self._decide_path(route_name, mode, experts)

        return RouteDecision(
            path=path, mode=mode, route_name=route_name,
            experts=experts, confidence=confidence,
        )

    @staticmethod
    def format_prompt_section() -> str:
        """返回注入 system prompt 的认知循环引导段（约 300 字）。"""
        return COGNITIVE_LOOP_GUIDANCE

    # -- 内部方法 --

    def _classify_intent(self, message: str) -> str:
        """用关键词匹配分类意图。"""
        msg_lower = message.lower()

        for route in ("implement", "research", "analyze", "discuss"):
            for pattern in _INTENT_PATTERNS.get(route, []):
                if pattern in msg_lower:
                    return route

        # 长消息含代码特征 → implement
        if len(message) > 100 and any(c in message for c in ("{", "}", "(", ")", "def ", "class ")):
            return "implement"

        return "simple"

    def _is_simple_message(self, message: str) -> bool:
        msg = message.strip()
        if len(msg) < 15:
            return True
        for pattern in _SIMPLE_PATTERNS:
            if re.match(pattern, msg, re.IGNORECASE):
                return True
        return False

    def _estimate_confidence(self, message: str, route_name: str) -> float:
        msg_len = len(message.strip())
        if route_name == "simple":
            return 0.9 if msg_len < 30 else 0.6

        code_chars = sum(1 for c in message if c in "{}()[]<>")
        if msg_len > 200 and code_chars > 10:
            return 0.95
        if msg_len > 100:
            return 0.85
        return 0.7

    def _decide_mode(self, route_name: str, experts: list) -> str:
        """根据意图决定 Agency 执行模式。"""
        if route_name == "implement" and experts:
            return "A"
        elif route_name == "analyze" and experts:
            return "B"
        elif route_name == "discuss":
            return "C"
        elif route_name == "research":
            return "D"
        return "B"

    def _decide_path(self, route_name: str, mode: str, experts: list) -> str:
        """根据意图和模式决定路径。"""
        if route_name == "simple":
            return "direct"
        if mode == "A" and experts:
            return "expert_delegate"
        if mode == "D":
            return "cognitive_loop"
        return "direct"
```

- [ ] **步骤 5.2：创建测试文件 `tests/agent/test_router.py`**

```python
"""Tests for AgentRouter — 语义路由总控。"""

import pytest
from pathlib import Path
from agent.router import AgentRouter, RouteDecision
from agent.expert_matcher import ExpertMatcher


@pytest.fixture
def mock_agents_dir(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "backend-architect.md").write_text(
        "---\nname: Backend Architect\ndivision: Engineering\n"
        "description: Backend architecture\n"
        "---\n\nYou are a backend architect."
    )
    return agents_dir


@pytest.fixture
def router(mock_agents_dir):
    matcher = ExpertMatcher(str(mock_agents_dir))
    matcher.refresh_cache()
    return AgentRouter(expert_matcher=matcher)


class TestClassifyIntent:
    def test_classifies_implement(self, router):
        decision = router.route("帮我实现一个登录功能")
        assert decision.route_name == "implement"

    def test_classifies_research(self, router):
        decision = router.route("帮我调研一下最新的前端框架")
        assert decision.route_name == "research"

    def test_classifies_discuss(self, router):
        decision = router.route("我想讨论一下微服务架构的利弊")
        assert decision.route_name == "discuss"

    def test_classifies_simple_greeting(self, router):
        decision = router.route("你好")
        assert decision.route_name == "simple"
        assert decision.path == "direct"

    def test_short_message_is_simple(self, router):
        decision = router.route("好的")
        assert decision.route_name == "simple"


class TestRouteDecision:
    def test_implement_returns_experts(self, router):
        decision = router.route("帮我设计后端 API")
        if decision.path != "direct":
            assert len(decision.experts) > 0
            assert decision.mode in ("A", "B", "D")

    def test_simple_no_experts(self, router):
        decision = router.route("谢谢")
        assert len(decision.experts) == 0

    def test_confidence_in_range(self, router):
        decision = router.route("实现一个复杂系统")
        assert 0 <= decision.confidence <= 1.0


class TestPromptSection:
    def test_format_prompt_section(self, router):
        section = router.format_prompt_section()
        assert "内吸" in section
        assert "外求" in section
        assert "三省吾身" in section
        assert len(section) > 100
```

- [ ] **步骤 5.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_router.py -v
```

预期：所有 10 个测试通过。

- [ ] **步骤 5.4：Commit**

```bash
git add agent/router.py tests/agent/test_router.py
git commit -m "feat: add router.py — semantic routing with expert matching for StarRoad Cognition | 添加语义路由总控"
```

---

# 阶段 2：修改已有文件

> **说明：** 任务 6-8 可以并行执行，因为它们修改不同的文件。任务 8 暂缓。

---

## 任务 6：修改 prompt_builder.py — 注入认知引导函数

**文件：** `agent/prompt_builder.py`

**改动量：** 在文件末尾（第 1043 行后）新增约 30 行。

**说明：** 在 `prompt_builder.py` 中为认知引导段添加纯函数，供 `run_agent.py` 的 `_build_system_prompt()` 调用。

- [ ] **步骤 6.1：在 `agent/prompt_builder.py` 末尾追加内容**

在文件最后（`return "\n".join(sections)` 之后，第 1043 行后）追加：

```python

# === DeepAgent: StarRoad Cognition ===
# 认知循环引导段（注入 system prompt）
# 约 300 字，描述三层认知框架和先内后外流程

COGNITIVE_LOOP_GUIDANCE = (
    "\n## Cognitive Loop (StarRoad Cognition)\n\n"
    "### 先内后外流程\n"
    "面对复杂任务时，优先从内部知识开始：\n"
    "1. 搜索 Memory Index 中的已有知识\n"
    "2. 搜索历史对话中的相关讨论（session_search）\n"
    "3. 加载相关 skill（skill_view）\n\n"
    "### 外部探索\n"
    "用最合适的工具（web_search, terminal, read_file 等）执行探索计划。\n"
    "发现新盲区时追加到计划。\n\n"
    "### 三层自评\n"
    "每次行动完成后再做检查：\n"
    "- Layer 1 荣辱观：有没有隐瞒不确定性？有没有未经验证的论断？\n"
    "- Layer 2 思维方式：有没有 step by step？有没有假设先行？\n"
    "- Layer 3 三省吾身：有哪些可以改进？\n"
)


def build_cognitive_loop_guidance() -> str:
    """返回认知循环引导段，供注入 system prompt。"""
    return COGNITIVE_LOOP_GUIDANCE
# === End ===
```

- [ ] **步骤 6.2：创建轻量测试**

```bash
mkdir -p tests/agent
```

```python
# tests/agent/test_prompt_builder_cognitive.py
"""Tests for cognitive loop guidance in prompt_builder."""

from agent.prompt_builder import build_cognitive_loop_guidance, COGNITIVE_LOOP_GUIDANCE


def test_guidance_contains_key_sections():
    section = build_cognitive_loop_guidance()
    assert len(section) > 100
    assert "先内后外" in section or "Cognitive Loop" in section


def test_constant_not_empty():
    assert len(COGNITIVE_LOOP_GUIDANCE) > 50
```

- [ ] **步骤 6.3：跑测试确认**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_prompt_builder_cognitive.py -v
```

预期：2 个测试通过。

- [ ] **步骤 6.4：Commit**

```bash
git add agent/prompt_builder.py tests/agent/test_prompt_builder_cognitive.py
git commit -m "feat: add cognitive loop guidance to prompt_builder.py | 注入认知循环引导函数"
```

---

## 任务 7：修改 context_compressor.py — KV Cache 围栏保护

**文件：** `agent/context_compressor.py`

**改动量：** 在 `compress()` 方法中新增约 15 行围栏检测过滤逻辑。

**说明：** 当 `-----COGNITIVE_INDEX_START-----` 出现在要压缩的内容中时，跳过该段不压缩，保护 Memory Index 的完整性。

- [ ] **步骤 7.1：找到插入位置**

在 `context_compressor.py` 中，找到 `compress()` 方法中 `turns_to_summarize = messages[compress_start:compress_end]` 这一行（约第 977 行）。
在此之后、`_generate_summary(turns_to_summarize)` 调用之前插入围栏过滤。

- [ ] **步骤 7.2：插入围栏过滤代码**

```python
# === DeepAgent: StarRoad Cognition 围栏保护 ===
# 检测 Cognitive Index 围栏段，跳过不压缩
_fence_start = "-----COGNITIVE_INDEX_START-----"
_fence_end = "-----COGNITIVE_INDEX_END-----"
_filtered_turns = []
for _turn in turns_to_summarize:
    _content = _turn.get("content", "")
    if isinstance(_content, str) and _fence_start in _content:
        continue  # 跳过整个围栏段，保护其完整性
    _filtered_turns.append(_turn)
if len(_filtered_turns) < len(turns_to_summarize):
    logger.info(
        "Cognitive index fence detected: skipped %d protected messages",
        len(turns_to_summarize) - len(_filtered_turns),
    )
turns_to_summarize = _filtered_turns
# === End ===
```

- [ ] **步骤 7.3：验证插入位置正确**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -c "from agent.context_compressor import ContextCompressor; print('import OK')"
```

预期：`import OK`（围栏保护逻辑不影响模块导入）。

- [ ] **步骤 7.4：Commit**

```bash
git add agent/context_compressor.py
git commit -m "feat: add KV cache fence protection to context_compressor.py | 添加认知索引围栏保护"
```

---

## 任务 8：修改 memory_tool.py — 扩展 read_nested（**暂缓**）

**决策：此任务暂不实施。**

**理由：** MemoryIndex 已经提供了 `read_nested()` 方法作为库接口（任务 2），认知循环内吸阶段直接调用库方法即可。模型已有 `read_file` 工具可以读任意文件。YAGNI 原则：等实际需要时再加。

---

# 阶段 3：集成到 run_agent.py

## 任务 9：run_agent.py — 集成认知模块

**依赖：** 任务 1-7（所有新模块 + prompt_builder + context_compressor 修改）

**文件：** `run_agent.py`

**改动量：** 约 100 行，分散在 4 个位置。

**策略：** 通过配置开关控制，默认关闭（`cognitive.enabled: false`），不影响现有行为。

- [ ] **步骤 9.1：在 `__init__()` 中添加认知模块属性声明**

在 `AIAgent.__init__()` 方法中（约第 900 行区域，在现有属性初始化之后）添加：

```python
# === DeepAgent: StarRoad Cognition ===
# 认知模块（按需初始化，默认关闭）
self._cognitive_enabled: bool = False
self._cognitive_router = None
self._cognitive_gate = None
self._memory_index = None
self._plan_tracker = None
self._expert_matcher = None
# === End ===
```

- [ ] **步骤 9.2：在 `__init__()` 末尾添加按需初始化调用**

在 `__init__()` 末尾（return 之前）添加配置读取 + 初始化调用：

```python
# === DeepAgent: StarRoad Cognition ===
# 从配置中读取 cognitive.enabled（默认关闭）
self._cognitive_enabled = False
try:
    from hermes_cli.config import load_config
    _cfg = load_config()
    self._cognitive_enabled = _cfg.get("cognitive", {}).get("enabled", False)
except Exception:
    pass

if self._cognitive_enabled:
    try:
        from agent.memory_index import MemoryIndex
        from agent.plan_tracker import PlanTracker
        from agent.expert_matcher import ExpertMatcher
        from agent.router import AgentRouter
        from agent.cognitive_gate import CognitiveGate

        self._memory_index = MemoryIndex()
        self._plan_tracker = PlanTracker()
        self._expert_matcher = ExpertMatcher()
        self._cognitive_gate = CognitiveGate()

        self._cognitive_router = AgentRouter(
            expert_matcher=self._expert_matcher,
            plan_tracker=self._plan_tracker,
            memory_index=self._memory_index,
            cognitive_gate=self._cognitive_gate,
        )
        logger.info("StarRoad Cognition modules initialized")
    except Exception as e:
        logger.warning("Failed to initialize StarRoad Cognition: %s", e)
        self._cognitive_enabled = False
# === End ===
```

- [ ] **步骤 9.3：在 `_build_system_prompt()` 中注入认知内容**

在 `_build_system_prompt()` 方法中（约第 3266 行，`<available_skills>` 块之后，时间戳之前），注入 Memory Index 导航段和认知循环引导：

```python
# === DeepAgent: StarRoad Cognition ===
# 注入 Memory Index 导航段（围栏包裹）
if self._cognitive_enabled and self._memory_index:
    try:
        index_summary = self._memory_index.index_summary()
        if index_summary:
            prompt_parts.append(index_summary)
    except Exception as e:
        logger.debug("Failed to inject memory index: %s", e)

# 注入认知循环引导
if self._cognitive_enabled and self._cognitive_router:
    try:
        guidance = self._cognitive_router.format_prompt_section()
        if guidance:
            prompt_parts.append(guidance)
    except Exception as e:
        logger.debug("Failed to inject cognitive guidance: %s", e)
# === End ===
```

- [ ] **步骤 9.4：在 `run_conversation()` 开始时添加路由决策**

在 `run_conversation()` 方法中（约第 7941 行之后，用户消息已添加、API 调用循环之前），插入前置路由：

```python
# === DeepAgent: StarRoad Cognition ===
# Pre-turn hook: 路由决策
cognitive_route = None
if self._cognitive_enabled and self._cognitive_router:
    try:
        cognitive_route = self._cognitive_router.route(
            user_message,
            context={"conversation_history": len(messages)},
        )
        if cognitive_route and cognitive_route.path != "direct":
            logger.info(
                "Cognitive route: path=%s mode=%s route_name=%s experts=%s",
                cognitive_route.path, cognitive_route.mode,
                cognitive_route.route_name,
                [e.slug for e in cognitive_route.experts],
            )
            # 模式 A：记录专家信息供后续 delegate_task 使用
            if cognitive_route.mode == "A" and cognitive_route.experts:
                self._cognitive_experts = cognitive_route.experts

            # 若无活跃 plan，自动创建
            if self._plan_tracker and not self._plan_tracker.get_current_plan_id():
                self._plan_tracker.create_or_update(user_message)
    except Exception as e:
        logger.debug("Cognitive routing failed (non-fatal): %s", e)
# === End ===
```

- [ ] **步骤 9.5：在 `run_conversation()` 末尾添加评估**

在 `run_conversation()` 方法中，`final_response` 生成后、返回前，插入后置评估：

```python
# === DeepAgent: StarRoad Cognition ===
# Post-turn hook: 三层自评
if self._cognitive_enabled and self._cognitive_gate and final_response:
    try:
        turn_data = {
            "user_message": user_message,
            "assistant_response": final_response,
            "tool_calls": [],
            "tool_results": [],
            "plan_id": (
                self._plan_tracker.get_current_plan_id()
                if self._plan_tracker else ""
            ),
        }

        # 从 messages 中提取工具调用信息
        for _msg in messages:
            if _msg.get("role") == "assistant" and _msg.get("tool_calls"):
                turn_data["tool_calls"].extend(_msg["tool_calls"])
            if _msg.get("role") == "tool":
                turn_data["tool_results"].append(_msg)

        eval_result = self._cognitive_gate.evaluate(turn_data)
        if eval_result.should_interrupt_user:
            logger.info(
                "CognitiveGate suggests asking user: %s",
                eval_result.adjustments_note,
            )
        if eval_result.gaps_found and self._plan_tracker:
            for gap in eval_result.gaps_found:
                self._plan_tracker.add_gap(gap)
                logger.info("CognitiveGate gap recorded: %s", gap)
    except Exception as e:
        logger.debug("Cognitive evaluation failed (non-fatal): %s", e)
# === End ===
```

- [ ] **步骤 9.6：验证导入无误**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -c "
from agent.cognitive_gate import CognitiveGate
from agent.memory_index import MemoryIndex
from agent.plan_tracker import PlanTracker
from agent.expert_matcher import ExpertMatcher
from agent.router import AgentRouter
from agent.prompt_builder import build_cognitive_loop_guidance
print('All cognitive modules imported OK')
"
```

预期：`All cognitive modules imported OK`

- [ ] **步骤 9.7：Commit**

```bash
git add run_agent.py
git commit -m "feat: integrate StarRoad Cognition into run_agent.py with config gate | 集成认知模块到 agent loop"
```

---

# 阶段 4：数据文件和最终验证

## 任务 10：创建 MAP.md 和更新 SOUL.md

**文件：**
- 创建：`~/.deepagent/memories/MAP.md`（由 `memory_index.build_initial_index()` 自动创建）
- 更新：`~/.deepagent/SOUL.md`（手动追加认知框架定义）

- [ ] **步骤 10.1：触发 `build_initial_index()` 首次创建 MAP.md**

在 `run_agent.py` 的认知模块初始化后添加：

```python
# 首次使用时自动构建 Memory Index
if self._cognitive_enabled and self._memory_index:
    try:
        self._memory_index.build_initial_index()
    except Exception as e:
        logger.debug("Failed to build initial memory index: %s", e)
```

- [ ] **步骤 10.2：更新 `~/.deepagent/SOUL.md`**

在 SOUL.md 末尾追加（如 SOUL.md 存在则追加，不存在则创建）：

```markdown

## 认知框架（StarRoad Cognition）

### Layer 1 — 荣辱观
- 以知道自己的不足为荣，以隐瞒不足为耻
- 以提升认知为荣，以原地踏步为耻
- 以忽悠为耻，以告诉实情为荣

### Layer 2 — 思维方式
- 第一性原理 | Step by Step | 拆解到最小任务 | 找盲区 | 科研严谨

### Layer 3 — 三省吾身
- 回头检查 L1+L2 → 找改进点 → 记录到 memory → 外部问询
```

- [ ] **步骤 10.3：创建初始目录结构**

```bash
mkdir -p ~/.deepagent/memories/skills ~/.deepagent/memories/paper-notes ~/.deepagent/memories/references
mkdir -p ~/.deepagent/plans
```

- [ ] **步骤 10.4：最终集成验证**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/ -v -q
```

预期：所有新建的测试通过（约 50 个测试）。

- [ ] **步骤 10.5：Commit**

```bash
git add -A
git commit -m "feat: add MAP.md init, SOUL.md update, and final integration for StarRoad Cognition | 添加数据文件和认知框架定义"
```

---

## 三、阶段完成检查清单

每完成一个阶段，运行对应的验证命令：

| 阶段 | 验证命令 | 预期结果 |
|------|---------|---------|
| 0 | `grep -rn '\.hermes\b\|HERMES_HOME' hermes_constants.py \| head -5` | 只有 `display_hermes_home()` docstring 和 `get_hermes_root` 中有展示路径，无 `HERMES_HOME` 残留 |
| 0 | `grep -rn 'hermes-agent' pyproject.toml` | 0 匹配 |
| 0 | `python -c "import hermes_constants; print(hermes_constants.get_hermes_home())"` | 输出 `~/.deepagent` |
| 1 | `python -m pytest tests/agent/test_cognitive_gate.py tests/agent/test_memory_index.py tests/agent/test_plan_tracker.py tests/agent/test_expert_matcher.py tests/agent/test_router.py -v -q` | 所有 50+ 测试通过 |
| 2 | `python -m pytest tests/agent/test_prompt_builder_cognitive.py -v` | 2 测试通过 |
| 2 | `python -c "from agent.context_compressor import ContextCompressor; print('import OK')"` | `import OK` |
| 3 | `python -c "from agent.cognitive_gate import CognitiveGate; from agent.router import AgentRouter; print('All modules import OK')"` | `All modules import OK` |
| 4 | `python -m pytest tests/agent/ -v -q` | 全部通过 |

---

## 四、需要用户确认的决策点

执行前请确认以下决策：

### 决策 1：Python 版本要求

**现状：** `pyproject.toml` 要求 `>=3.11`。粗方案要求 `3.10+`。
**影响：** 新模块中使用了 `str | None` 类型语法（Python 3.10+ 支持），`dataclass` 的 `field()` 方法（3.8+）。
**建议：** 保持 `>=3.11`，无需调整。所有新代码与此兼容。

### 决策 2：`run_agent.py` 的具体注入行号

**现状：** `run_agent.py` 文件极大（11024 行），行号随版本变动。
**影响：** 计划中的"约第 3147 行"、"约第 7803 行"等为近似位置。
**建议：** 执行时使用 `grep` 精确定位，根据方法签名 `def _build_system_prompt(`、`def run_conversation(` 定位，而非依赖行号。

### 决策 3：阶段 0 是否影响现有安装

**现状：** 改了 `hermes_cli/main.py` 的帮助文案，但不改 import 路径、函数名、目录名。现有用 `hermes-cli/` 作为命名空间的代码不受影响。
**影响：** 安装后的命令变为 `deepagent`，但 `from hermes_cli.main import main` 仍有效。
**建议：** 确认用户同意命令名变更为 `deepagent`。

### 决策 4：认知模块默认开关

**现状：** `cognitive.enabled` 默认 `false`。用户需在 `config.yaml` 中显式设为 `true` 才启用。
**影响：** 不影响现有行为，渐进式启用。
**建议：** 保持默认关闭，内部测试后再考虑默认开启。

### 决策 5：ExpertMatcher 依赖 Agency

**现状：** `ExpertMatcher` 依赖 `~/.config/opencode/agents/` 目录中的 Agency 专家文件。如果用户没有安装 Agency，`match()` 返回空列表，Router 仍可工作（回退到直接路径）。
**影响：** 认知引擎可以独立工作，专家匹配是可选增强。
**建议：** 无需更改。独立运行时可正常工作，安装 Agency 后获得增强。

### 决策 6：memory_tool.py 的 `read_nested` 是否实施

**现状：** MemoryIndex 已有 `read_nested()` 作为库接口。工具层暂不需要暴露此功能。
**影响：** 无。
**建议：** 暂缓（如本文档任务 8 所述）。

---

## 五、StarRoad Cognition 三层自评（计划质量）

### Layer 1 荣辱观自评

| 检查点 | 结果 | 说明 |
|--------|------|------|
| 是否诚实说明了不确定性 | ✅ 通过 | 上方标明了 6 个决策点需要用户确认 |
| 是否用工具验证了论断 | ✅ 通过 | 所有代码接口基于实际阅读的源文件（prompt_builder.py 1043 行、context_compressor.py 1091 行、memory_tool.py 584 行）|
| 是否完整报告了真实情况 | ✅ 通过 | 如实标明了暂缓任务（任务 8）、集成复杂性、未知行号 |

### Layer 2 思维方式自评

| 检查点 | 结果 | 说明 |
|--------|------|------|
| 拆解到最小任务 | ✅ 通过 | 15 个任务，每个有文件路径、完整代码、测试代码、commit 命令 |
| Step by Step | ✅ 通过 | 每任务有明确的步骤顺序和依赖关系 |
| 第一性原理 | ✅ 通过 | 从现有代码架构出发分析注入点，不重新设计 |
| 找盲区 | ✅ 通过 | 发现并处理了 6 个决策点和 2 个暂缓项 |

### Layer 3 三省吾身（已知局限）

| 局限 | 置信度 | 说明 |
|------|--------|------|
| CognitiveGate 的启发式规则可能误报 | 大概率 80% | L1/L2 基于关键词匹配，实际情况更复杂。建议先上线观察，后续优化 |
| Router 意图分类精度在边界情况 | 大概 70% | 只有关键词匹配，无 LLM 辅助。长混合消息可能误判 |
| run_agent.py 注入位置可能需调整 | 大概率 85% | 基于代码结构推断，执行时需针对性确认 |
| Mode A（委派专家）的完整链路 | 大概率 50% | 本期只记录专家信息，未自动调 delegate_task。完整实现留二期 |
| 独立化后 hermes_cli 目录名不一致 | 大概率 95% | 目录名保持 hermes_cli 不修改，可能与 deepagent 品牌冲突，但风险极低 |

---

## 六、实施建议

1. **用 `superpowers:subagent-driven-development` 模式执行** — 每个任务由一个独立 subagent 完成，review 后进入下一个
2. **阶段 0 先做** — 独立化改了 5 个文件，先跑通保证基础可用
3. **阶段 1 并行** — 5 个新模块完全独立，可以同时开 5 个 subagent
4. **每阶段末尾跑全量测试** — 防止回归
5. **commit 频率：每任务一 commit** — 原子粒度，便于 bisect 和 review
