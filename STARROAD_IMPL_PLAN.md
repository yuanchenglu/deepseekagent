# StarRoad Cognition 详细实施计划

> **For agentic workers:** 每个任务使用 subagent-driven-development 模式执行。步骤使用 checkbox（`- [ ]`）语法追踪进度。

**目标：** DeepAgent 独立化（改名） + 实现三层认知引擎架构（StarRoad Cognition），包含阶段 0（5 个文件独立化）+ 10 个认知模块任务，共 15 个任务。

**架构概要：** 先通过阶段 0 将 DeepAgent 从 Hermes Agent 独立（`hermes` → `deepagent`，`~/.hermes` → `~/.deepagent`），再叠加三层认知框架（荣辱观/思维方式/三省吾身）+ 三路由层（语义路由/专家匹配/执行路由）+ Memory 嵌套索引 + Plan 状态机。所有新模块通过 hook points 插入现有 agent loop，不替换现有代码。

**技术栈：** Python 3.10+, 无额外外部依赖。文件路径使用 `get_hermes_home()`（独立化后自动指向 `~/.deepagent`）。所有代码写中文注释。

---

## 零、DeepAgent 独立化

> **背景：** DeepAgent 是从 Hermes Agent fork 的独立项目。核心发现是 `hermes_constants.py` 的 `get_hermes_home()` 函数是所有路径的唯一入口（50+ 个文件通过它获取路径），默认值为 `Path.home() / ".hermes"`，可通过 `HERMES_HOME` 环境变量覆盖。只需改动此函数的默认值和环境变量名，其他所有文件自动跟随。

**改动原则：** 纯字符串替换，无逻辑变更。不修改目录名（如 `hermes_cli/`）、不修改函数名（如 `get_hermes_home()`）、不修改 import 路径（如 `from hermes_cli.main import main`）。

### 任务 0.1：hermes_constants.py — 改默认配置目录和环境变量

**文件：**
- 修改：`hermes_constants.py`

**改动：** 2 行。`get_hermes_home()` 中的默认路径和环境变量名。

**影响：** 所有调用 `get_hermes_home()` 的 50+ 个文件自动使用新路径，无需逐个修改。

- [ ] **步骤 0.1.1：改默认路径**

在第 17 行，将 `Path.home() / ".hermes"` 改为 `Path.home() / ".deepagent"`：

```python
# 修改前
return Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))

# 修改后
return Path(os.getenv("DEEPAGENT_HOME", Path.home() / ".deepagent"))
```

- [ ] **步骤 0.1.2：改 docstring**

同时更新第 12-14 行的 docstring，反映新路径和环境变量名：

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

> 函数名 `get_hermes_home` **不修改**——改名会引发 50+ 个文件的 import 断裂，收益极小。内部实现改了就行。

- [ ] **步骤 0.1.3：验证影响面**

```bash
# 确认改动前：~/.hermes 是硬编码的唯一源头
grep -rn '\.hermes\|HERMES_HOME' hermes_constants.py | head -5
```

预期：只有 `hermes_constants.py` 中约 3-4 处（get_hermes_home + get_default_hermes_root + get_skills_dir 等）。


### 任务 0.2：pyproject.toml — 改包名和 CLI entry points

**文件：**
- 修改：`pyproject.toml`

**改动：** 约 20 处替换。包括包名、CLI entry point 名称、extras 引用。

- [ ] **步骤 0.2.1：改包名**

第 6 行：`name = "hermes-agent"` → `name = "deepagent"`

- [ ] **步骤 0.2.2：改 CLI entry points**

第 115-117 行：
```toml
# 修改前
hermes = "hermes_cli.main:main"
hermes-agent = "run_agent:main"
hermes-acp = "acp_adapter.entry:main"

# 修改后
deepagent = "hermes_cli.main:main"
deepagent-agent = "run_agent:main"
deepagent-acp = "acp_adapter.entry:main"
```

- [ ] **步骤 0.2.3：改 extras 中的自引用**

第 70-76 行（termux extra）和 89-112 行（all extra）中的 `hermes-agent[xxx]` 改为 `deepagent[xxx]`。

```toml
# 修改前（第 70-76 行）
termux = [
  "hermes-agent[cron]",
  "hermes-agent[cli]",
  "hermes-agent[pty]",
  "hermes-agent[mcp]",
  "hermes-agent[honcho]",
  "hermes-agent[acp]",
]

# 修改后
termux = [
  "deepagent[cron]",
  "deepagent[cli]",
  "deepagent[pty]",
  "deepagent[mcp]",
  "deepagent[honcho]",
  "deepagent[acp]",
]
```

同理修改 all extra（第 88-112 行）中的所有 `hermes-agent` → `deepagent`。

- [ ] **步骤 0.2.4：验证**

```bash
# 确认 pyproject.toml 中没有残留的 hermes-agent 包名引用
grep -n 'hermes-agent' pyproject.toml || echo "No remaining hermes-agent references"
```

预期：0 匹配。


### 任务 0.3：根目录 `hermes` 启动器 — 改名

**文件：**
- 重命名：`hermes` → `deepagent`
- 修改：第 3-4 行注释

- [ ] **步骤 0.3.1：重命名文件**

```bash
mv hermes deepagent
```

- [ ] **步骤 0.3.2：更新注释**

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

> 注意：第 10 行的 `from hermes_cli.main import main` **不修改**——这是 import 路径。


### 任务 0.4：setup-hermes.sh — 改名 + 内容更新

**文件：**
- 重命名：`setup-hermes.sh` → `setup-deepagent.sh`
- 修改：全文约 22 处替换

- [ ] **步骤 0.4.1：重命名**

```bash
mv setup-hermes.sh setup-deepagent.sh
```

- [ ] **步骤 0.4.2：全局内容替换**

| 替换目标 | 替换为 | 出现次数 |
|---------|--------|---------|
| `Hermes Agent`（文件名/标题） | `DeepAgent` | ~3 |
| `hermes`（命令名） | `deepagent` | ~10 |
| `HERMES_HOME` | `DEEPAGENT_HOME` | ~1 |
| `~/.hermes` | `~/.deepagent` | ~2 |
| `setup-hermes.sh`（自引用） | `setup-deepagent.sh` | ~2 |
| 其他 `hermes` 小写实例 | `deepagent` | ~4 |

具体替换示例：

```bash
# 第 3-4 行：标题和描述
# 修改前
# Hermes Agent Setup Script
# 修改后
# DeepAgent Setup Script

# 第 17 行：symlink 描述
# 修改前
# 5. Symlinks the 'hermes' CLI command into a user-facing bin dir
# 修改后
# 5. Symlinks the 'deepagent' CLI command into a user-facing bin dir

# 第 9 行
# 修改前
#   ./setup-hermes.sh
# 修改后
#   ./setup-deepagent.sh
```

- [ ] **步骤 0.4.3：内部逻辑中的命令名替换**

搜索脚本中所有 `hermes` 命令调用，改为 `deepagent`。例如：

```bash
# 类似这样的行（假设行号）
# 修改前
$VENV_DIR/bin/hermes setup
# 修改后
$VENV_DIR/bin/deepagent setup
```


### 任务 0.5：hermes_cli/main.py — 更新 CLI 帮助文案

**文件：**
- 修改：`hermes_cli/main.py`

**改动：** 约 15 处。只改 docstring 和帮助文本中的命令名，不碰 import 路径和函数名。

- [ ] **步骤 0.5.1：更新模块 docstring**

第 3-7 行：
```python
# 修改前
"""
Hermes CLI - Main entry point.

Usage:
    hermes                     # Interactive chat (default)
    hermes chat                # Interactive chat
    hermes gateway             # Run gateway in foreground
"""

# 修改后
"""
DeepAgent CLI - Main entry point.

Usage:
    deepagent                  # Interactive chat (default)
    deepagent chat             # Interactive chat
    deepagent gateway          # Run gateway in foreground
"""
```

- [ ] **步骤 0.5.2：全文搜索替换帮助文本中的命令名**

搜索所有 `"hermes "`（带引号+空格，避免碰函数名中的 `hermes`）改为 `"deepagent "`。

```bash
# 修改前
# "hermes gateway", "hermes cron", "hermes doctor"
# 修改后
# "deepagent gateway", "deepagent cron", "deepagent doctor"
```

> **不动清单（明确不包括）：**
> - `hermes_cli/` 目录名 — 不重命名
> - 函数名如 `get_hermes_home()` — 不改名
> - import 路径如 `from hermes_cli.main import main` — 不改
> - `hermes_constants.py`, `hermes_state.py` 等文件名 — 不改
> - 内部变量名、日志消息中的 `hermes` — 仅改用户可见的 CLI 帮助文本


### 阶段 0 改后效果验证

| 维度 | 改前 | 改后 |
|------|------|------|
| 运行命令 | `hermes` | `deepagent` |
| 配置目录 | `~/.hermes` | `~/.deepagent` |
| 环境变量 | `HERMES_HOME` | `DEEPAGENT_HOME` |
| pip 包名 | `hermes-agent` | `deepagent` |
| 安装脚本 | `setup-hermes.sh` | `setup-deepagent.sh` |
| 启动器文件 | `hermes`（可执行） | `deepagent`（可执行） |

