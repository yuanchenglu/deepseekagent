# DeepAgent 产品经理维护方案

## 写给产品经理/维护者

这份文档帮助没有深厚技术背景的产品经理理解代码结构、知道如何新增功能、排查常见问题。

---

## 一、如何快速理解代码结构

### 1.1 从哪里开始看

如果你第一次接触这个项目，按以下顺序阅读：

1. **README.md** — 项目是什么、怎么启动
2. **docs/ARCHITECTURE.md** — 系统架构和核心数据流（本文件同目录）
3. **deepagent_harness/__init__.py** — 看导出了哪些模块，了解Harness层的全部组件
4. **deepagent_harness/README.md** — Harness层模块说明

### 1.2 关键目录索引

| 目录/文件 | 是什么 | 产品视角 |
|-----------|--------|---------|
| `deepagent_harness/` | Harness层核心（10个模块） | DeepAgent的"大脑优化层"，决定Agent的智能水平 |
| `run_agent.py` | Agent核心对话循环 | 主程序，所有功能最终都在这里串联 |
| `cli.py` | 命令行界面 | 用户敲`deepagent`命令时看到的东西 |
| `tools/` | 工具实现 | Agent能调用的能力（文件、终端、网络等） |
| `deepagent_code_mode/` | Code Mode隔离层 | 研发任务自动派发给内置OpenCode小组 |
| `tests/test_harness_*.py` | Harness层单元测试 | 改完代码跑一下这些，确保没改坏 |
| `docs/` | 文档目录 | 你现在看的东西都在这里 |

### 1.3 十个Harness模块一句话解释

| 模块文件 | 一句话解释 |
|---------|-----------|
| `scene_router.py` | 判断用户要做什么类型的事（写代码/做研究/问问题/搞部署） |
| `intent_router.py` | 更细粒度判断任务类型（重构/新建/架构决策/简单问答...），决定做多深 |
| `prefix_manager.py` | 把系统提示词"冻住"不随便改，省token还跑得快 |
| `hard_constraint.py` | 自动找出用户说的"必须""禁止"这些硬要求，放在最显眼位置 |
| `model_router.py` | 简单问题用便宜模型，复杂问题自动升级贵模型，省钱还保证质量 |
| `reasoning_manager.py` | 模型的"思考过程"该留就留该删就删，不浪费token |
| `immune_system.py` | 干完活自动检查有没有违反用户的硬要求，违反了自动记住下次不犯 |
| `starroad_cognition.py` | 三层"价值观"：什么不能做、怎么做最好、干完怎么自省 |
| `context_layout.py` | 重要信息放在模型"眼前"，不被挤到看不见的地方 |
| `tool_schema_stabilizer.py` | 工具描述保持稳定不瞎变，让缓存命中省成本 |
| `bidirectional_primitives.py` | 模型能主动"举手"：要更多信息、要更强模型、要自我检查 |

---

## 二、如何新增功能

### 2.1 新增一个意图类型（如"创作类任务"）

**改动文件**：仅需改 2 个文件

1. **deepagent_harness/intent_router.py**：
   - 在 `IntentType` 枚举加一个值：`CREATIVE = "creative"`
   - 在 `INTENT_STRATEGIES` 加一条策略配置（面谈深度/计划粒度/审查标准/模型层级）
   - 在 `_INTENT_KEYWORDS` 加触发词：如「写小说/创作/写文案/写诗」
   - 在 `scene_to_intent` 映射表加默认映射

2. **deepagent_harness/starroad_cognition.py**：
   - 在 `L2_METHODS` 加 `"creative"` 对应的方法论清单

**验证**：
```bash
source .venv/bin/activate
python3 -m pytest tests/test_harness_intent_router.py -v -o "addopts="
```

**预期**：测试通过，你说"帮我写一首诗"会被识别为creative意图。

### 2.2 新增一条硬约束关键词

**改动文件**：1个文件

**deepagent_harness/hard_constraint.py**：
- 禁止类词加在 `_PROHIBITION_PATTERNS`
- 必须类词加在 `_REQUIREMENT_PATTERNS`
- 如果是误匹配场景，加过滤规则到 `_FALSE_POSITIVE_PATTERNS`

### 2.3 新增一个模型路由升级条件

**改动文件**：1个文件

**deepagent_harness/model_router.py**：
- 在 `UPGRADE_CONDITIONS` 字典加一条：
  ```python
  "your_condition_key": (
      "人类可读的升级原因",
      lambda ctx: ctx.get("your_field", 0) > THRESHOLD,
  ),
  ```

### 2.4 新增一个工具（Tool）

**改动文件**：1个新文件 + 1处注册

1. 在 `tools/` 目录创建 `your_tool.py`，参考已有工具的写法
2. 工具会通过 `tools/registry.py` 自动发现注册
3. 不需要改其他文件！

### 2.5 新增一个双向元指令

**改动文件**：1个文件

**deepagent_harness/bidirectional_primitives.py**：
- 在 `META_DIRECTIVE_TOOLS` 列表加工具schema
- 在 `_TOOL_NAME_TO_TYPE` 加映射
- 在 `BidirectionalPrimitives.handlers` 加处理函数
- 如果需要调用其他Harness模块，在 `__init__` 注入

