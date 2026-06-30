# StarRoad Cognition — 粗框架实现方案

## 项目概述

在 Hermes Agent v0.17.0 基础上实现三层认知引擎架构，命名为 **StarRoad Cognition**（星辰路认知法），包含三层认知引擎、认知循环流程（先内后外）、Memory 嵌套索引、Plan 状态机、The Agency 专家自动匹配和 KV Cache 保护。

## 核心参考文档

**务必先读以下文件，理解已有设计后再动手：**

1. `~/.hermes/skills/autonomous-ai-agents/the-agency/SKILL.md` — The Agency 232 专家库的完整匹配逻辑和 4 种执行模式（A/B/C/D）
2. `~/.hermes/skills/autonomous-ai-agents/the-agency/references/cognitive-workflow.md` — 三层认知框架、认知循环、Memory 嵌套索引、Plan 状态机的完整文档定义（本文档的绝大部分设计在此已有定义）
3. 本项目的 `STARROAD_COARSE_PLAN.md` — 粗框架方案（即本文档）

**核心原则：cognitive-workflow.md 已经有了完整的框架定义，实现层的工作是把它从文档翻译成代码，而不是重新设计。**

---

## 三层认知框架

### Layer 1: 荣辱观（价值过滤器）

所有 action 前和 action 后的门控检查：

| 原则 | 检查点 | 示例 |
|------|--------|------|
| 以知道自己的不足为荣 | 每次行动前是否诚实说明了不确定性 | "我对这个模块不熟悉，先查一下" |
| 以隐瞒不足为耻 | 是否主动暴露了盲区 | 禁止假装懂一个没查过的方向 |
| 以提升认知为荣 | 每次探索后是否收获了新认知 | "我发现了X，这将影响方案设计" |
| 以忽悠为耻 | 是否用工具验证了每个论断 | 禁止凭感觉回答需要查证的问题 |
| 以告诉实情为荣 | 是否完整报告了真实情况（含失败） | 工具调用失败要如实报告，不是绕过 |

### Layer 2: 思维方式（方法论框架）

| 方法 | 含义 | 应用 |
|------|------|------|
| 第一性原理 | 拆到不能再拆为止 | 不是翻文档找参数，而是理解这个参数为什么存在 |
| Step by Step | 每一步都有明确输入输出 | 不跳步骤，不"顺便"做多件事 |
| 拆解到最小任务 | 一个 task 只做一件事 | Plan 中的每一项都是 atomic 的 |
| 找盲区 | 主动识别自己的认知边界 | "这个方向我不确定，需要查" |
| 科研严谨 | 假设先行，验证后行 | 先说"我认为应该是X因为Y"再验证，不是"试一下" |

### Layer 3: 三省吾身（反省循环）

每次行动完成后：
1. 回头检查 L1+L2 — 刚才的行为是否符合荣辱观和思维方式？
2. 找改进点 — 即使结果正确，过程中有没有可优化的？
3. 记录到 memory — 把发现的盲区/经验存入索引，供下次参考
4. 外部问询 — 对真正不懂的方向，用工具搜索或问用户

---

## 三路由层架构

整个新代码的消息处理流程：

```
消息入口（用户输入）
  │
  ▼
┌─────────────────────────────────────┐
│ Route 1: 语义路由器 (Intent Router)  │ ← agent/router.py
│ 分类: discuss / implement / analyze  │
│       / research / simple            │
│ 输出: route_name + confidence       │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌────────────┐   ┌──────────────┐
│ simple     │   │ 复杂任务      │
│ (直走原流程)│   │ (进入认知循环)│
└────────────┘   └──────┬───────┘
                        ▼
┌────────────────────────────────────────┐
│ Route 2: 专家匹配器 (Expert Matcher)    │ ← agent/expert_matcher.py
│ 基于 route_name + 关键词 → 匹配 Agency  │
│ 返回 top 1-2 个专家（主+交叉验证）      │
└──────────────────┬─────────────────────┘
                   ▼
┌────────────────────────────────────────┐
│ Route 3: 执行路由 (Execution Router)    │ ← agent/router.py
│ 决定执行模式:                           │
│ A: delegate_task（委派编码任务）        │
│ B: 本地专家（直接加载专家 prompt）      │
│ C: 讨论/咨询（以专家 lens 对话）        │
│ D: 认知循环（完整的内吸→外求→自评）    │
└──────────────────┬─────────────────────┘
                   ▼
         ┌──────────────────┐
         │ Agent Loop       │ ← 现有 run_agent.py
         │ + 认知循环注入    │
         └──────────────────┘
```

