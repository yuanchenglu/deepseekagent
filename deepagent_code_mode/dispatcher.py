"""
Code Mode Dispatcher

负责把用户（董事长）的自然语言指令翻译成对内置 OpenCode 研发小组的任务，
并收集结果返回给 Deep Agent 做最终总结。

隔离原则：
- 所有调用都走 embedded/ 目录
- 不读取用户 ~/.config/opencode 或任何本地配置

MVP 阶段：
- dispatch() 通过 subprocess 调用 embedded/run_task.sh
- 返回非阻塞的 task_id，供后续 collect_result / check_status 查询
"""

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional


class CodeModeDispatcher:
    """Code Mode 派发器 — 将指令转换为嵌入式研发小组的任务并收集结果"""

    def __init__(self, embedded_root: Optional[Path] = None):
        self.embedded_root = embedded_root or Path(__file__).parent.parent / "embedded"
        self.workspace = self.embedded_root / "workspace"
        self.config = self.embedded_root / "config"
        self._task_script = self.embedded_root / "run_task.sh"

    def translate_to_task(self, user_instruction: str) -> Dict[str, Any]:
        """
        将用户指令转换为结构化任务。
        MVP 阶段使用简单 prompt + 规则，后续可接入小模型分类。
        """
        return {
            "instruction": user_instruction,
            "task_type": "general_development",  # 后续扩展：feature / bugfix / refactor / research
            "priority": "normal",
            "context": {
                "mode": "code",
                "isolated": True,
            }
        }

    def dispatch(self, user_instruction: str) -> Dict[str, Any]:
        """
        派发任务到内置研发小组。

        1. 将指令写入临时任务文件
        2. 调用 embedded/run_task.sh 执行
        3. 解析 stdout 中的 JSON 结果
        4. 返回 {status, task_id, pid}

        非阻塞式：调用后立即返回 task_id，后续通过 collect_result() 获取结果。
        """
        task = self.translate_to_task(user_instruction)
        task_id = str(uuid.uuid4())[:8]

        # 写入临时任务文件（包含 task_id，供 run_task.sh 读取）
        task_file = self.workspace / f"incoming_{task_id}.json"
        self.workspace.mkdir(parents=True, exist_ok=True)
        task_with_id = {"task_id": task_id, **task}
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_with_id, f, ensure_ascii=False, indent=2)

        print(f"[CodeMode] Dispatching task [{task_id}]: {user_instruction[:80]}...")

        # 调用嵌入式任务执行脚本
        pid = None
        if self._task_script.exists():
            proc = subprocess.Popen(
                [str(self._task_script), str(task_file)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            pid = proc.pid
            try:
                stdout_data, stderr_data = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout_data, stderr_data = proc.communicate()
            result_text = stdout_data

            # 尝试解析脚本返回的 JSON
            stdout_trimmed = result_text.strip()
            task_result = None
            if stdout_trimmed:
                # 尝试直接解析整个输出
                try:
                    task_result = json.loads(stdout_trimmed)
                except json.JSONDecodeError:
                    # 回退：逐行查找 JSON 块
                    json_lines = []
                    in_json = False
                    for line in stdout_trimmed.split('\n'):
                        if line.strip().startswith('{'):
                            in_json = True
                        if in_json:
                            json_lines.append(line)
                        if line.strip().endswith('}'):
                            break
                    if json_lines:
                        try:
                            task_result = json.loads('\n'.join(json_lines))
                        except json.JSONDecodeError:
                            task_result = {"raw_output": stdout_trimmed[:500]}
                    else:
                        task_result = {"raw_output": stdout_trimmed[:500]}
        else:
            # fallback：脚本不存在时直接模拟
            print(f"[CodeMode] Warning: {self._task_script} not found, using fallback")
            task_result = {
                "task_id": task_id,
                "status": "simulated",
                "instruction": user_instruction,
                "result": {"summary": "（回退模式）未找到 run_task.sh，使用模拟结果"}
            }
            pid = None

        # 清理临时任务文件
        if task_file.exists():
            task_file.unlink()

        return {
            "status": task_result.get("status", "dispatched") if task_result else "dispatched",
            "task_id": task_id,
            "task": task,
            "pid": pid,
            "result": task_result.get("result", {}) if task_result else {},
            "message": f"任务 [{task_id}] 已派发给内置研发小组"
        }

    def collect_result(self, task_id: str) -> Dict[str, Any]:
        """
        收集指定任务 ID 的执行结果。

        从 workspace/ 查找 task_{task_id}.json 并解析。
        如果文件不存在，返回 pending 状态。
        """
        task_file = self.workspace / f"task_{task_id}.json"
        if not task_file.exists():
            # 尝试查找其他 task_id 文件（可能存在不同前缀）
            for f in self.workspace.glob(f"*{task_id}*.json"):
                task_file = f
                break
            else:
                return {
                    "status": "pending",
                    "task_id": task_id,
                    "summary": "任务尚未完成或 task_id 不存在",
                    "artifacts": []
                }

        try:
            with open(task_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "status": data.get("status", "unknown"),
                "task_id": data.get("task_id", task_id),
                "summary": data.get("result", {}).get("summary", "任务已完成"),
                "artifacts": [],
                "logs": str(task_file),
                "raw": data
            }
        except (json.JSONDecodeError, IOError) as e:
            return {
                "status": "error",
                "task_id": task_id,
                "summary": f"读取结果失败: {e}",
                "artifacts": []
            }

    def check_status(self, task_id: str) -> Dict[str, Any]:
        """
        快速检查任务状态，无需完整结果。

        返回简化的状态信息，适用于轮询场景。
        """
        full = self.collect_result(task_id)
        return {
            "task_id": task_id,
            "status": full["status"],
            "has_result": full["status"] not in ("pending", "unknown"),
        }

    def list_tasks(self) -> list:
        """列出 workspace 中所有已完成的任务"""
        task_files = sorted(self.workspace.glob("task_*.json"))
        tasks = []
        for f in task_files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                tasks.append({
                    "task_id": data.get("task_id", f.stem),
                    "status": data.get("status", "unknown"),
                    "started_at": data.get("started_at", ""),
                    "instruction_preview": data.get("instruction", "")[:80],
                })
            except (json.JSONDecodeError, IOError):
                continue
        return tasks


# === 快捷入口：python -m deepagent_code_mode.dispatcher ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
    else:
        instruction = "实现一个用户登录功能"
    disp = CodeModeDispatcher()
    result = disp.dispatch(instruction)
    print(json.dumps(result, ensure_ascii=False, indent=2))