---

## 三、常见问题排查

### 3.1 测试不通过怎么办

```bash
# 跑所有Harness测试
source .venv/bin/activate
python3 -m pytest tests/test_harness_*.py -v -o "addopts="

# 跑单个文件
python3 -m pytest tests/test_harness_prefix_manager.py -v -o "addopts="
```

如果是你改坏的，看哪个测试FAIL，回查你改的代码。
如果是之前就FAIL的，记录到 `docs/BUG_LIST.md`。

### 3.2 Agent不听用户的硬约束（"不要用X"结果还是用了）

检查点：
1. `hard_constraint.py` 的正则是否匹配到了用户的约束词？
2. 约束是否正确注入到了System Prompt？
3. 免疫系统是否检测到违反？

快速验证：
```python
from deepagent_harness import extract_hard_constraints, format_constraints_for_prefix
constraints = extract_hard_constraints("禁止使用外部API，必须用中文回复")
print(format_constraints_for_prefix(constraints))
```

### 3.3 模型成本太高/响应太慢

检查点：
1. `model_router.py` 是否正确路由到了Flash？简单问题不应该用Pro
2. `reasoning_manager.py` 是否正确剥离了无用reasoning？
3. `prefix_manager.py` 是否冻结成功？缓存命中应该很高

看统计：
```python
# 在Agent运行后查看Harness诊断
# （run_conversation返回的result中有harness_stats字段）
```

### 3.4 上下文太长模型"忘事"

检查点：
1. `context_layout.py` 是否注入了Task Anchor？
2. 硬约束是否在冻结前缀区？（应该在，不会被压缩冲走）
3. L1荣辱观是否在冻结前缀区？

### 3.5 怎么确认Harness模块真的在工作？

快速烟雾测试：
```python
from deepagent_harness import *

# 测试各模块能正常导入和实例化
pm = PrefixManager()
he = HardConstraintExtractor()
mr = ModelRouter()
rm = ReasoningManager()
ir = IntentRouter()
ims = ImmuneSystem()
sr = StarRoadCognition()
clm = ContextLayoutManager()
bp = BidirectionalPrimitives(prefix_manager=pm, model_router=mr, starroad=sr)

print("All Harness modules loaded OK!")

# 测试意图识别
intent, strategy = ir.classify_and_get_strategy("帮我重构这个模块")
print(f"Intent: {intent.value}, model_hint: {strategy.model_tier_hint}")
```

---

## 四、配置说明

### 4.1 Harness配置位置

用户配置文件：`~/.deepagent/config.yaml`

Harness相关配置段：
```yaml
deepseek_routing:
  enabled: true              # 是否启用智能路由（默认true）
  flash_model: "deepseek-v4-flash"
  pro_model: "deepseek-v4-pro"
  flash_first: true          # Flash优先策略
```

### 4.2 如何关闭某个Harness特性

当前所有Harness模块默认启用。如果需要禁用：
- 在 `run_agent.py` 的Harness初始化段（约1095行），将对应模块设为None
- 或在config.yaml加开关（需要小改代码）

---

## 五、测试策略

### 5.1 改完代码必做验证

每改一个模块，三件事：
1. **跑对应单元测试**：`python3 -m pytest tests/test_harness_xxx.py -v -o "addopts="`
2. **跑所有Harness测试**：`python3 -m pytest tests/test_harness_*.py -v -o "addopts="`
3. **烟雾测试导入**：`python3 -c "from deepagent_harness import *; print('OK')"`

### 5.2 测试覆盖情况

| 模块 | 测试文件 | 用例数 |
|------|---------|--------|
| scene_router | test_harness_scene_router.py | 15 |
| prefix_manager | test_harness_prefix_manager.py | 11 |
| hard_constraint | test_harness_hard_constraint.py | 15 |
| model_router | test_harness_model_router.py | 15 |
| reasoning_manager | test_harness_reasoning_manager.py | 11 |
| intent_router | test_harness_intent_router.py | 12 |
| immune_system | test_harness_immune_system.py | 4 |
| starroad_cognition | test_harness_starroad.py | 6 |
| context_layout | test_harness_context_layout.py | 7 |
| tool_schema_stabilizer | test_harness_tool_schema_stabilizer.py | 7 |
| bidirectional_primitives | test_harness_bidirectional.py | 10 |
| imports测试 | test_harness_imports.py | 13 |
| **合计** | | **141** |

---

## 六、技术债务和已知限制

1. **免疫系统是MVP关键词匹配**：不是spawn独立审查Agent，复杂违反可能漏判
2. **意图路由是关键词规则**：不是小模型分类，边界case可能误分
3. **硬约束提取是正则**：复杂句式可能提取不到，误匹配已修复大部分
4. **Code Mode是MVP模拟**：embedded/run_task.sh调用的OpenCode二进制在Linux下路径问题
5. **Memory嵌套索引未完全实现**：MEMORY_TIERS定义了分层但实际检索逻辑待完善