### Agency 的 4 种执行模式（已在 SKILL.md 中定义）

**模式 A：委派编码任务** — 适用于实现/构建
- 确定最佳 agent → 读取其 system prompt → delegate_task 注入 context → 执行

**模式 B：本地专家模式** — 适用于分析/审查/策略
- 确定最佳 agent → 读取其 system prompt → 直接加载到上下文 → 以该视角执行

**模式 C：讨论/咨询模式** — 适用于方向讨论/头脑风暴
- 识别讨论领域 → 匹配专家 → 公告视角 → 以该 lens 引导对话（澄清→发散→收敛）

**模式 D：认知循环模式** — 适用于复杂探索任务
- 完整的 内吸 → 形成探索计划 → 外求 → 三层自评 → 循环直到退出条件

---

## 完整认知循环流程（阶段 0-5）

### 阶段 0: 接收消息
```
收到用户消息
  → 语义理解（是什么类型的任务？讨论/实现/分析/调研？）
  → 判断是否进入认知循环（复杂任务 → 进循环；简单任务 → 正常执行）
```

### 阶段 1: 内吸（Internal Recall）—— 先向内求
```
并行动作：
  → 搜索 Memory Index（~/.hermes/memories/）— 找到已有的知识领域索引
  → 搜索 Session DB（state.db FTS5）— 历史对话中有无相关讨论
  → 扫描 Skill Index（<available_skills> 块）— 加载相关 skill
  → 按需加载子文档（通过 skill_view / read_file 读取导航指向的具体文档）

输出：
  → 已知清单（已经确认了的方向）
  → 盲区清单（还不确定的方向）
  → 探索计划草案（下一步需要查什么）
```

### 阶段 2: 形成探索计划
```
基于内吸结果：
  → 将盲区转化为具体的探索任务
  → 按优先级排序（对当前任务影响最大的优先）
  → 写入 todo / plan 系统
  → 如果需要，加载 Agency 专家辅助制定探索方向

输出：
  → 结构化探索计划（3-8个探索项）
```

### 阶段 3: 外求（External Exploration）—— 再向外求
```
逐项执行探索计划：
  → 每项使用最合适的工具：
    - 搜索技术方向 → web_search
    - 查开源项目 → web_search + GitHub API
    - 读论文 → arxiv + paper-translation skill
    - 查代码 → 直接读目标仓库
  → 每项完成后立即三层自评
  → 发现新的盲区 → 追加到探索计划（计划是动态的）

输出：
  → 每项的答案/结论
  → 新的盲区（追加到计划）
  → 对原始问题的认知更新
```

### 阶段 4: 综合评估
```
基于所有探索结果：
  → 综合所有已知信息
  → 对照用户原始问题的要求
  → 三层自评：答案是否满足L1/L2/L3？
  → 判断退出条件：
    - ① 达到边界（需要用户决策）→ 问用户
    - ② 用户打断 → 接受打断，继续处理
    - ③ 可以给第一轮回复了 → 出回复
```

### 阶段 5: 动态迭代
```
如果选择继续探索（不退出）：
  → 回到阶段1（内吸），但此时已有更多上下文
  → 循环正常继续

如果发现需要调整任务目标：
  → 识别差距（用户认知 vs 实际情况）
  → 微调目标：「从出方案 → 先帮用户补认知再出方案」
  → 更新 Plan + 更新 todo
  → 继续循环

如果选择回复用户：
  → 结构化回复（现状分析/探索结果/待决策点）
  → 输出到 product-rd-workflow 阶段 0 对接
```

### 退出条件判断矩阵

| 条件 | 判断依据 | 动作 |
|------|---------|------|
| 达到边界（需用户决策） | 探索后发现存在多个可行方向，需要用户拍板 | 出中间结果 + 问用户选哪个 |
| 用户主动打断 | 用户发来新的消息（非请求继续） | 停止当前探索，处理新消息（插入链条向下） |
| 可以给第一轮回复 | ① L1/L2/L3 评估通过 ② 已形成完整理解 | 结构化回复给用户 |

---

## 需新增的5个模块

### 1. agent/cognitive_gate.py — 三层认知评估器

