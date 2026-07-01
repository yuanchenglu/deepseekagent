"""
Code Mode 与主 Agent 的简单集成示例

在真实 run_agent / cli 中，可以这样调用：

    from deepagent_code_mode import handle_development_request

    result = handle_development_request("实现用户登录功能，支持手机号和邮箱")
    print(result)

本模块展示了三种集成方式：
  1. 函数式快捷调用 (handle_development_request)
  2. 面向对象调度 (CodeModeDispatcher)
  3. 异步状态检查 (check_task / get_task_result)
"""

from .dispatcher import CodeModeDispatcher
from .handler import handle_development_request, check_task, get_task_result


def handle_code_mode_request(instruction: str) -> dict:
    """示例：主循环中检测到需要 Code Mode 时调用（方式一：快捷函数）"""
    return handle_development_request(instruction)


def handle_code_mode_request_oO(instruction: str) -> dict:
    """示例：面向对象方式调用 dispatcher"""
    dispatcher = CodeModeDispatcher()
    result = dispatcher.dispatch(instruction)
    # 如果需要异步轮询：
    # task_id = result["task_id"]
    # status = dispatcher.check_status(task_id)
    # full_result = dispatcher.collect_result(task_id)
    return result


# === CLI 演示 ===
if __name__ == "__main__":
    import json
    test_instruction = "实现用户登录功能，支持手机号和邮箱注册，密码使用 bcrypt 加密"

    print("=" * 60)
    print("Code Mode 集成演示")
    print("=" * 60)
    print(f"指令: {test_instruction}\n")

    # 方式一：快捷函数
    print("--- 方式一: handle_development_request ---")
    result = handle_code_mode_request(test_instruction)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()

    # 检查状态
    task_id = result.get("task_id", "")
    if task_id:
        print(f"--- 检查任务状态: {task_id} ---")
        status = check_task(task_id)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        print()

        print(f"--- 收集任务结果: {task_id} ---")
        full = get_task_result(task_id)
        print(json.dumps(full, ensure_ascii=False, indent=2))
