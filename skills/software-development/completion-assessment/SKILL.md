---
name: completion-assessment
description: "Three-layer methodology for assessing real project completion — not trusting file existence + compilation as proof of working modules. Distinguishes 50% (infrastructure exists) from 80% (modules actually wired together)."
version: 1.1.0
metadata:
  hermes:
    tags: [code-analysis, evaluation, planning, inspection]
---

# 完成度评估方法论

## 核心问题

前序 AI 模型产出的代码可能：
- 文件存在 ✅ 且编译通过 ✅
- 但模块之间**没有真实调用**（模拟回复、零引用的死代码、传 None 的构造函数参数）

只看文件数 + 编译状态，你会误判为 80% 完成，实际只有 50%。

## 三层递进评估法

```
第一层：文件存在性
  ls *.py → py_compile → 确认文件都在且可编译
  ⚠️ 陷阱层——文件存在 ≠ 功能可用

第二层：模块集成度
  grep 跨模块引用：模块 A 是否真的 import 了模块 B？
  grep 构造函数参数：创建实例时传入了真实依赖，还是传了 None？
  grep 调用点：模块 B 的 API 在模块 A 的代码中是否有实际调用？

第三层：管线完整性
  画出数据流：用户操作 → 模块A → 模块B → 模块C → 结果
  逐跳验证：每个箭头在代码中是否有真实调用（不是模拟/占位）
  找断点：管线在哪一跳断了？
```

## 50% vs 80% 特征对照

| 评估维度 | 50% 状态 | 80% 状态 |
|---------|---------|---------|
| 文件层 | 模块存在可编译 | 同上 |
| 集成层 | 有 import 但无实际调用 | 模块 A 真实调用模块 B 的 API |
| 管线层 | 单模块可独立工作 | 完整端到端管线有一条通 |
| UI 层 | 界面元素存在 | 操作能触发后端逻辑 |
| 异常处理 | 无 try/except | 每层有合理降级 |

## 实操步骤

```bash
# 1. 编译检查
python3 -c "
import ast
for f in files:
    try:
        ast.parse(open(f).read())
        print(f'OK {f}')
    except SyntaxError as e:
        print(f'FAIL {f}: {e}')
"

# 2. 跨模块引用检查
# 模块A 是否真的 import 了模块B？
grep -rn "from scanner\|import scanner\|RepairEngine" project/ --include="*.py"

# 模块A 的构造函数是否传入了真实依赖？
grep -n "scanner=\|repair=" launcher_flet.py

# 3. 管线断点检查
# 写一段数据流：入口 → A → B → C → 结果
# 逐跳检查每个箭头在源码中是否存在
```

## 快速健康检查（5 分钟出判断组合）

不必先读全部源码。一组快速命令建立 baseline，立刻暴露 50% 状态：

```bash
# 1. 跨平台检查（最简单也最致命的信号）
echo "=== .sh files ===" && find . -name "*.sh" -type f | wc -l
echo "=== .bat files ===" && find . -name "*.bat" -type f | wc -l
echo "=== platform.system() refs ===" && grep -rn "platform\.system\|os\.name" --include="*.py" . | wc -l

# 2. 模块沉寂检测（文件存在但零引用 = 死代码）
echo "=== scanner import count ===" && grep -rn "from.*scanner\|import.*scanner" --include="*.py" . | grep -v __pycache__ | wc -l
echo "=== repair import count ===" && grep -rn "from.*repair\|import.*repair" --include="*.py" . | grep -v __pycache__ | wc -l

# 3. 模拟/占位信号（关键词越少越接近真实）
echo "=== mock/placeholder signals ===" && grep -rn "mock\|placeholder\|TODO\|FIXME\|模拟\|假数据" --include="*.py" . | grep -v __pycache__

# 4. 空接口检测（pass 越多说明未实现越多）
echo "=== pass-only methods ===" && grep -rn "^\s*pass\s*$" --include="*.py" . | grep -v __pycache__ | grep -v "test_" | wc -l

# 5. 数据流断点检测（核心模块是否被主入口调用）
grep -n "scan_all\|scan_one" launcher_flet.py 2>/dev/null || echo "⚠️ Scanner 从未在主入口被调用"
grep -n "repair" launcher_flet.py 2>/dev/null || echo "⚠️ RepairEngine 从未在主入口被引用"
```

## 50% vs 80% 具体信号对照表

| 信号 | 50% 必然有 | 80% 必然没有 |
|------|-----------|-------------|
| Shell 脚本 | 只有 .bat（Windows-only） | .bat 和 .sh 成对出现 |
| 模块调用 | 主入口不 import 该模块 | 主入口显式调用了模块 API |
| 模拟数据 | 有 mock_response / fake_data | 所有回复来源真实调用 |
| 空接口 | 方法体只有 `pass` 或 `...` | 每个方法有实现 |
| 构造函数 | 依赖参数为 `None` 或 `Optional` 且调用方不传 | 所有依赖通过构造函数注入 |
| 错误处理 | `except: pass` 或无 try | 每层 try/except 有降级 |
| 截图证明 | 无或只有单模块截图 | 端到端用户路径截图完整 |

## 向用户汇报的方式

❌ "这个项目完成了多少？" → 抽象，用户说不清

✅ "我检查了各模块间的集成：scanner 文件存在且可编译，但 ops_chat 用了模拟回复而非真实调 scanner；repair_engine 11 文件但全项目无一处 import。目前的管线在 ops_chat 这里断了。你觉得应该把打通这条管作为本期任务，还是先补别的？"

✅ 带证据的汇报（本会话验证有效的格式）：
- "启动脚本：2 个 .bat，0 个 .sh → Linux 上跑不了。这是 P0 级问题，必须先做"
- "主入口调用情况：grep scanner launcher_flet.py → 无匹配。Scanner 是孤立的"
- "ops_chat.py 数据流追踪：_generate_response() 内部是 if/else 关键词匹配。输入'检查一下' → 返回写死的字符串，返回的是模拟数据而非真实扫描结果"

## 典型发现模式

这种评估常在多期整合项目中暴露问题——前几期各自建好了独立模块，但没人把它们连起来：

- `ops_chat.py` 的 `_generate_response()` 是 if/else 关键词匹配（模拟），实际数据来源为空
- `repair/` 包 11 文件写好了，但整个项目 **0 处 import**
- 引擎构造函数接受 `scanner=None`，但调用方从来没传
- 模块 UI 入口存在，按钮绑定了回调，但回调内部用硬编码假数据
- 所有启动脚本是 `.bat`，零个 `.sh`（`ls *.sh = 0`），跨平台直接不可用

## 四维评估框架（本会话产出）

在实际项目中验证有效的框架，从四个独立维度评估完成度：

| 维度 | 评估方法 | 典型 50% 表现 |
|------|---------|-------------|
| 文件完整度 | `ls *.py + py_compile` | 35 文件全部存在且编译通过 ✅ 但这是最表面的 |
| 平台完备度 | `find .sh .bat + grep platform.system` | 零 .sh 文件、全硬编码 Windows 路径 |
| 模块集成度 | `grep` 跨模块引用 + grep 构造函数传参 | 核心引擎（repair/）零引用、引擎参数传 None |
| 生产体验度 | grep loading/empty state + grep try/except | 无加载态、无空状态、无全局日志、无测试 |

**为什么四维缺一不可**：文件完整度最容易让你误判——35 个文件编译通过的报告看起来很漂亮，但平台、集成、体验三个维度会立刻揭露项目实际只有 50%。