```python
class CognitiveGate:
    """三层认知评估器。在 agent loop 每个 turn 后触发，输出三层评估结果。"""

    def evaluate(self, turn_data: dict, eval_history: list) -> dict
        # 返回 {honor_result, thinking_result, reflection, gaps, adjustments,
        #        should_interrupt, should_explore, plan_adjustments}

    def _check_honor(self, turn_data) -> HonorResult
        """Layer 1 荣辱观检查：有没有隐瞒不确定性？有没有忽悠？
           有没有诚实报告工具失败？"""

    def _check_thinking(self, turn_data) -> ThinkingResult
        """Layer 2 思维方式检查：是不是 step by step？
           有没有假设先行？有没有拆到最小任务？
           返回 blindspots（盲区清单）"""

    def _reflect(self, honor, thinking, history) -> Reflection
        """Layer 3 三省吾身：回头检查 L1+L2 → 找改进点 → 记录到 memory
           返回 gap_analysis, plan_adjustments, goal_adjustments"""

    def _should_ask_user(self, reflection) -> bool
        """判断不确定性是否超过阈值，需要中断问用户"""

    def get_recent_evaluations(self, n: int) -> list
        """返回最近 n 次评估记录"""
```

### 2. agent/memory_index.py — 记忆嵌套索引管理器

```python
class MemoryIndex:
    """Memory 嵌套索引管理器。
    核心规则：MAP.md 只存导航指引（1-2KB），深度内容存在于子文档按需加载。"""

    def __init__(self, index_path: str = "~/.hermes/memories/MAP.md")

    def read_nested(self, path: str) -> str
        """从 MAP.md 索引导航读取子文档内容。
           例: read_nested('deepseek-physics')  → 找到索引, 加载 skills/SKILL.md"""

    def navigate(self, topic: str) -> list[str]
        """搜索 MAP.md 找到与 topic 相关的索引条目"""

    def suggest_docs(self, query: str) -> list[str]
        """基于查询推荐需要加载的子文档路径"""

    def index_summary(self) -> str
        """返回注入 system prompt 的导航段（短文本，1-2KB）。
           用 -----COGNITIVE_INDEX_START----- 包裹"""

    def update_entry(self, topic: str, path: str, description: str)
        """更新或新增索引条目"""

    def build_initial_index(self)
        """首次初始化时读取现有 ~/.hermes/memories/ 下的文件构建 MAP.md"""
```

### 3. agent/plan_tracker.py — 计划状态机

```python
class PlanTracker:
    """Plan 状态机管理器。plan 不只是 markdown 文件，是一个动态状态机。
    JSON 持久化到 ~/.hermes/plans/<id>.json"""

    def __init__(self, plans_dir: str = "~/.hermes/plans/")
    def create_or_update(self, goal: str, tasks: list) -> str  # 返回 plan_id
    def mark_done(self, task_id: str)
    def add_gap(self, gap: str)  # 探索中发现的盲区追加到计划
    def refine_goal(self, new_goal: str)  # 发现用户认知不够时调整目标
    def get_status(self) -> dict  # 返回注入 system prompt 的当前 plan 状态
    def load_plan(self, plan_id: str) -> dict
    def list_plans(self) -> list
    def validate_plan(self, plan: dict) -> bool  # 校验 plan 结构完整性
```

Plan JSON 数据格式：
```json
{
  "plan_id": "unique-id",
  "goal": "原始目标（可调整）",
  "goal_history": ["v1: 初始目标", "v2: 调整后目标"],
  "status": "in_progress",
  "current_task": "当前正在做的任务ID",
  "tasks": [
    {"id": "t1", "desc": "任务描述", "status": "done"},
    {"id": "t2", "desc": "任务描述", "status": "in_progress"},
    {"id": "t3", "desc": "任务描述", "status": "pending"}
  ],
  "gaps_found": ["探索中发现的盲区"],
  "created_at": "ISO时间戳",
  "updated_at": "ISO时间戳"
}
```

动态调整规则：
1. 发现盲区 → 追加探索任务（不必改 Plan 文件，用 todo 追踪即可）
2. 发现用户认知与实际情况差距大 → 调整 goal，优先补认知
3. 已经做完的任务标记 done，不做回顾性重写

### 4. agent/expert_matcher.py — 专家匹配器

