"""
Code Mode Handler — 供技能系统和 run_agent 调用的高层入口

封装 CodeModeDispatcher，提供简单的函数式接口，
让技能文件（SKILL.md）和 run_agent 路由可以直接调用。

提供两个层次：
1. 通用接口：handle_development_request() — 自由文本指令
2. 类型化快捷接口：handle_feature / handle_bugfix / handle_refactor / handle_research
"""

import json
from enum import Enum
from typing import Dict, Any, Optional

from .dispatcher import CodeModeDispatcher


class TaskType(Enum):
    """任务类型枚举 — 让 handler 快捷接口可以指定任务种类"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    RESEARCH = "research"
    GENERAL = "general"


# 全局单例（可选，避免重复创建）
_dispatcher: Optional[CodeModeDispatcher] = None


def get_dispatcher() -> CodeModeDispatcher:
    """获取全局 CodeModeDispatcher 实例"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = CodeModeDispatcher()
    return _dispatcher


def _build_task_instruction(task_type: TaskType, description: str) -> str:
    """根据任务类型构建完整的自然语言指令"""
    prefix = {
        TaskType.FEATURE: "实现功能",
        TaskType.BUGFIX: "修复bug",
        TaskType.REFACTOR: "重构",
        TaskType.RESEARCH: "调研",
        TaskType.GENERAL: "",
    }[task_type]
    return f"{prefix}: {description}" if prefix else description


def handle_development_request(instruction: str) -> Dict[str, Any]:
    """
    通用开发请求入口。

    由技能系统或 run_agent 路由调用。
    输入自然语言指令，返回调度结果。

    示例:
        result = handle_development_request("实现用户登录功能")
        print(result["status"])  # "dispatched"
    """
    disp = get_dispatcher()
    return disp.dispatch(instruction)


def handle_feature(description: str) -> Dict[str, Any]:
    """快捷接口：实现新功能"""
    return handle_development_request(_build_task_instruction(TaskType.FEATURE, description))


def handle_bugfix(description: str) -> Dict[str, Any]:
    """快捷接口：修复 bug"""
    return handle_development_request(_build_task_instruction(TaskType.BUGFIX, description))


def handle_refactor(module_or_area: str) -> Dict[str, Any]:
    """快捷接口：重构模块"""
    return handle_development_request(_build_task_instruction(TaskType.REFACTOR, module_or_area))


def handle_research(topic: str) -> Dict[str, Any]:
    """快捷接口：调研技术课题"""
    return handle_development_request(_build_task_instruction(TaskType.RESEARCH, topic))


def check_task(task_id: str) -> Dict[str, Any]:
    """检查指定任务的执行状态"""
    disp = get_dispatcher()
    return disp.check_status(task_id)


def get_task_result(task_id: str) -> Dict[str, Any]:
    """获取指定任务的完整执行结果"""
    disp = get_dispatcher()
    return disp.collect_result(task_id)


def list_recent_tasks(limit: int = 10) -> list:
    """列出最近完成的任务"""
    disp = get_dispatcher()
    tasks = disp.list_tasks()
    return tasks[:limit]


# === CLI 入口 ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "dispatch" and len(sys.argv) > 2:
            result = handle_development_request(" ".join(sys.argv[2:]))
        elif cmd == "feature" and len(sys.argv) > 2:
            result = handle_feature(" ".join(sys.argv[2:]))
        elif cmd == "bugfix" and len(sys.argv) > 2:
            result = handle_bugfix(" ".join(sys.argv[2:]))
        elif cmd == "refactor" and len(sys.argv) > 2:
            result = handle_refactor(" ".join(sys.argv[2:]))
        elif cmd == "research" and len(sys.argv) > 2:
            result = handle_research(" ".join(sys.argv[2:]))
        elif cmd == "status" and len(sys.argv) > 2:
            result = check_task(sys.argv[2])
        elif cmd == "result" and len(sys.argv) > 2:
            result = get_task_result(sys.argv[2])
        elif cmd == "list":
            result = {"tasks": list_recent_tasks()}
        else:
            result = {"error": f"用法: python -m deepagent_code_mode.handler <dispatch|feature|bugfix|refactor|research|status|result|list> [args]"}
    else:
        result = {"error": "需要子命令: dispatch, feature, bugfix, refactor, research, status, result, list"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
