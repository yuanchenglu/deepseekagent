"""
DeepAgent Code Mode - CEO指挥内置研发小组的核心模块

这是 Deep Agent 作为数字分身 CEO 的关键差异化能力。
所有实现必须保证与用户本地 OpenCode 完全隔离。
"""

from .dispatcher import CodeModeDispatcher
from .session import CodeModeSessionManager
from .handler import (
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

__all__ = [
    "CodeModeDispatcher",
    "CodeModeSessionManager",
    "handle_development_request",
    "check_task",
    "get_task_result",
    "list_recent_tasks",
    "TaskType",
    "handle_feature",
    "handle_bugfix",
    "handle_refactor",
    "handle_research",
]