```python
class Expert:
    """专家对象"""
    slug: str       # 如 "software-architect"
    name: str       # 如 "Software Architect"
    division: str   # 如 "Engineering"
    prompt: str     # 完整的 system prompt（从 .md 文件读取）

class ExpertMatcher:
    """对接 The Agency 的 232 专家库。根据 route_name + 关键词匹配最佳专家。"""

    def __init__(self, agents_dir: str = "~/.config/opencode/agents/")

    def match(self, message: str, route_name: str) -> list[Expert]
        """根据 route_name + 关键词查找最匹配的 Agency 专家。
           返回 top 1-2 个专家（主专家 + 交叉验证专家）"""

    def match_for_mode(self, message: str, mode: str) -> Expert
        """根据 Agency 4 种模式（A/B/C/D）匹配对应专家"""

    def load_expert_prompt(self, slug: str) -> str
        """读取对应 .md 文件，提取 system prompt 内容"""

    def get_available_experts(self) -> list[dict]
        """返回所有可用专家的摘要列表（slug + name + description）"""

    def build_expert_registry(self) -> dict
        """构建专家注册表（slug → Expert 的映射）"""

    def get_experts_for_division(self, division: str) -> list[Expert]
        """按 division 获取专家列表"""
```

匹配逻辑基于 The Agency 的决策矩阵（SKILL.md 已定义的 16 个 division × 232 agents）。

认知循环中调用 Agency 专家的时机：

| 认知阶段 | 调用专家方式 |
|---------|------------|
| 内吸（形成探索计划时） | 加载架构师/研究员类专家，帮助梳理盲区、制定探索方向 |
| 外求（执行具体探索时） | 按领域加载对应专家（如调研 GitHub 项目加载 software-architect） |
| 评估（验证答案时） | 加载对立视角的专家做交叉验证（如 security-architect 验证架构安全性）|
| 目标调整（发现认知不足时） | 加载 trend-researcher 或 product-manager，帮助重新框定问题 |

### 5. agent/router.py — 语义路由总控

```python
class RouteDecision:
    """路由决策结果"""
    path: str       # 'direct' | 'cognitive_loop' | 'expert_delegate'
    mode: str       # 'A' | 'B' | 'C' | 'D'（对应 Agency 4 种模式）
    route_name: str # 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
    experts: list[Expert]
    confidence: float  # 0.0-1.0

class AgentRouter:
    """消息路由总控。决定消息走哪条处理路径。"""

    def __init__(self, expert_matcher: ExpertMatcher)

    def route(self, message: str, context: dict) -> RouteDecision
        """主路由方法：
           1. 分类意图
           2. 简单任务 → path='direct'
           3. 复杂任务 → 匹配专家 → 决定执行模式 A/B/C/D"""

    def _classify_intent(self, message: str) -> str
        """用关键词匹配 + LLM 轻量判断。
           返回: 'discuss' / 'implement' / 'analyze' / 'research' / 'simple'"""

    def _decide_path(self, route_name: str, confidence: float) -> str
        """根据意图和置信度决定走哪条路径"""
```

---

## 现有代码集成点（必须修改的文件）

### 1. agent/prompt_builder.py — 注入认知循环引导和 Memory 导航

修改 `_build_system_prompt()` 方法：
- 在 `<available_skills>` 块后注入 `MemoryIndex.index_summary()` 返回的导航段
- 导航段用 `-----COGNITIVE_INDEX_START-----` / `-----COGNITIVE_INDEX_END-----` 围栏包裹
- 在现有 system prompt 末尾增加约 300 字段的 Cognitive Loop 引导（先内后外流程简述）

### 2. agent/context_compressor.py — KV Cache 顺序保护

在 `compress()` 或 `summarize_or_skip_conversation()` 方法中：
- 检测 `-----COGNITIVE_INDEX_START-----` 到 `-----COGNITIVE_INDEX_END-----` 围栏
- 围栏段被检测到时**跳过不压缩**（保持索引内容完整）
- 只压缩用户对话轮次
- 已有 [CONTEXT COMPACTION] 围栏逻辑可作为参考

### 3. tools/memory_tool.py — 增加嵌套读支持

在现有 memory tool 中增加 `read_nested` 动作（或扩展 `read` 动作支持 `path` 参数）：
- 参数: `path` (str) — MAP.md 中的导航路径标识
- 行为: 解析 MAP.md → 找到 path 对应的目标文件 → 读取并返回内容
- 保留现有 `add/replace/remove/read` 动作不变

### 4. run_agent.py — 插入认知循环的 hook points

在 agent loop 主循环中插入两个 hook：
- **Pre-turn hook**（`_get_response()` 之前）：调用 AgentRouter.route() 决定路径
- **Post-turn hook**（每个 turn 后）：调用 CognitiveGate.evaluate() 做三层自评

