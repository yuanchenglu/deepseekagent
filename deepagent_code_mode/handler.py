"""
Code Mode Handler — 供技能系统和 run_agent 调用的高层入口

封装 CodeModeDispatcher，提供简单的函数式接口，
让技能文件（SKILL.md）和 run_agent 路由可以直接调用。
"""

import json
from typing import Dict, Any, Optional

from .dispatcher import CodeModeDispatcher


# 全局单例（可选，避免重复创建）
_dispatcher: Optional[CodeModeDispatcher] = None


def get_dispatcher() -> CodeModeDispatcher:
    """获取全局 CodeModeDispatcher 实例"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = CodeModeDispatcher()
    return _dispatcher


def handle_development_request(instruction: str) -> Dict[str, Any]:
    """
    处理开发请求的高层入口。

    由技能系统或 run_agent 路由调用。
    输入自然语言指令，返回调度结果。

    示例:
        result = handle_development_request("实现用户登录功能")
        print(result["status"])  # "completed"
    """
    disp = get_dispatcher()
    return disp.dispatch(instruction)


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
        elif cmd == "status" and len(sys.argv) > 2:
            result = check_task(sys.argv[2])
        elif cmd == "result" and len(sys.argv) > 2:
            result = get_task_result(sys.argv[2])
        elif cmd == "list":
            result = {"tasks": list_recent_tasks()}
        else:
            result = {"error": f"用法: python -m deepagent_code_mode.handler <dispatch|status|result|list> [args]"}
    else:
        result = {"error": "需要子命令: dispatch, status, result, list"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