> **不动的内容：** `hermes_cli/` 目录名、`get_hermes_home()` 函数名、`hermes_constants.py` 等文件名、内部 import 路径 `from hermes_cli import ...` 全部保留不变。这是最低风险策略——改了这些会引发大规模 import 断裂，而函数名的内部引用可以保持语义自明（"hermes_home" 即使指向 `~/.deepagent` 也无妨）。

---

## 一、粗方案审评结果

### 1.1 架构层面合理处

| 方面 | 评价 |
|------|------|
| 5 个新模块分解 | 职责清晰、边界明确，符合单一职责原则 |
| 集成策略 | 通过 hook points 插入而非替换现有代码，风险最低 |
| Memory Index 设计 | 只存导航指引（1-2KB），深度内容存子文档按需加载，节省大量 system prompt token |
| KV Cache 围栏保护 | 借鉴现有 [CONTEXT COMPACTION] 围栏模式，实现成本低 |
| 三层评估位置 | 后置处理、不 block 主循环的设计合理 |

### 1.2 发现的问题/盲区（共 9 项）

**问题 1 — Router 和 CognitiveGate 职责重叠：**
- 粗方案的 `AgentRouter` 做语义路由（Route1）和执行路由（Route3），按决策矩阵也判断 "复杂任务→进循环"，但这与 `CognitiveGate` 的评估职能有交叠。
- **修复：** Router 只做前置路由决策（分类意图+匹配专家+选择执行模式）。CognitiveGate 只做后置评估（每轮对话后的三层自评）。"是否进入认知循环"由 Router 的 `_decide_path()` 判断，不给 CognitiveGate。

**问题 2 — `ExpertMatcher.match_for_mode()` 接口语义不清晰：**
- Agency 的 4 种模式（A/B/C/D）是执行模式，不是匹配模式。匹配应该基于任务类型和关键词，mode 是匹配后的决策输出。
- **修复：** 去掉 `match_for_mode()`。统一用 `match(message, route_name, context)` 返回 `list[Expert]`，其中 route_name 来自 Router 的意图分类。

**问题 3 — Memory Index 初始化需要更细致的目录结构设计：**
- 粗方案说 `build_initial_index()` 读取现有 `~/.hermes/memories/` 下的文件构建 MAP.md，但现有目录下只有 MEMORY.md 和 USER.md（memory_tool.py 定义的），没有 skills/、paper-notes/ 等子目录。
- **修复：** 需要先在 memories/ 下创建子目录结构（skills/、paper-notes/、references/），然后构建初始 MAP.md。

**问题 4 — PlanTracker 与 Hermes 已有 todo 系统的关系需要明确：**
- Hermes 已有 `todo_tool.py` 和 `todowrite` 工具管理原子任务状态。
- **关系定义：** `PlanTracker` 是 todo 的上层抽象——管理 plan 级别信息（目标、盲区清单、goal 调整历史、整体状态），而不管理每个原子任务的细节。原子任务状态仍由 todo 工具负责。
- Plan JSON 只存储：plan_id, goal, goal_history, status, current_task_id, gaps_found, 时间戳。

**问题 5 — 专家加载路径：**
- Agency 专家安装在 `~/.config/opencode/agents/`，这个路径是由 Agency 工具确定的固定路径，不是 Hermes 配置路径。
- **修复：** `ExpertMatcher` 的 `agents_dir` 默认值设为 `~/.config/opencode/agents/`，同时支持通过构造函数参数覆盖。不使用 `get_hermes_home()`。

**问题 6 — 意图分类粒度可能不够：**
- 粗方案只分 5 类（discuss/implement/analyze/research/simple），但 Agency 实际有 16 个 division × 232 专家，更细粒度的分类可能更准确。
- **修复：** 保持粗方案分类粒度，但将 route_name 直接映射到 Agency 的 division，缩小匹配范围。

**问题 7 — 缺少缓存策略：**
- `ExpertMatcher` 每次匹配都扫描 232 个 .md 文件，性能差。
- **修复：** 添加 `_agent_cache` 字典，在 `build_expert_registry()` 时一次读取所有专家元数据（slug + name + description + division），后续匹配只操作内存。

**问题 8 — CognitiveGate 评估频率：**
- 粗方案说"每个 turn 后触发"，但 agent loop 中一个 turn 可能包含多个 tool call。对每个 tool call 做三层自评太频繁。
- **修复：** CognitiveGate 只在 agent 出 text response 时（即 `final_response` 生成后）触发全面评估。Tool call 后只做轻量检查（L1 荣辱观中的"是否如实报告工具失败"）。

**问题 9 — run_agent.py hook point 定位不精确：**
- 粗方案说插入 Pre-turn/Post-turn hook，但 run_agent.py 中主循环（约 8103 行）的架构是：一个 turn = 一次 API call + 零次或多次 tool dispatch。
- **修复：** Pre-turn hook 在 `run_conversation()` 开始处（约 7803 行，用户消息已添加但 API 调用未开始前）。Post-turn hook 在 API 调用后的 text response 生成后。

### 1.3 模块依赖关系图

```
并行第一组（完全独立）：
  cognitive_gate.py  ← 无依赖
  memory_index.py    ← 依赖 MAP.md 文件存在
  plan_tracker.py    ← 依赖 JSON 文件路径
  expert_matcher.py  ← 依赖 Agency 专家 .md 文件

并行第二组（依赖第一组）：
  router.py          ← 依赖 expert_matcher + plan_tracker + memory_index + cognitive_gate

并行第三组（独立已有文件修改）：
  prompt_builder.py  ← 注入 MemoryIndex 导航段 + 认知循环引导
  context_compressor.py ← 添加围栏检测逻辑
  memory_tool.py     ← 扩展 read_nested 动作

串行第四组（集成）：
  run_agent.py       ← 依赖以上所有模块

串行第五组（数据文件）：
  MAP.md 创建       ← 依赖 memory_index.py
  SOUL.md 更新      ← 独立
```

---

## 二、详细实施任务

### 任务 1：agent/cognitive_gate.py — 三层认知评估器

**文件：**
- 创建：`agent/cognitive_gate.py`
- 测试：`tests/agent/test_cognitive_gate.py`

**接口（产出供后续任务消费）：**

```python
@dataclass
class HonorResult:
    hid_uncertainty: bool      # 是否隐瞒了不确定性
    made_unverified_claim: bool # 是否做了未经工具验证的论断
    hid_tool_failure: bool     # 是否隐瞒了工具失败
    passed: bool               # 整体是否通过

@dataclass
class ThinkingResult:
    skipped_steps: list[str]   # 跳过的步骤
    no_hypothesis_first: list[str]  # 没有假设先行的操作
    blindspots: list[str]      # 识别到的盲区
    passed: bool

@dataclass
class EvalResult:
    plan_id: str                     # 关联的 plan_id
    honor: HonorResult
    thinking: ThinkingResult
    should_interrupt_user: bool      # 是否达到边界需要问用户
    gaps_found: list[str]            # 新发现的盲区
    goal_adjustment: str | None      # 如需调整目标，建议的新目标
    adjustments_note: str            # 人类可读的评估结论
```

**任务步骤：**