```python
# Pre-turn hook — 在 _get_response() 之前
if hasattr(self, 'cognitive_router'):
    route_decision = self.cognitive_router.route(user_message, context)
    if route_decision.path == 'cognitive_loop':
        # 注入专家 prompt 到 system prompt
        for expert in route_decision.experts:
            self._inject_expert_prompt(expert)
        # 创建 plan
        self.plan_tracker.create_or_update(...)

# Post-turn hook — 在 tool dispatch 之后
if hasattr(self, 'cognitive_gate'):
    eval_result = self.cognitive_gate.evaluate(turn_data)
    if eval_result.should_interrupt:
        # 问用户
    elif eval_result.should_explore:
        # 追加探索任务
        self.plan_tracker.add_gap(gap)
```

### 5. ~/.hermes/SOUL.md — 写入三层原则定义

```
## 认知框架 (StarRoad Cognition)

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

## 需创建的数据文件

### ~/.hermes/memories/MAP.md（导航索引文件）
```markdown
# 记忆索引 (导航层)
## 关键知识领域
- deepseek-physics: skills/deepseek-physics/SKILL.md
- agent-architecture: paper-notes/agent-patterns.md
- testing-conventions: docs/test-conventions.md

## 项目状态
- openstudy: ~/Code/miniappStudyTools/AGENTS.md
- fangzhou-25: ~/Code/fangzhouzhongce/第25期_bluth/

## 用户偏好
- 称呼: 小路
```

---

## 关键设计决策

1. **所有新模块不替换现有代码** — 通过 hook points 插入 agent loop
2. **Memory Index 不做全量存储** — MAP.md 只存导航指引（1-2KB），深度内容存在于子文档
3. **旧 session 内容不搬进 memory** — 通过 `session_search` 检索 state.db
4. **Plan 状态机使用 JSON 文件持久化** — 轻量，无外部依赖
5. **专家匹配基于 The Agency 的 232 个专家** — 从 ~/.config/opencode/agents/ 读取 .md
6. **KV Cache 保护使用围栏标记** — 不改变现有压缩逻辑，只跳过索引段
7. **三层评估是后处理的** — 不 block 主循环，只追加调整建议和记录
8. **cognitive-workflow.md 是框架定义的权威来源** — 先读它，不重复设计

## 约束条件

1. Python 3.10+，无额外外部依赖
2. 所有文件路径使用 `get_hermes_home()` 而非硬编码 `~/.hermes`
3. 新增模块保持独立可测试，每个模块有对应的测试文件
4. 修改已有文件时用 `# === DeepAgent: StarRoad Cognition ===` 标记
5. 每个 commit 只做一件事
6. 所有代码写中文注释，让刚毕业的大学生都能看懂并维护
7. 先读 The Agency 的 `references/cognitive-workflow.md` 确保复用已有定义
8. 所有错误处理和边界情况必须覆盖（文件不存在、路径错误、空内容等）
9. 模型切换：实现任务用 opencode/deepseek-v4-flash-free（便宜），复杂架构决策用 opencode-go/deepseek-v4-pro

## 参考文件（需提前阅读）

- ~/Code/DeepAgent/agent/memory_manager.py（现有 memory 系统）
- ~/Code/DeepAgent/agent/prompt_builder.py（system prompt 组装逻辑）
- ~/Code/DeepAgent/agent/context_compressor.py（压缩逻辑，需加围栏保护）
- ~/Code/DeepAgent/tools/memory_tool.py（现有 memory 工具）
- ~/Code/DeepAgent/tools/session_search_tool.py（FTS5 检索）
- ~/Code/DeepAgent/tools/delegate_tool.py（subagent 委派）
- ~/Code/DeepAgent/agent/skill_utils.py（skill 索引系统）
- ~/Code/DeepAgent/toolsets.py（工具集注册）
- ~/.hermes/skills/autonomous-ai-agents/the-agency/SKILL.md（The Agency 专家库）
- ~/.hermes/skills/autonomous-ai-agents/the-agency/references/cognitive-workflow.md（认知框架的完整文档定义）

## 实施顺序

```
第一步：读参考文件，理解现有代码结构
第二步：创建 5 个新模块（可并行）：
  ├─ cognitive_gate.py（独立）
  ├─ memory_index.py（独立）
  ├─ plan_tracker.py（独立）
  ├─ expert_matcher.py（独立）
  └─ router.py（依赖以上 4 个）
第三步：修改 3 个已有文件：
  ├─ prompt_builder.py（注入认知引导+Memory导航）
  ├─ context_compressor.py（KV Cache 围栏保护）
  └─ memory_tool.py（嵌套读支持）
第四步：集成到 run_agent.py（加 hook points）
第五步：创建 MAP.md 和初始 Memory 嵌套结构
第六步：跑 pytest 验证 + 集成测试
```
