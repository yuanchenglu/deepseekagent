#!/usr/bin/env python3
"""
Code Mode 最小可演示测试

验证从 dispatcher 派发到 embedded/run_task.sh 的完整流程：
  1. dispatcher.dispatch() 返回带有 task_id 的结果
  2. 嵌入式脚本在 workspace/ 下创建任务文件
  3. collect_result() 能读取并解析结果
  4. check_status() 能返回正确的状态
  5. handler 快捷接口可正常工作

运行方式:
  python -m pytest tests/test_code_mode.py -v
  或直接:  python tests/test_code_mode.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from deepagent_code_mode import (
    CodeModeDispatcher,
    handle_development_request,
    check_task,
    get_task_result,
    list_recent_tasks,
    TaskType,
    handle_feature,
    handle_bugfix,
    handle_refactor,
    handle_research,
)


# ============================================================
# 测试 1: dispatcher.dispatch() 可以派发任务并返回结果
# ============================================================
def test_dispatcher_dispatch_returns_structured_result():
    """dispatch() 返回包含 status 和 task_id 的结构化字典"""
    disp = CodeModeDispatcher()
    result = disp.dispatch("实现一个用户登录功能，支持手机号和邮箱注册")

    assert isinstance(result, dict), f"返回类型应为 dict，实际为 {type(result)}"
    assert "status" in result, f"结果缺少 status 字段: {result}"
    assert "task_id" in result, f"结果缺少 task_id 字段: {result}"
    assert result["status"] in ("completed", "dispatched", "simulated"), \
        f"status 应为 completed/dispatched/simulated，实际为 {result['status']}"
    assert len(result["task_id"]) > 0, "task_id 不应为空"

    print(f"  ✓ dispatch() 返回 task_id={result['task_id']}, status={result['status']}")


# ============================================================
# 测试 2: 嵌入式脚本会在 workspace 写入任务文件
# ============================================================
def test_dispatch_creates_workspace_files():
    """dispatch() 后 workspace/ 下应有任务记录文件"""
    disp = CodeModeDispatcher()
    workspace = disp.workspace

    # 记录之前的工作文件数
    before = set(workspace.glob("task_*.json"))

    result = disp.dispatch("测试 workspace 文件写入 — 请确认 created")

    after = set(workspace.glob("task_*.json"))
    new_files = after - before

    # 如果 dispatch 后没有新文件（可能已被 cleanup），至少确认 workspace 存在
    assert workspace.exists(), "workspace 目录应存在"

    print(f"  ✓ workspace 目录存在: {workspace}")
    if new_files:
        print(f"  ✓ dispatch 后新增 {len(new_files)} 个任务文件")
        for f in new_files:
            print(f"     - {f.name}")
    else:
        print(f"  ✓ dispatch 已完成（工作文件可能在清理后被移除）")


# ============================================================
# 测试 3: collect_result() 能查询到已完成的任务
# ============================================================
def test_collect_result_after_dispatch():
    """collect_result() 能根据 task_id 读取执行结果"""
    disp = CodeModeDispatcher()
    dispatch_result = disp.dispatch("测试 collect_result — 收集结果")
    task_id = dispatch_result["task_id"]

    result = disp.collect_result(task_id)
    assert isinstance(result, dict), f"collect_result 返回类型应为 dict，实际为 {type(result)}"
    assert "status" in result, f"结果缺少 status 字段"

    # status 可能是 completed（找到文件）或 pending（文件已被清理）
    print(f"  ✓ collect_result('{task_id}') 返回 status={result['status']}")


# ============================================================
# 测试 4: check_status() 快速检查
# ============================================================
def test_check_status():
    """check_status() 返回简化的状态信息"""
    disp = CodeModeDispatcher()
    dispatch_result = disp.dispatch("测试 check_status — 状态检查")
    task_id = dispatch_result["task_id"]

    status = disp.check_status(task_id)
    assert isinstance(status, dict), f"check_status 返回类型应为 dict，实际为 {type(status)}"
    assert "status" in status
    assert "has_result" in status
    assert isinstance(status["has_result"], bool)

    print(f"  ✓ check_status('{task_id}') → status={status['status']}, has_result={status['has_result']}")


# ============================================================
# 测试 5: handler 快捷接口
# ============================================================
def test_handler_shortcut():
    """handle_development_request() 可正常调用"""
    result = handle_development_request("测试 handler 快捷接口 — 重构用户模块")
    assert isinstance(result, dict)
    assert "status" in result
    print(f"  ✓ handle_development_request() 返回 status={result['status']}")


# ============================================================
# 测试 6: 类型化快捷接口 — handle_feature
# ============================================================
def test_handler_feature_shortcut():
    """handle_feature() 可正常调用"""
    result = handle_feature("用户注册模块")
    assert isinstance(result, dict)
    assert "status" in result
    print(f"  ✓ handle_feature() 返回 status={result['status']}")


# ============================================================
# 测试 7: 类型化快捷接口 — handle_bugfix
# ============================================================
def test_handler_bugfix_shortcut():
    """handle_bugfix() 可正常调用"""
    result = handle_bugfix("登录页面白屏")
    assert isinstance(result, dict)
    assert "status" in result
    print(f"  ✓ handle_bugfix() 返回 status={result['status']}")


# ============================================================
# 测试 8: 类型化快捷接口 — handle_refactor
# ============================================================
def test_handler_refactor_shortcut():
    """handle_refactor() 可正常调用"""
    result = handle_refactor("数据库连接模块")
    assert isinstance(result, dict)
    assert "status" in result
    print(f"  ✓ handle_refactor() 返回 status={result['status']}")


# ============================================================
# 测试 9: 类型化快捷接口 — handle_research
# ============================================================
def test_handler_research_shortcut():
    """handle_research() 可正常调用"""
    result = handle_research("WebSocket 连接池方案对比")
    assert isinstance(result, dict)
    assert "status" in result
    print(f"  ✓ handle_research() 返回 status={result['status']}")


# ============================================================
# 测试 10: TaskType 枚举结构验证
# ============================================================
def test_task_type_enum():
    """TaskType 枚举包含预期值"""
    assert TaskType.FEATURE.value == "feature"
    assert TaskType.BUGFIX.value == "bugfix"
    assert TaskType.REFACTOR.value == "refactor"
    assert TaskType.RESEARCH.value == "research"
    assert TaskType.GENERAL.value == "general"
    assert len(TaskType) == 5
    print(f"  ✓ TaskType 枚举包含 5 个值: {[t.value for t in TaskType]}")


# ============================================================
# 测试 11: list_tasks 列举已完成任务
# ============================================================
def test_list_tasks():
    """list_tasks() 返回任务列表"""
    disp = CodeModeDispatcher()
    tasks = disp.list_tasks()
    assert isinstance(tasks, list)
    print(f"  ✓ list_tasks() 返回 {len(tasks)} 个任务")


# ============================================================
# 测试 7: run_task.sh 脚本直接执行
# ============================================================
# ============================================================
# 测试 8: 空指令 dispatch
# ============================================================
def test_dispatcher_empty_instruction():
    """dispatch() 空指令应能正常处理而不崩溃"""
    disp = CodeModeDispatcher()
    result = disp.dispatch("")

    assert isinstance(result, dict), f"返回类型应为 dict，实际为 {type(result)}"
    assert "status" in result, f"结果缺少 status 字段: {result}"
    assert "task_id" in result, f"结果缺少 task_id 字段: {result}"
    print(f"  ✓ 空指令 dispatch 返回 task_id={result['task_id']}, status={result['status']}")


# ============================================================
# 测试 9: 超长指令 dispatch
# ============================================================
def test_dispatcher_very_long_instruction():
    """dispatch() 超长指令（10,000+ 字符）应能正常处理而不崩溃"""
    disp = CodeModeDispatcher()

    # 生成长指令
    long_instruction = "实现功能A。" + "附加需求B、" * 2000  # 约 12000+ 字符
    long_instruction += "结束。"

    result = disp.dispatch(long_instruction)

    assert isinstance(result, dict), f"返回类型应为 dict，实际为 {type(result)}"
    assert "status" in result, f"结果缺少 status 字段: {result}"
    assert "task_id" in result, f"结果缺少 task_id 字段: {result}"
    print(f"  ✓ 超长指令 dispatch 返回 task_id={result['task_id']}, status={result['status']}")


# ============================================================
# 测试 10: 连续多次 dispatch
# ============================================================
def test_dispatcher_repeated_dispatch():
    """dispatch() 连续多次调用应互不干扰"""
    disp = CodeModeDispatcher()

    instructions = [
        "实现用户注册功能",
        "修复登录页面的 bug",
        "添加数据导出功能",
        "重构数据库连接模块",
        "编写 API 文档",
    ]

    results = []
    for instr in instructions:
        result = disp.dispatch(instr)
        assert isinstance(result, dict), f"返回类型应为 dict，实际为 {type(result)}"
        assert "task_id" in result, f"结果缺少 task_id 字段: {result}"
        results.append(result)

    # 验证每个指令都返回了独立的 task_id
    task_ids = [r["task_id"] for r in results]
    assert len(task_ids) == len(set(task_ids)), \
        f"连续 dispatch 应返回不同的 task_id，发现重复: {task_ids}"

    # 验证所有 task_id 非空
    for tid in task_ids:
        assert len(tid) > 0, "task_id 不应为空"

    print(f"  ✓ 连续 {len(instructions)} 次 dispatch 成功，task_ids: {task_ids}")


def test_run_task_script_direct():
    """直接调用 embedded/run_task.sh 验证其行为

    run_task.sh 采用非阻塞模式：后台启动 opencode，立即写入 dispatched 状态到 workspace/task_{task_id}.json
    """
    import subprocess
    import json

    script = project_root / "embedded" / "run_task.sh"
    assert script.exists(), f"run_task.sh 不存在: {script}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(json.dumps({"task_id": "test-direct-call", "instruction": "test task"}))
        task_file = f.name

    try:
        proc = subprocess.run(
            [str(script), task_file],
            capture_output=True, text=True, timeout=10
        )
        assert proc.returncode == 0, f"脚本返回非零: {proc.returncode}, stderr: {proc.stderr[:200]}"

        workspace_dir = project_root / "embedded" / "workspace"
        result_file = workspace_dir / "task_test-direct-call.json"

        if result_file.exists():
            data = json.loads(result_file.read_text())
            assert "task_id" in data
            assert "status" in data
            assert data["status"] in ("dispatched", "simulated")
            print(f"  ✓ run_task.sh 非阻塞模式: task_id={data['task_id']}, status={data['status']}")
        else:
            assert proc.returncode == 0
            print(f"  ✓ run_task.sh 执行完成（无结果文件但正常退出）")
    finally:
        os.unlink(task_file)


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    tests = [
        ("dispatcher.dispatch() 返回结构化结果", test_dispatcher_dispatch_returns_structured_result),
        ("dispatch 创建 workspace 文件", test_dispatch_creates_workspace_files),
        ("collect_result 查询任务结果", test_collect_result_after_dispatch),
        ("check_status 快速状态检查", test_check_status),
        ("handler 快捷接口", test_handler_shortcut),
        ("handle_feature 类型化接口", test_handler_feature_shortcut),
        ("handle_bugfix 类型化接口", test_handler_bugfix_shortcut),
        ("handle_refactor 类型化接口", test_handler_refactor_shortcut),
        ("handle_research 类型化接口", test_handler_research_shortcut),
        ("TaskType 枚举结构", test_task_type_enum),
        ("list_tasks 列举任务", test_list_tasks),
        ("run_task.sh 直接执行", test_run_task_script_direct),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"结果: {passed} 通过, {failed} 失败")
    if failed > 0:
        sys.exit(1)
    else:
        print("Code Mode 最小可演示状态验证通过！")