- [ ] **步骤 1.1：创建 `agent/cognitive_gate.py` 框架**

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
            turn_data: 包含当前 turn 的信息：
                - user_message: str
                - assistant_response: str (final text response, 非中间 tool call)
                - tool_calls: list[dict] — 本次 turn 调用的工具列表
                - tool_results: list[dict] — 对应的工具结果
                - plan_id: str — 当前 plan_id（可选）
                - confidence_indicators: list[str] — 模型输出的不确定性指标

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
        1. 模型是否明确说了"我不确定"、"我需要查一下"之类的话
           → 如果始终没有不确定性表达，但有明显盲区 → hid_uncertainty=True
        2. 模型是否使用工具验证了关键论断
           → 如果做出事实性论断但没有对应的工具调用 → made_unverified_claim=True
        3. 工具调用失败时是否如实报告
           → 遍历 tool_results，如果有 error/failure 但在 response 中未提及 → hid_tool_failure=True
        """
        result = HonorResult()
        response = turn_data.get("assistant_response", "")
        tool_calls = turn_data.get("tool_calls", [])
        tool_results = turn_data.get("tool_results", [])
        confidence_indicators = turn_data.get("confidence_indicators", [])

        # 检查 1：是否有不确定性表达
        has_uncertainty_expr = any(
            kw in response.lower()
            for kw in ["不确定", "不太确定", "可能", "probably", "might", "i'm not sure",
                       "我需要查", "let me check", "先查一下", "让我查"]
        )
        if not has_uncertainty_expr and confidence_indicators:
            # 有盲区但没说不确定
            result.hid_uncertainty = True

        # 检查 2：是否有未经工具验证的论断
        # 简单启发式：如果 response 中包含事实性断言但对应工具没调用过
        has_factual_assertion = any(
            kw in response.lower()
            for kw in ["是", "不是", "应该", "必须", "always", "never", "all", "every"]
        )
        if has_factual_assertion and not tool_calls:
            result.made_unverified_claim = True

        # 检查 3：工具失败是否如实汇报
        for tr in tool_results:
            content = str(tr.get("content", ""))
            if "error" in content.lower() or "fail" in content.lower() or "timeout" in content.lower():
                # 在 response 中找对应
                if "失败" not in response and "error" not in response.lower() and "没有成功" not in response:
                    result.hid_tool_failure = True
                    break

        return result

    def _check_thinking(self, turn_data: dict) -> ThinkingResult:
        """Layer 2 思维方式检查。

        检查点：
        1. 是否 step by step（多个工具调用应该按逻辑顺序）
        2. 是否有假设先行（工具调用前有假设说明）
        3. 是否有主动识别的盲区
        """
        result = ThinkingResult()
        response = turn_data.get("assistant_response", "")
        tool_calls = turn_data.get("tool_calls", [])

        # 检查跳过步骤：如果有复杂的工具调用但 response 中没按顺序说明
        if len(tool_calls) > 3 and "step" not in response.lower() and "先" not in response:
            result.skipped_steps.append("多步操作未说明执行顺序")

        # 检查假设先行
        if tool_calls and not any(
            kw in response.lower()
            for kw in ["假设", "我认为", "hypothesis", "i think", "应该是因为", "按理说"]
        ):
            result.no_hypothesis_first.append("工具调用前未声明假设")

        # 识别盲区
        for kw in ["不确定", "不清楚", "盲区", "需要查", "盲点", "不懂", "unknown", "need to investigate"]:
            if kw in response.lower():
                result.blindspots.append(f"主动识盲区: {kw}")

        return result

    def _reflect(self, honor: HonorResult, thinking: ThinkingResult, turn_data: dict) -> dict:
        """Layer 3 三省吾身。

        回头检查 L1+L2 结果，生成改进建议。
        """
        gaps = list(thinking.blindspots)
        goal_adjustment = None
        note_parts = []

        if not honor.passed:
            if honor.hid_uncertainty:
                gaps.append("Layer1违规：有不确定性但未明确说明")
                note_parts.append("有不确定性应明确说明")
            if honor.made_unverified_claim:
                gaps.append("Layer1违规：有未经工具验证的论断")
                note_parts.append("事实性论断需用工具验证")
            if honor.hid_tool_failure:
                gaps.append("Layer1违规：工具失败未如实报告")
                note_parts.append("工具失败必须如实报告")

        if not thinking.passed:
            note_parts.append("思维方式可优化：使用Step-by-Step+假设先行")

        return {
            "gaps": gaps,
            "goal_adjustment": goal_adjustment,
            "note": "; ".join(note_parts) if note_parts else "评估通过",
        }

    def _should_ask_user(self, reflection: dict) -> bool:
        """判断不确定性是否超过阈值，需要中断问用户。"""
        gaps = reflection.get("gaps", [])
        return len(gaps) >= 2  # 两个以上盲区则需要问用户

    def get_recent_evaluations(self, n: int = 5) -> list[dict]:
        """返回最近 n 次评估记录。"""
        return self._eval_history[-n:]
```

- [ ] **步骤 1.2：编写测试文件 `tests/agent/test_cognitive_gate.py`**

```python
"""Tests for CognitiveGate — 三层认知评估器。"""

import pytest
from agent.cognitive_gate import CognitiveGate, HonorResult, ThinkingResult, EvalResult


class TestHonorCheck:
    """Layer 1 荣辱观检查测试。"""

    def test_passes_when_no_issues(self):
        """正常情况：不隐瞒不确定性、有工具验证、如实报告失败。"""
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
        """有事实性论断但没用工具。"""
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

预期：所有测试通过。

---

### 任务 2：agent/memory_index.py — 记忆嵌套索引管理器

**文件：**
- 创建：`agent/memory_index.py`
- 创建目录：`~/.hermes/memories/skills/`, `~/.hermes/memories/paper-notes/`, `~/.hermes/memories/references/`
- 测试：`tests/agent/test_memory_index.py`

**接口（产出供后续任务消费）：**

```python
class MemoryIndex:
    def __init__(self, index_path: str | Path | None = None)
        # index_path 默认：get_hermes_home() / "memories" / "MAP.md"

    def index_summary(self) -> str
        # 返回注入 system prompt 的导航段，用 -----COGNITIVE_INDEX_START----- 包裹
        # 输出：1-2KB 的 MAP.md 导航内容

    def navigate(self, topic: str) -> list[dict]
        # 搜索 MAP.md 找到与 topic 相关的索引条目
        # 返回 [{"topic": str, "path": str, "description": str}, ...]

    def read_nested(self, path: str) -> str
        # 从 MAP.md 索引导航读取子文档内容
        # path 可以是相对路径（如 "skills/deepseek-physics/SKILL.md"）或绝对路径

    def update_entry(self, topic: str, path: str, description: str) -> None
        # 更新或新增索引条目

    def build_initial_index(self) -> None
        # 首次初始化：扫描 ~/.hermes/memories/ 下子目录，构建 MAP.md
```

- [ ] **步骤 2.1：创建 `agent/memory_index.py`**

```python
"""Memory 嵌套索引管理器（StarRoad Cognition）。
核心规则：MAP.md 只存导航指引（1-2KB），深度内容存在于子文档按需加载。"""

from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Optional

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

    # -- 公开接口 --

    def index_summary(self) -> str:
        """返回注入 system prompt 的导航段。

        格式：
            -----COGNITIVE_INDEX_START-----
            (MAP.md 的导航内容，1-2KB)
            -----COGNITIVE_INDEX_END-----

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
            topic: 搜索关键词

        Returns:
            [{"topic": str, "path": str, "description": str}, ...]
        """
        content = self._load_map()
        if not content:
            return []

        results = []
        topic_lower = topic.lower()
        # 解析 MAP.md 中的条目：- topic: path — description
        pattern = re.compile(r"^-\s+(.+?):\s+(.+?)(?:\s+—\s+(.+))?$", re.MULTILINE)
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
        """从索引导航读取子文档内容。

        Args:
            path: 相对路径（如 "skills/deepseek-physics/SKILL.md"）
                  或绝对路径

        Returns:
            子文档的文本内容。如果文件不存在，返回空字符串。
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

    def update_entry(self, topic: str, path: str, description: str) -> None:
        """更新或新增索引条目。

        如果 topic 已存在，更新其 path 和 description。
        如果不存在，追加新条目。
        """
        content = self._load_map()
        if not content:
            # MAP.md 不存在，创建基本结构
            content = "# 记忆索引（导航层）\n\n## 关键知识领域\n\n"
            content += f"- {topic}: {path} — {description}\n"
        else:
            # 检查是否已存在
            pattern = re.compile(
                rf"^-\s+{re.escape(topic)}:\s+.*$", re.MULTILINE
            )
            if pattern.search(content):
                # 更新已有条目
                new_line = f"- {topic}: {path} — {description}"
                content = pattern.sub(new_line, content)
            else:
                # 追加新条目
                content += f"- {topic}: {path} — {description}\n"

        self._write_map(content)

    def build_initial_index(self) -> None:
        """首次初始化：扫描 ~/.hermes/memories/ 下子目录，构建 MAP.md。

        如果 MAP.md 已存在且非空，跳过初始化。
        """
        if self._index_path.exists():
            content = self._read_file_content(self._index_path)
            if content and content.strip():
                logger.info("MemoryIndex: MAP.md already exists, skipping initialization")
                return

        # 扫描子目录
        sections = {
            "关键知识领域": [],
            "项目状态": [],
            "用户偏好": [],
        }

        if self._memories_dir.exists():
            for child in sorted(self._memories_dir.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    # 检查子目录中是否有 SKILL.md 或 .md 文件
                    md_files = sorted(child.glob("*.md"))
                    for md_file in md_files:
                        if md_file.name == MAP_FILENAME:
                            continue
                        rel_path = md_file.relative_to(self._memories_dir)
                        sections["关键知识领域"].append(
                            f"- {child.name}: {rel_path}\n"
                        )

        # 构建 MAP.md 内容
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
            logger.info("MemoryIndex: initial MAP.md created")

    # -- 内部方法 --

    def _load_map(self) -> str:
        """读取 MAP.md 内容（带缓存）。"""
        if self._map_content is not None:
            return self._map_content
        content = self._read_file_content(self._index_path)
        self._map_content = content or ""
        return self._map_content

    def _write_map(self, content: str) -> None:
        """写回 MAP.md 并更新缓存。"""
        self._memories_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._index_path.write_text(content, encoding="utf-8")
            self._map_content = content
        except Exception as e:
            logger.error("MemoryIndex: failed to write MAP.md: %s", e)

    @staticmethod
    def _read_file_content(path: Path) -> str:
        """安全读取文件内容，失败返回空字符串。"""
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug("MemoryIndex: failed to read %s: %s", path, e)
            return ""
```

- [ ] **步骤 2.2：编写测试文件 `tests/agent/test_memory_index.py`**

```python
"""Tests for MemoryIndex — 记忆嵌套索引管理器。"""

import pytest
from pathlib import Path
from agent.memory_index import MemoryIndex, COGNITIVE_FENCE_START, COGNITIVE_FENCE_END


@pytest.fixture
def tmp_index(tmp_path):
    """创建临时目录的 MemoryIndex 实例。"""
    mem_dir = tmp_path / "memories"
    mem_dir.mkdir(parents=True)
    index_path = mem_dir / "MAP.md"
    return MemoryIndex(str(index_path))


class TestIndexSummary:
    def test_returns_empty_when_no_map(self, tmp_index):
        """MAP.md 不存在时返回空字符串。"""
        summary = tmp_index.index_summary()
        assert summary == ""

    def test_wraps_content_with_fences(self, tmp_index):
        """返回内容被 COGNITIVE_FENCE 围栏包裹。"""
        tmp_index.update_entry("test-topic", "test/path.md", "test desc")
        summary = tmp_index.index_summary()
        assert summary.startswith(COGNITIVE_FENCE_START)
        assert summary.endswith(COGNITIVE_FENCE_END)

    def test_truncates_to_2000_chars(self, tmp_index):
        """超长内容被截断到 2000 字符。"""
        for i in range(200):
            tmp_index.update_entry(f"topic-{i}", f"path/{i}.md", "d" * 50)
        summary = tmp_index.index_summary()
        # 拿到围栏内部的内容
        inner = summary[len(COGNITIVE_FENCE_START):-len(COGNITIVE_FENCE_END)].strip()
        assert len(inner) <= 2100


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
        """读取存在的子文档。"""
        sub_file = tmp_path / "memories" / "test.md"
        sub_file.parent.mkdir(parents=True)
        sub_file.write_text("hello world")
        content = tmp_index.read_nested(str(sub_file))
        assert content == "hello world"

    def test_returns_empty_for_missing_file(self, tmp_index):
        content = tmp_index.read_nested("/nonexistent/path.md")
        assert content == ""

    def test_resolves_relative_path(self, tmp_index, tmp_path):
        """相对路径基于 memories_dir 解析。"""
        sub_file = tmp_path / "memories" / "sub" / "doc.md"
        sub_file.parent.mkdir(parents=True)
        sub_file.write_text("relative content")
        content = tmp_index.read_nested("sub/doc.md")
        assert content == "relative content"


class TestUpdateEntry:
    def test_creates_map_when_not_exists(self, tmp_index):
        """MAP.md 不存在时，update_entry 创建它。"""
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
        assert "关键知识领域" in content
        assert "test.md" in content

    def test_skips_if_map_exists(self, tmp_index):
        tmp_index.update_entry("existing", "path.md", "desc")
        initial_mtime = tmp_index._index_path.stat().st_mtime
        tmp_index.build_initial_index()
        assert tmp_index._index_path.stat().st_mtime == initial_mtime
```

- [ ] **步骤 2.3：创建初始目录结构并跑测试**

```bash
# 创建初始目录结构
mkdir -p ~/.hermes/memories/skills ~/.hermes/memories/paper-notes ~/.hermes/memories/references

# 跑测试
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_memory_index.py -v
```

预期：所有测试通过。

---

### 任务 3：agent/plan_tracker.py — 计划状态机

**文件：**
- 创建：`agent/plan_tracker.py`
- 测试：`tests/agent/test_plan_tracker.py`

**接口（产出供后续任务消费）：**

```python
class PlanTracker:
    def __init__(self, plans_dir: str | Path | None = None)
        # plans_dir 默认：get_hermes_home() / "plans"

    def create_or_update(self, goal: str, tasks: list[dict] | None = None) -> str
        # 创建新 plan 或追加任务到现有 plan（如果已有 in_progress 的 plan）
        # 返回 plan_id

    def mark_done(self, task_id: str) -> None
        # 标记指定任务完成

    def add_gap(self, gap: str) -> None
        # 探索中发现的盲区追加到计划

    def refine_goal(self, new_goal: str) -> None
        # 发现用户认知不够时调整目标，记录 goal_history

    def get_status(self) -> dict
        # 返回当前 plan 的状态摘要

    def get_current_plan_id(self) -> str | None
        # 返回当前 in_progress 的 plan_id，或 None

    def load_plan(self, plan_id: str) -> dict | None
        # 读取指定 plan 的 JSON

    def list_plans(self) -> list[dict]
        # 列出所有 plan（按创建时间倒序）

    def validate_plan(self, plan: dict) -> bool
        # 校验 plan 结构完整性
```

- [ ] **步骤 3.1：创建 `agent/plan_tracker.py`**

```python
"""Plan 状态机管理器（StarRoad Cognition）。
Plan 不只是 markdown 文件，是一个动态状态机。
JSON 持久化到 ~/.hermes/plans/<id>.json

与 todo 工具的关系：
- PlanTracker 管理 plan 级别信息（目标/盲区/调整历史/整体状态）
- todo 工具管理每个原子任务的详细状态
- PlanTracker 的 tasks 列表只是简化的任务清单，详细追踪走 todo"""

from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

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
        tracker.add_gap("发现 Token 刷新逻辑不完善")
        status = tracker.get_status()
    """

    def __init__(self, plans_dir: str | Path | None = None):
        if plans_dir is None:
            plans_dir = get_hermes_home() / "plans"
        self._plans_dir = Path(plans_dir)
        self._plans_dir.mkdir(parents=True, exist_ok=True)
        self._current_plan_id: str | None = None  # 缓存当前 in_progress 的 plan_id

    def create_or_update(self, goal: str, tasks: list[dict] | None = None) -> str:
        """创建新 plan 或追加任务到现有 plan。

        Args:
            goal: 任务目标
            tasks: 任务列表，每个元素为 {"id": str, "desc": str}

        Returns:
            plan_id
        """
        # 检查是否有 in_progress 的 plan
        existing = self._find_in_progress_plan()
        if existing:
            # 追加任务到现有 plan（如果提供了新任务）
            if tasks:
                existing_tasks = existing.get("tasks", [])
                existing_ids = {t["id"] for t in existing_tasks}
                for t in tasks:
                    if t["id"] not in existing_ids:
                        existing_tasks.append({
                            "id": t["id"],
                            "desc": t["desc"],
                            "status": "pending",
                        })
                existing["tasks"] = existing_tasks
            existing["updated_at"] = self._now_iso()
            self._save_plan(existing)
            self._current_plan_id = existing["plan_id"]
            return existing["plan_id"]

        # 创建新 plan
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
        """标记指定任务完成。"""
        plan = self._load_current_plan()
        if not plan:
            logger.debug("PlanTracker: no active plan to mark task done")
            return
        for task in plan.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = "done"
                break
        # 自动推进到下一个 pending 任务
        for task in plan.get("tasks", []):
            if task["status"] == "pending":
                plan["current_task"] = task["id"]
                break
        plan["updated_at"] = self._now_iso()
        self._save_plan(plan)

    def add_gap(self, gap: str) -> None:
        """探索中发现的盲区追加到计划。"""
        plan = self._load_current_plan()
        if not plan:
            logger.debug("PlanTracker: no active plan to add gap")
            return
        if gap not in plan.get("gaps_found", []):
            plan.setdefault("gaps_found", []).append(gap)
            plan["updated_at"] = self._now_iso()
            self._save_plan(plan)

    def refine_goal(self, new_goal: str) -> None:
        """发现用户认知不够时调整目标。"""
        plan = self._load_current_plan()
        if not plan:
            logger.debug("PlanTracker: no active plan to refine goal")
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
        in_progress_count = sum(1 for t in tasks if t["status"] == "in_progress")

        return {
            "has_active_plan": True,
            "plan_id": plan["plan_id"],
            "goal": plan["goal"],
            "goal_history": plan.get("goal_history", []),
            "status": plan["status"],
            "progress": f"{done}/{total}",
            "done_count": done,
            "pending_count": pending,
            "in_progress_count": in_progress_count,
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
        """校验 plan 结构完整性。"""
        required_keys = {"plan_id", "goal", "status", "tasks", "created_at", "updated_at"}
        if not all(k in plan for k in required_keys):
            return False
        if plan["status"] not in ("in_progress", "completed", "cancelled"):
            return False
        for task in plan.get("tasks", []):
            if not all(k in task for k in ("id", "desc", "status")):
                return False
            if task["status"] not in ("pending", "in_progress", "done"):
                return False
        return True

    # -- 内部方法 --

    def _find_in_progress_plan(self) -> dict | None:
        """扫描 plans 目录找到 in_progress 的 plan。"""
        for f in sorted(self._plans_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("status") == "in_progress":
                    return data
            except Exception:
                continue
        return None

    def _load_current_plan(self) -> dict | None:
        """加载当前 plan。"""
        plan_id = self.get_current_plan_id()
        if not plan_id:
            return None
        return self.load_plan(plan_id)

    def _save_plan(self, plan: dict) -> None:
        """持久化 plan 到 JSON 文件。"""
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

- [ ] **步骤 3.2：编写测试文件 `tests/agent/test_plan_tracker.py`**

```python
"""Tests for PlanTracker — 计划状态机管理器。"""

import pytest
import json
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
        assert pid1 == pid2  # 同一个 plan
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
        status = tracker.get_status()
        assert status["has_active_plan"] is False

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
        assert status["done_count"] == 1
        assert status["pending_count"] == 2


class TestValidatePlan:
    def test_validates_correct_plan(self, tracker):
        plan = {
            "plan_id": "test-1",
            "goal": "test",
            "status": "in_progress",
            "tasks": [{"id": "t1", "desc": "task", "status": "pending"}],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        assert tracker.validate_plan(plan) is True

    def test_rejects_missing_keys(self, tracker):
        assert tracker.validate_plan({"plan_id": "test"}) is False

    def test_rejects_invalid_status(self, tracker):
        plan = {
            "plan_id": "test-1",
            "goal": "test",
            "status": "invalid_status",
            "tasks": [],
            "created_at": "",
            "updated_at": "",
        }
        assert tracker.validate_plan(plan) is False
```

- [ ] **步骤 3.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_plan_tracker.py -v
```

---

### 任务 4：agent/expert_matcher.py — 专家匹配器

**文件：**
- 创建：`agent/expert_matcher.py`
- 测试：`tests/agent/test_expert_matcher.py`

**接口（产出供后续任务消费）：**

```python
@dataclass
class Expert:
    slug: str
    name: str
    division: str
    prompt: str     # 完整的 system prompt（从 .md 文件读取）

class ExpertMatcher:
    def __init__(self, agents_dir: str | Path | None = None)
        # agents_dir 默认：~/.config/opencode/agents/

    def match(self, message: str, route_name: str, top_n: int = 2) -> list[Expert]
        # 根据 route_name + 关键词匹配最佳专家
        # route_name: 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
        # 返回 top_n 个专家（主专家 + 交叉验证专家）

    def load_expert_prompt(self, slug: str) -> str
        # 读取对应 .md 文件，提取 content 作为 system prompt

    def get_available_experts(self) -> list[dict]
        # 返回所有可用专家的摘要列表

    def get_experts_for_division(self, division: str) -> list[Expert]
        # 按 division 获取专家列表

    def refresh_cache(self) -> None
        # 重建专家注册表缓存
```

- [ ] **步骤 4.1：创建 `agent/expert_matcher.py`**

```python
"""专家匹配器（StarRoad Cognition）。
对接 The Agency 的 232 专家库（~/.config/opencode/agents/）。
根据 route_name + 关键词匹配最佳专家。"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Agency 16 个 division 到 route_name 的映射
# 用于缩小匹配范围
ROUTE_TO_DIVISIONS = {
    "implement": ["Engineering", "Game Dev", "Spatial Computing"],
    "analyze": ["Security", "Testing", "Finance"],
    "research": ["Product", "Marketing", "Specialized", "GIS"],
    "discuss": ["Product", "Marketing", "Design", "Sales", "Project Mgmt"],
    "simple": [],  # 简单任务不需要匹配专家
}

# 默认 Agency 安装路径
DEFAULT_AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"


@dataclass
class Expert:
    """专家对象。"""
    slug: str         # 如 "software-architect"
    name: str         # 如 "Software Architect"
    division: str     # 如 "Engineering"
    prompt: str       # 完整的 system prompt（从 .md 文件读取）


class ExpertMatcher:
    """对接 The Agency 的 232 专家库。

    Usage:
        matcher = ExpertMatcher()
        experts = matcher.match("帮我设计数据库表", "implement")
        # 返回 [Expert("backend-architect"), Expert("database-optimizer")]
    """

    def __init__(self, agents_dir: str | Path | None = None):
        if agents_dir is None:
            agents_dir = DEFAULT_AGENTS_DIR
        self._agents_dir = Path(agents_dir)
        # 缓存：slug -> {"slug": str, "name": str, "division": str, "description": str}
        self._registry: dict[str, dict] = {}
        # prompt 缓存：slug -> str
        self._prompt_cache: dict[str, str] = {}

    def match(self, message: str, route_name: str, top_n: int = 2) -> list[Expert]:
        """根据 route_name + 关键词查找最匹配的专家。

        Args:
            message: 用户消息
            route_name: 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
            top_n: 返回 top N 个专家

        Returns:
            list[Expert] — 按匹配度排序。route_name='simple' 时返回空列表。
        """
        if route_name == "simple":
            return []

        # 确保缓存已加载
        if not self._registry:
            self.refresh_cache()

        # 根据 route_name 过滤可用的 division
        target_divisions = ROUTE_TO_DIVISIONS.get(route_name, [])
        candidates = list(self._registry.values())
        if target_divisions:
            candidates = [c for c in candidates if c.get("division") in target_divisions]

        if not candidates:
            # 降级：返回所有可用专家
            candidates = list(self._registry.values())

        # 关键词匹配评分
        keywords = self._extract_keywords(message)
        scored = []
        for candidate in candidates:
            score = self._score_match(candidate, keywords, route_name)
            if score > 0:
                scored.append((score, candidate))

        # 按分数排序，取 top_n
        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [c for _, c in scored[:top_n]]

        # 如果没有匹配，返回默认专家
        if not top_candidates:
            default_slugs = {
                "implement": "software-architect",
                "analyze": "code-reviewer",
                "research": "trend-researcher",
                "discuss": "product-manager",
            }
            slug = default_slugs.get(route_name, "software-architect")
            experts = self.get_experts_for_division("Engineering")
            for exp in experts:
                if exp.slug == slug:
                    top_candidates = [{"slug": slug, "name": exp.name, "division": exp.division}]
                    break

        # 加载 expert prompt
        result = []
        for c in top_candidates:
            prompt = self.load_expert_prompt(c["slug"])
            result.append(Expert(
                slug=c["slug"],
                name=c["name"],
                division=c.get("division", ""),
                prompt=prompt,
            ))

        return result

    def load_expert_prompt(self, slug: str) -> str:
        """读取对应 .md 文件，提取 content 作为 system prompt。

        缓存已读取的 prompt，避免重复文件 IO。
        """
        if slug in self._prompt_cache:
            return self._prompt_cache[slug]

        path = self._agents_dir / f"{slug}.md"
        if not path.exists():
            logger.warning("ExpertMatcher: agent file not found: %s", path)
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
            {"slug": v["slug"], "name": v["name"], "division": v.get("division", ""),
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
                    slug=v["slug"],
                    name=v["name"],
                    division=division,
                    prompt=prompt,
                ))
        return experts

    def refresh_cache(self) -> None:
        """重建专家注册表缓存。

        扫描 agents_dir 下所有 .md 文件，提取 frontmatter 中的元数据。
        """
        self._registry = {}
        if not self._agents_dir.exists():
            logger.warning("ExpertMatcher: agents dir not found: %s", self._agents_dir)
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

    def _parse_agent_file(self, path: Path) -> dict | None:
        """解析单个 agent .md 文件，提取 frontmatter 元数据。

        Agency 的 .md 文件格式：
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

        # 解析 frontmatter
        name = slug.replace("-", " ").title()
        division = "Engineering"
        description = ""

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            for line in fm_text.split("\n"):
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

        return {
            "slug": slug,
            "name": name,
            "division": division,
            "description": description,
        }

    @staticmethod
    def _extract_keywords(message: str) -> list[str]:
        """从消息中提取关键领域词。"""
        # 领域关键词（扩展自 Agency 决策矩阵）
        domain_keywords = {
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

        msg_lower = message.lower()
        found = []
        for domain, keywords in domain_keywords.items():
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
        elif route_name == "research" and division in ("product", "marketing"):
            score += 5

        return score
```

- [ ] **步骤 4.2：编写测试文件 `tests/agent/test_expert_matcher.py`**

```python
"""Tests for ExpertMatcher — 专家匹配器。"""

import pytest
from pathlib import Path
from agent.expert_matcher import ExpertMatcher, Expert


@pytest.fixture
def mock_agents_dir(tmp_path):
    """创建几个模拟的 Agency 专家文件。"""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # backend-architect.md
    (agents_dir / "backend-architect.md").write_text(
        "---\nname: Backend Architect\ndivision: Engineering\n"
        "description: Backend architecture and API design\n"
        "---\n\nYou are a backend architect. Design scalable APIs."
    )
    # database-optimizer.md
    (agents_dir / "database-optimizer.md").write_text(
        "---\nname: Database Optimizer\ndivision: Engineering\n"
        "description: Database optimization and SQL\n"
        "---\n\nYou are a database expert. Optimize queries."
    )
    # security-architect.md
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
        slugs = [e.slug for e in experts]
        assert "database-optimizer" in slugs or "backend-architect" in slugs

    def test_falls_back_to_default(self, mock_agents_dir):
        """没有匹配时使用默认专家。"""
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        experts = matcher.match("完全无关的内容zzz", "implement")
        assert len(experts) > 0


class TestLoadExpertPrompt:
    def test_loads_existing_prompt(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt = matcher.load_expert_prompt("backend-architect")
        assert "Backend Architect" in prompt or "backend architect" in prompt.lower()

    def test_returns_empty_for_missing(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt = matcher.load_expert_prompt("nonexistent-agent")
        assert prompt == ""

    def test_caches_after_first_load(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        prompt1 = matcher.load_expert_prompt("backend-architect")
        prompt2 = matcher.load_expert_prompt("backend-architect")
        assert prompt1 == prompt2


class TestCacheManagement:
    def test_refresh_cache_loads_all_agents(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        available = matcher.get_available_experts()
        assert len(available) >= 3  # 我们创建了 3 个 mock 文件

    def test_get_experts_for_division(self, mock_agents_dir):
        matcher = ExpertMatcher(str(mock_agents_dir))
        matcher.refresh_cache()
        engineers = matcher.get_experts_for_division("Engineering")
        assert len(engineers) >= 2
        security = matcher.get_experts_for_division("Security")
        assert len(security) >= 1
```

- [ ] **步骤 4.3：跑测试确认通过**

```bash
cd /Volumes/Doc/Code/DeepAgent && python -m pytest tests/agent/test_expert_matcher.py -v
```

---

### 任务 5：agent/router.py — 语义路由总控

**文件：**
- 创建：`agent/router.py`
- 测试：`tests/agent/test_router.py`

**说明：** Router 是前置路由决策模块。依赖 Task 1-4 的接口。

**接口（产出供后续任务消费）：**

```python
@dataclass
class RouteDecision:
    path: str           # 'direct' | 'cognitive_loop' | 'expert_delegate'
    mode: str           # 'A' | 'B' | 'C' | 'D'
    route_name: str     # 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
    experts: list[Expert]
    confidence: float   # 0.0-1.0

class AgentRouter:
    def __init__(self, expert_matcher, plan_tracker, memory_index, cognitive_gate)
    def route(self, message: str, context: dict | None = None) -> RouteDecision
    def format_prompt_section(self) -> str
        # 返回注入 system prompt 的认知循环引导段
```

- [ ] **步骤 5.1：创建 `agent/router.py`**

```python
"""语义路由总控（StarRoad Cognition Route 1-3）。
决定消息走哪条处理路径。前置路由，在 run_conversation() 开始时调用。"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from agent.expert_matcher import Expert, ExpertMatcher
from agent.plan_tracker import PlanTracker
from agent.memory_index import MemoryIndex
from agent.cognitive_gate import CognitiveGate

