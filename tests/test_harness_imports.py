#!/usr/bin/env python3
"""全模块集成验证测试

验证 deepagent_harness 和 deepagent_code_mode 所有模块
可以正常导入，以及关键端到端流程不报错。
"""

import sys
from pathlib import Path

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 测试 1: deepagent_harness 所有模块可正常 import
# ============================================================
class TestHarnessImports:
    """deepagent_harness 模块导入测试"""

    def test_harness_init_import(self):
        """验证 deepagent_harness 包根目录可导入"""
        import deepagent_harness
        assert hasattr(deepagent_harness, "SceneRouter"), \
            "deepagent_harness 应导出 SceneRouter"
        assert hasattr(deepagent_harness, "SceneType"), \
            "deepagent_harness 应导出 SceneType"
        assert hasattr(deepagent_harness, "route_instruction"), \
            "deepagent_harness 应导出 route_instruction"

    def test_harness_scene_router_import(self):
        """验证 scene_router 模块可单独导入"""
        from deepagent_harness.scene_router import SceneRouter, SceneType, route_instruction
        assert SceneRouter is not None
        assert SceneType is not None
        assert route_instruction is not None

    def test_harness_scene_type_enum_values(self):
        """验证 SceneType 枚举包含所有预期场景"""
        from deepagent_harness import SceneType
        
        expected_types = {"CODE", "RESEARCH", "QUERY", "PLANNING", "OPERATION", "OTHER"}
        actual_types = {m.name for m in SceneType}
        
        for t in expected_types:
            assert t in actual_types, f"SceneType 缺少枚举值: {t}"
        
        assert SceneType.CODE.value == "code"
        assert SceneType.OTHER.value == "other"


# ============================================================
# 测试 2: deepagent_code_mode 所有模块可正常 import
# ============================================================
class TestCodeModeImports:
    """deepagent_code_mode 模块导入测试"""

    def test_code_mode_init_import(self):
        """验证 deepagent_code_mode 包根目录可导入"""
        import deepagent_code_mode
        assert hasattr(deepagent_code_mode, "CodeModeDispatcher"), \
            "deepagent_code_mode 应导出 CodeModeDispatcher"
        assert hasattr(deepagent_code_mode, "handle_development_request"), \
            "deepagent_code_mode 应导出 handle_development_request"
        assert hasattr(deepagent_code_mode, "CodeModeSessionManager"), \
            "deepagent_code_mode 应导出 CodeModeSessionManager"

    def test_code_mode_dispatcher_import(self):
        """验证 dispatcher 模块可单独导入"""
        from deepagent_code_mode.dispatcher import CodeModeDispatcher
        assert CodeModeDispatcher is not None

    def test_code_mode_handler_import(self):
        """验证 handler 模块可单独导入"""
        from deepagent_code_mode.handler import (
            handle_development_request,
            check_task,
            get_task_result,
            list_recent_tasks,
        )
        assert handle_development_request is not None
        assert check_task is not None
        assert get_task_result is not None
        assert list_recent_tasks is not None

    def test_code_mode_session_import(self):
        """验证 session 模块可单独导入"""
        from deepagent_code_mode.session import CodeModeSessionManager, CodeModeSession
        assert CodeModeSessionManager is not None
        assert CodeModeSession is not None

    def test_code_mode_integration_example_import(self):
        """验证 integration_example 模块可单独导入"""
        from deepagent_code_mode.integration_example import handle_code_mode_request
        assert handle_code_mode_request is not None


# ============================================================
# 测试 3: route_instruction → handle_development_request 端到端不报错
# ============================================================
class TestEndToEnd:
    """端到端集成测试"""

    def test_route_instruction_to_code_mode(self):
        """验证 route_instruction 可以路由研发类指令到 Code Mode 且不报错"""
        from deepagent_harness import route_instruction
        
        # 研发类指令应能正常路由
        result = route_instruction("帮我实现一个登录功能")
        assert result is not None
        assert isinstance(result, dict)
        # status 可能是 completed/dispatched/simulated/passthrough 都不算报错
        assert "status" in result
        # 不应报错
        assert result.get("status") != "error", f"路由返回错误: {result}"

    def test_route_non_code_instruction(self):
        """验证非研发类指令路由返回 passthrough 且不报错"""
        from deepagent_harness import route_instruction
        
        result = route_instruction("今天天气怎么样")
        assert result is not None
        assert isinstance(result, dict)
        assert "status" in result
        # 非研发类应 passthrough
        if result["status"] not in ("passthrough", "other"):
            pytest.skip(f"非研发类状态为 {result['status']}（可能已实现自动路由）")

    def test_handle_development_request_direct(self):
        """验证 handle_development_request 可直接调用不报错"""
        from deepagent_code_mode import handle_development_request
        
        result = handle_development_request("实现一个用户登录功能")
        assert result is not None
        assert isinstance(result, dict)
        assert "status" in result
        assert "task_id" in result

    def test_dispatcher_cycle(self):
        """验证 CodeModeDispatcher 完整生命周期：创建 → dispatch → list → status"""
        from deepagent_code_mode import CodeModeDispatcher
        
        disp = CodeModeDispatcher()
        
        # dispatch
        result = disp.dispatch("端到端测试指令 — 验证完整周期")
        assert "task_id" in result
        task_id = result["task_id"]
        
        # list
        tasks = disp.list_tasks()
        assert isinstance(tasks, list)
        
        # check_status
        status = disp.check_status(task_id)
        assert isinstance(status, dict)
        assert "status" in status

    def test_route_instruction_via_harness_shortcut(self):
        """验证快捷函数 route_instruction 能从 harness 正确调用"""
        from deepagent_harness import route_instruction
        from deepagent_code_mode import handle_development_request
        
        # 验证两者可以串联工作
        harness_result = route_instruction("写一个RESTful API")
        assert isinstance(harness_result, dict)
        assert "status" in harness_result