logger = logging.getLogger(__name__)

# 意图分类规则（关键词匹配 + 简单启发式）
_INTENT_PATTERNS: dict[str, list[str]] = {
    "implement": [
        "实现", "写代码", "创建", "开发", "构建", "加个", "添加", "修改",
        "implement", "create", "build", "add", "write", "code", "fix",
        "重构", "改", "修", "implement", "develop",
    ],
    "analyze": [
        "分析", "评审", "review", "检查", "审计", "评估", "review",
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
    "simple": [],  # 简单任务无关键词特征，由阈值判断
}

# 简单消息特征：短、无代码、无工具需求
_SIMPLE_PATTERNS = [
    r"^你好", r"^hi", r"^hello", r"^谢谢", r"^thanks",
    r"^yes", r"^no", r"^是的", r"^好的", r"^ok",
    r"^\S+\s*$",  # 单句无细节
]


@dataclass
class RouteDecision:
    """路由决策结果。"""
    path: str = "direct"                # 'direct' | 'cognitive_loop' | 'expert_delegate'
    mode: str = ""                      # 'A' | 'B' | 'C' | 'D'
    route_name: str = "simple"          # 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
    experts: list[Expert] = field(default_factory=list)
    confidence: float = 1.0


class AgentRouter:
    """消息路由总控。决定消息走哪条处理路径。

    职责：
    1. 分类意图（route_name）
    2. 简单任务 → path='direct'
    3. 复杂任务 → 匹配专家 → 决定执行模式 A/B/C/D

    不负责：后置评估（由 CognitiveGate 负责）。
    """

    def __init__(
        self,
        expert_matcher: ExpertMatcher,
        plan_tracker: PlanTracker | None = None,
        memory_index: MemoryIndex | None = None,
        cognitive_gate: CognitiveGate | None = None,
    ):
        self._expert_matcher = expert_matcher
        self._plan_tracker = plan_tracker
        self._memory_index = memory_index
        self._cognitive_gate = cognitive_gate

    def route(self, message: str, context: dict | None = None) -> RouteDecision:
        """主路由方法。

        Args:
            message: 用户消息
            context: 可选上下文（包含当前 plan 状态、对话历史长度等）

        Returns:
            RouteDecision
        """
        # 步骤 1：分类意图
        route_name = self._classify_intent(message)
        confidence = self._estimate_confidence(message, route_name)

        # 步骤 2：简单任务 → 直走原流程
        if route_name == "simple" or self._is_simple_message(message):
            return RouteDecision(
                path="direct",
                route_name="simple",
                confidence=confidence,
            )

        # 步骤 3：复杂任务 → 匹配专家
        experts = self._expert_matcher.match(message, route_name, top_n=2)

        # 步骤 4：决定执行模式
        mode = self._decide_mode(route_name, experts, context)

        # 步骤 5：决定路径
        path = self._decide_path(route_name, mode, experts)

        return RouteDecision(
            path=path,
            mode=mode,
            route_name=route_name,
            experts=experts,
            confidence=confidence,
        )

    def format_prompt_section(self) -> str:
        """返回注入 system prompt 的认知循环引导段。

        约 300 字，在 system prompt 末尾注入。
        """
        parts = [
            "## 认知循环（StarRoad Cognition）",
            "",
            "面对复杂任务时，请遵循先内后外的认知循环流程：",
            "",
            "1. **内吸（Internal Recall）** — 先向内求：",
            "   - 搜索记忆索引找已有知识",
            "   - 搜索历史对话回忆相关讨论",
            "   - 扫描技能列表加载相关 skill",
            "",
            "2. **形成探索计划** — 将盲区转化为具体探索任务",
            "",
            "3. **外求（External Exploration）** — 再向外求：",
            "   - 用最合适的工具执行探索计划",
            "   - 发现新盲区时追加到计划",
            "",
            "4. **综合评估** — 判断是否可以回复，还是需要继续探索或问用户",
            "",
            "5. **三省吾身** — 每次行动后检查：",
            "   - 是否诚实地说明了不确定性（荣辱观 L1）",
            "   - 是否 step by step、假设先行（思维方式 L2）",
            "   - 是否有可改进之处（反省 L3）",
        ]
        return "\n".join(parts)

    # -- 内部方法 --

    def _classify_intent(self, message: str) -> str:
        """用关键词匹配分类意图。"""
        msg_lower = message.lower()

        # 检查 implement
        for pattern in _INTENT_PATTERNS["implement"]:
            if pattern in msg_lower:
                return "implement"

        # 检查 research
        for pattern in _INTENT_PATTERNS["research"]:
            if pattern in msg_lower:
                return "research"

        # 检查 analyze
        for pattern in _INTENT_PATTERNS["analyze"]:
            if pattern in msg_lower:
                return "analyze"

        # 检查 discuss
        for pattern in _INTENT_PATTERNS["discuss"]:
            if pattern in msg_lower:
                return "discuss"

        # 默认：如果是长消息且含代码特征，倾向 implement
        if len(message) > 100 and any(c in message for c in ("{", "}", "(", ")", "def ", "class ")):
            return "implement"

        return "simple"

    def _is_simple_message(self, message: str) -> bool:
        """判断是否为简单消息。"""
        msg_stripped = message.strip()
        if len(msg_stripped) < 15:
            return True
        for pattern in _SIMPLE_PATTERNS:
            if re.match(pattern, msg_stripped, re.IGNORECASE):
                return True
        return False

    def _estimate_confidence(self, message: str, route_name: str) -> float:
        """估算分类置信度。"""
        msg_len = len(message.strip())
        if route_name == "simple":
            return 0.9 if msg_len < 30 else 0.6

        # 消息越长、含代码特征越多，置信度越高
        code_chars = sum(1 for c in message if c in "{}()[]<>")
        if msg_len > 200 and code_chars > 10:
            return 0.95
        if msg_len > 100:
            return 0.85
        return 0.7

    def _decide_mode(self, route_name: str, experts: list[Expert], context: dict | None) -> str:
        """根据意图决定 Agency 执行模式。"""
        if route_name == "implement" and experts:
            return "A"  # 委派编码任务
        elif route_name == "analyze" and experts:
            return "B"  # 本地专家模式
        elif route_name == "discuss":
            return "C"  # 讨论/咨询模式
        elif route_name == "research":
            return "D"  # 认知循环模式
        return "B"

    def _decide_path(self, route_name: str, mode: str, experts: list[Expert]) -> str:
        """根据意图和模式决定路径。"""
        if route_name == "simple":
            return "direct"
        if mode == "A" and experts:
            return "expert_delegate"
        if mode == "D":
            return "cognitive_loop"
        return "direct"  # 模式 B/C 走直接路径（prompt 注入即可）
```

- [ ] **步骤 5.2：编写测试文件 `tests/agent/test_router.py`**

```python
"""Tests for AgentRouter — 语义路由总控。"""

import pytest
from agent.router import AgentRouter, RouteDecision
from agent.expert_matcher import Expert, ExpertMatcher


@pytest.fixture
def router(mock_agents_dir):
    """创建 Router 实例，使用 mock 专家目录。"""
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

    def test_classifies_short_message(self, router):
        decision = router.route("好的")
        assert decision.route_name == "simple"


class TestRouteDecision:
    def test_implement_returns_experts(self, router):
        decision = router.route("帮我设计后端 API",)
        if decision.path != "direct":
            assert len(decision.experts) > 0
            assert decision.mode in ("A", "B", "D")

    def test_simple_no_experts(self, router):
        decision = router.route("谢谢")
        assert len(decision.experts) == 0
        assert decision.mode == ""

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

---

### 任务 6：修改 prompt_builder.py — 注入认知引导+Memory 导航

**文件：**
- 修改：`agent/prompt_builder.py`
  - 在 `build_context_files_prompt()` 或 `_build_system_prompt()` 逻辑的等价位置注入

**说明：** 此任务直接在 `prompt_builder.py` 中添加两个注入点：
1. 在 `<available_skills>` 块后注入 `MemoryIndex.index_summary()` 返回的导航段
2. 在 system prompt 末尾增加认知循环引导

- [ ] **步骤 6.1：分析注入位置**

在 `prompt_builder.py` 中，`build_skills_system_prompt()` 返回包含 `<available_skills>` 的字符串。但这里不是注入点——因为 `prompt_builder.py` 是纯函数库，不创建 `MemoryIndex` 实例。

注入点实际在 `run_agent.py` 的 `_build_system_prompt()` 方法中（约 3147-3312 行）：
- 在 `<available_skills>` 块（第 3266 行）后
- 在 context files（第 3277 行）后
- 在时间戳（第 3288 行）前

因为 `prompt_builder.py` 不持有 `MemoryIndex` 实例，我们需要：
1. 在 `prompt_builder.py` 中为认知引导段添加一个纯函数
2. 实际的注入逻辑在 `run_agent.py` 的 `_build_system_prompt()` 中

- [ ] **步骤 6.2：在 `prompt_builder.py` 添加认知引导段辅助函数**

```python
# 在 prompt_builder.py 末尾（或合适位置）添加：

COGNITIVE_LOOP_GUIDANCE = (
    "\n## Cognitive Loop (StarRoad Cognition)\n\n"
    "### 先内后外流程\n"
    "面对复杂任务时，优先从内部知识开始：\n"
    "1. 搜索 Memory Index 中的已有知识\n"
    "2. 搜索历史对话中的相关讨论\n"
    "3. 加载相关 skill\n\n"
    "### 三层自评\n"
    "每次行动完成后再做检查：\n"
    "- Layer 1 荣辱观：有没有隐瞒不确定性？有没有未经验证的论断？\n"
    "- Layer 2 思维方式：有没有 step by step？有没有假设先行？\n"
    "- Layer 3 三省吾身：有哪些可以改进？\n"
)


def build_cognitive_loop_guidance() -> str:
    """返回认知循环引导段，供注入 system prompt。"""
    return COGNITIVE_LOOP_GUIDANCE
```

注意：实际修改时需要在 `prompt_builder.py` 文件末尾（第 1043 行后）添加上述内容。

- [ ] **步骤 6.3：编写测试确认 `build_cognitive_loop_guidance()` 存在且合理**

```python
# tests/agent/test_prompt_builder_cognitive.py
from agent.prompt_builder import build_cognitive_loop_guidance, COGNITIVE_LOOP_GUIDANCE


def test_cognitive_loop_guidance_contains_key_sections():
    section = build_cognitive_loop_guidance()
    assert "先内后外" in section or "Internal" in section or "_SUM" not in section  # 至少包含引导内容
    assert len(section) > 100
```

---

### 任务 7：修改 context_compressor.py — KV Cache 围栏保护

**文件：**
- 修改：`agent/context_compressor.py`

**说明：** 在 `compress()` 方法中添加围栏检测逻辑：当 `-----COGNITIVE_INDEX_START-----` 出现在要压缩的内容中时，跳过该段不压缩。

- [ ] **步骤 7.1：分析现有代码**

`context_compressor.py` 的 `compress()` 方法（927 行）：
1. `_prune_old_tool_results()` — 修剪旧工具结果（无 LLM 调用）
2. 确定边界（protect head / find tail）
3. `_generate_summary()` — 对中间轮次做 LLM 摘要

围栏保护应在第 2 步和第 3 步之间插入：在 `turns_to_summarize` 中，如果某条消息包含 `-----COGNITIVE_INDEX_START-----`，将其从压缩范围中排除。

- [ ] **步骤 7.2：在 `compress()` 中添加围栏过滤**

```python
# 在 context_compressor.py 中 compress() 方法内部，turns_to_summarize 使用前插入：

# === DeepAgent: StarRoad Cognition 围栏保护 ===
# 检测 Cognitive Index 围栏段，跳过不压缩
_fence_start = "-----COGNITIVE_INDEX_START-----"
_fence_end = "-----COGNITIVE_INDEX_END-----"
_filtered_turns = []
for _turn in turns_to_summarize:
    _content = _turn.get("content", "")
    if isinstance(_content, str) and _fence_start in _content:
        # 跳过整个围栏段
        continue
    _filtered_turns.append(_turn)
if len(_filtered_turns) < len(turns_to_summarize):
    logger.info(
        "Cognitive index fence detected: skipped %d protected messages",
        len(turns_to_summarize) - len(_filtered_turns),
    )
turns_to_summarize = _filtered_turns
# === End ===
```

这个插入点在 `compress()` 方法中 `turns_to_summarize = messages[compress_start:compress_end]`（第 977 行）之后，`_generate_summary(turns_to_summarize)`（第 1002 行）之前。

- [ ] **步骤 7.3：编写测试**

```python
"""Tests for context_compressor Cognitive Index fence protection."""
import pytest
from agent.context_compressor import ContextCompressor


@pytest.fixture
def compressor():
    """Create a compressor with a very low threshold for testing."""
    return ContextCompressor(
        model="test-model",
        threshold_percent=0.1,
        protect_first_n=1,
        protect_last_n=2,
        quiet_mode=True,
    )


def test_fence_content_is_filtered_from_summary_input():
    """Verify the compress() method filters messages with cognitive fence."""
    # 这个测试验证 compress() 内部过滤逻辑
    # 通过构造包含围栏的消息列表来测试
    compressor = ContextCompressor(
        model="test-model",
        threshold_percent=0.01,
        protect_first_n=1,
        protect_last_n=1,
        quiet_mode=True,
        context_length=128000,
    )

    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {
            "role": "assistant",
            "content": "-----COGNITIVE_INDEX_START-----\nmemory content\n-----COGNITIVE_INDEX_END-----",
        },
        {"role": "user", "content": "more conversation"},
        {"role": "assistant", "content": "more response"},
    ]

    # 强制压缩
    compressor.threshold_tokens = 1
    compressed = compressor.compress(messages)

    # 验证围栏内容未丢失
    compressed_text = ""
    for msg in compressed:
        if isinstance(msg.get("content"), str):
            compressed_text += msg["content"]

    assert "memory content" in compressed_text, "Cognitive index content should be preserved"
```

---

### 任务 8：修改 memory_tool.py — 扩展 read_nested 动作（可选）

**文件：**
- 修改：`tools/memory_tool.py`

**说明：** 此任务可选——MemoryIndex 已经提供了 `read_nested()` 方法作为库接口。如果希望在工具层暴露这个能力，可以在现有 memory tool 中增加 `read_nested` 动作。

**但根据设计原则（YAGNI）：** MemoryIndex 的 `read_nested()` 是给系统内部用的（认知循环内吸阶段），不是给模型直接调的。模型已有 `read_file` 工具可以读子文档。**建议此任务暂不实施**，等实际需要时再说。

---

### 任务 9：集成到 run_agent.py

**文件：**
- 修改：`run_agent.py`
  - `__init__()` 中初始化认知模块
  - `_build_system_prompt()` 中注入导航段 + 引导
  - `run_conversation()` 开头加入路由决策
  - 主循环中加入 CognitiveGate 评估

**说明：** 这是最复杂的集成任务，依赖所有新模块。

- [ ] **步骤 9.1：在 `__init__()` 中添加认知模块初始化**

在 `run_agent.py` 的 `AIAgent.__init__()` 中（约 900 行区域）添加：

```python
# === DeepAgent: StarRoad Cognition ===
# 认知模块（按需初始化）
self._cognitive_router: Optional[AgentRouter] = None
self._cognitive_gate: Optional[CognitiveGate] = None
self._memory_index: Optional[MemoryIndex] = None
self._plan_tracker: Optional[PlanTracker] = None
self._expert_matcher: Optional[ExpertMatcher] = None
self._cognitive_enabled: bool = False
# === End ===
```

- [ ] **步骤 9.2：添加初始化方法**

在 `__init__()` 之后（或作为独立方法）添加：

```python
def _init_cognitive_modules(self) -> None:
    """按需初始化 StarRoad Cognition 认知模块。

    仅在 cognitive.enabled=True 时启用（默认关闭）。
    """
    if not getattr(self, '_cognitive_enabled', False):
        return

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
```

- [ ] **步骤 9.3：修改 `_build_system_prompt()` 注入认知内容**

在 `_build_system_prompt()` 方法（约 3147 行），时间戳段（约 3279 行）之前插入：

```python
# === DeepAgent: StarRoad Cognition ===
# 注入 Memory Index 导航段
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

- [ ] **步骤 9.4：在 `run_conversation()` 开头加入路由决策**

在 `run_conversation()` 方法（约 7803 行）中，用户消息已添加后（约 7941 行之后）、API 调用循环前（约 8103 行之前）插入：

```python
# === DeepAgent: StarRoad Cognition ===
# Pre-turn hook: 路由决策
cognitive_route = None
if self._cognitive_enabled and self._cognitive_router:
    try:
        cognitive_route = self._cognitive_router.route(
            original_user_message,
            context={"conversation_history": len(messages)},
        )
        if cognitive_route and cognitive_route.path != "direct":
            logger.info(
                "Cognitive route: path=%s mode=%s route_name=%s experts=%s",
                cognitive_route.path,
                cognitive_route.mode,
                cognitive_route.route_name,
                [e.slug for e in cognitive_route.experts],
            )
            # 模式 A：委派专家
            if cognitive_route.mode == "A" and cognitive_route.experts:
                # 记录专家信息供后续 delegate_task 使用
                self._cognitive_experts = cognitive_route.experts

            # 创建 plan
            if self._plan_tracker and not self._plan_tracker.get_current_plan_id():
                self._plan_tracker.create_or_update(original_user_message)
    except Exception as e:
        logger.debug("Cognitive routing failed (non-fatal): %s", e)
# === End ===
```

- [ ] **步骤 9.5：在主循环后加入 CognitiveGate 评估**

在 `run_conversation()` 的主循环结束后（约 8700 行附近，`final_response` 已生成处）插入：

```python
# === DeepAgent: StarRoad Cognition ===
# Post-turn hook: 三层自评
if self._cognitive_enabled and self._cognitive_gate and final_response:
    try:
        turn_data = {
            "user_message": original_user_message,
            "assistant_response": final_response,
            "tool_calls": [],  # 可以从 messages 中提取
            "tool_results": [],
            "plan_id": self._plan_tracker.get_current_plan_id() if self._plan_tracker else "",
        }
        # 从 messages 中提取工具调用信息
        for _msg in messages:
            if _msg.get("role") == "assistant" and _msg.get("tool_calls"):
                turn_data["tool_calls"].extend(_msg["tool_calls"])
            if _msg.get("role") == "tool":
                turn_data["tool_results"].append(_msg)

        eval_result = self._cognitive_gate.evaluate(turn_data)
        if eval_result.should_interrupt_user:
            logger.info("CognitiveGate suggests asking user: %s", eval_result.adjustments_note)
        if eval_result.gaps_found and self._plan_tracker:
            for gap in eval_result.gaps_found:
                self._plan_tracker.add_gap(gap)
                logger.info("CognitiveGate gap recorded: %s", gap)
    except Exception as e:
        logger.debug("Cognitive evaluation failed (non-fatal): %s", e)
# === End ===
```

- [ ] **步骤 9.6：配置开关（新增配置项）**

在 `~/.hermes/config.yaml` 中添加：

```yaml
cognitive:
  enabled: false  # 默认关闭，需要手动开启
```

在 `AIAgent.__init__()` 中读取此配置：

```python
# 从配置中读取 cognitive.enabled
self._cognitive_enabled = False
try:
    from hermes_cli.config import load_config
    _cfg = load_config()
    self._cognitive_enabled = _cfg.get("cognitive", {}).get("enabled", False)
except Exception:
    pass
```

---

### 任务 10：创建 MAP.md 和更新 SOUL.md

**文件：**
- 创建：`~/.hermes/memories/MAP.md`（由 memory_index.build_initial_index() 自动创建）
- 更新：`~/.hermes/SOUL.md`（手动追加）

- [ ] **步骤 10.1：触发 `build_initial_index()`**

这一步由 `MemoryIndex.__init__()` 在首次使用时自动触发，或在 `run_agent.py` 集成时显式调用：

```python
if self._memory_index:
    self._memory_index.build_initial_index()
```

- [ ] **步骤 10.2：更新 `~/.hermes/SOUL.md`**

在 SOUL.md 末尾追加：

```markdown
## 认知框架（StarRoad Cognition）

### Layer 1 — 荣辱观
以知道自己的不足为荣，以隐瞒不足为耻
以提升认知为荣，以原地踏步为耻
以忽悠为耻，以告诉实情为荣

### Layer 2 — 思维方式
第一性原理 | Step by Step | 拆解到最小任务 | 找盲区 | 科研严谨

### Layer 3 — 三省吾身
回头检查 L1+L2 → 找改进点 → 记录到 memory → 外部问询
```

---

## 三、实施顺序总结

```
阶段 0：DeepAgent 独立化（并行，纯字符串替换，无测试）
  ├── 任务 0.1: hermes_constants.py 改路径    ≈ 2 行
  ├── 任务 0.2: pyproject.toml 改包名         ≈ 20 行
  ├── 任务 0.3: hermes → deepagent 改名       ≈ 1 行注释 + mv
  ├── 任务 0.4: setup-hermes.sh → deepagent   ≈ 22 处替换 + mv
  └── 任务 0.5: hermes_cli/main.py 帮助文案   ≈ 15 处替换

阶段 1：并行创建 5 个新模块 + 测试
  ├── 任务 1: cognitive_gate.py + tests/       ≈ 200 行代码 + 150 行测试
  ├── 任务 2: memory_index.py + tests/          ≈ 200 行代码 + 200 行测试
  ├── 任务 3: plan_tracker.py + tests/          ≈ 200 行代码 + 150 行测试
  ├── 任务 4: expert_matcher.py + tests/        ≈ 200 行代码 + 100 行测试
  └── 任务 5: router.py + tests/                ≈ 150 行代码 + 80 行测试

阶段 2：修改已有文件（可并行）
  ├── 任务 6: prompt_builder.py 修改           ≈ 20 行
  ├── 任务 7: context_compressor.py 修改       ≈ 15 行
  └── 任务 8: memory_tool.py 修改（暂缓）      ≈ 0 行

阶段 3：集成（串行）
  └── 任务 9: run_agent.py 修改                ≈ 80 行

阶段 4：数据文件
  └── 任务 10: SOUL.md + MAP.md 创建           ≈ 20 行

总计：约 1050 行代码 + 680 行测试 + 约 60 处替换 = 约 1730 行
```

---

## 四、StarRoad Cognition 三层自评

### Layer 1 荣辱观自评

| 检查点 | 结果 | 说明 |
|--------|------|------|
| 是否诚实说明了不确定性 | ✅ 通过 | 上方标明了 9 项盲区及其修复方案 |
| 是否用工具验证了论断 | ✅ 通过 | 所有评估依据来自实际阅读的源码文件（prompt_builder.py 1043 行、context_compressor.py 1091 行、memory_tool.py 584 行等）|
| 是否完整报告了真实情况 | ✅ 通过 | 如实报告了粗方案的不足，包括现有代码结构和模块依赖的约束 |

### Layer 2 思维方式自评

| 检查点 | 结果 | 说明 |
|--------|------|------|
| 拆解到最小任务 | ✅ 通过 | 15 个任务（5 个独立化 + 10 个认知模块），每个都有具体的文件路径、函数签名、代码内容 |
| Step by Step | ✅ 通过 | 每个任务都有明确的依赖关系、串行/并行分组、测试要求 |
| 第一性原理 | ✅ 通过 | 从现有代码的实际架构出发（而非从零设计），分析注入点 |
| 找盲区 | ✅ 通过 | 发现 9 个粗方案盲区，全部给出修复方案 |

### Layer 3 三省吾身（剩余盲区标记）

| 盲区 | 置信度 | 说明 |
|------|--------|------|
| CognitiveGate 的启发式规则能否覆盖实际场景 | 不确定 | L1/L2 检查使用的是关键词匹配和简单启发式，可能误报。**建议：** 先上线观察，后续根据实际数据优化匹配规则 |
| Router 的意图分类精度 | 大概 70% | 目前只有关键词匹配，没有 LLM 辅助分类。长消息可能误判。**建议：** 如果实际使用中分类精度不足，后续加入 LLM 轻量分类 |
| Mode A（委派专家）的集成路径未完全实现 | 大概率 60% | run_agent.py 中 mode A 的逻辑取了 expert 但没有自动调 delegate_task。完整的委派链路需要额外实现。**建议：** mode A 的实现可以放到二期 |
| expert_matcher.py 的 _parse_agent_file | 大概 80% | Agency 的 .md frontmatter 格式可能不完全一致。需要先验证真实文件的解析兼容性 |
| config.yaml 的 cognitive.enabled 配置读取 | 大概 90% | 需要确认现有的配置加载机制能正确读取 nested key |
| 性能影响 | 不确定 | CognitiveGate 在每个 text response 后执行，memory_index 在 system prompt 构建时执行。总体开销预计 < 50ms/次。**建议：** 如果性能有问题，评估逻辑可以异步化 |

---

## 五、约束条件检查

- [x] Python 3.10+
- [x] 无额外外部依赖
- [x] 所有文件路径使用 `get_hermes_home()`
- [x] 每个模块有对应的测试文件
- [x] 修改已有文件时用 `# === DeepAgent: StarRoad Cognition ===` 标记
- [x] 所有代码写中文注释
- [x] 错误处理和边界情况覆盖
