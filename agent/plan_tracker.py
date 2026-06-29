"""Plan 状态机管理器（StarRoad Cognition）。
Plan 不只是 markdown 文件，是一个动态状态机。
JSON 持久化到 ~/.deepagent/plans/<id>.json

与 todo 工具的关系：
- PlanTracker 管理 plan 级别信息（目标/盲区/调整历史/整体状态）
- todo 工具管理每个原子任务的详细状态
- PlanTracker 的 tasks 列表只是简化的任务清单，详细追踪走 todo"""

# === DeepAgent: StarRoad Cognition ===

from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)


class PlanTracker:
    """Plan 状态机管理器。

    用法：
        tracker = PlanTracker()
        plan_id = tracker.create_or_update("实现登录功能", [
            {"id": "t1", "desc": "设计数据库表"},
            {"id": "t2", "desc": "实现 API"},
        ])
        tracker.add_gap("发现 Token 刷新逻辑不完善")
        status = tracker.get_status()  # → {"has_active_plan": True, ...}
    """

    def __init__(self, plans_dir: str | Path | None = None):
        """初始化 PlanTracker。

        Args:
            plans_dir: plan JSON 文件目录，默认 get_hermes_home() / "plans"
        """
        if plans_dir is None:
            plans_dir = get_hermes_home() / "plans"
        self._plans_dir = Path(plans_dir)
        self._plans_dir.mkdir(parents=True, exist_ok=True)
        # 缓存当前 in_progress 的 plan_id
        self._current_plan_id: str | None = None

    def create_or_update(self, goal: str, tasks: list[dict] | None = None) -> str:
        """创建新 plan 或追加任务到现有 plan。

        Args:
            goal: 任务目标
            tasks: 任务列表，每个元素为 {"id": str, "desc": str}

        Returns:
            plan_id
        """
        # 检查是否有 in_progress 的 plan
        existing = self._find_in_progress_plan()
        if existing:
            # 追加任务到现有 plan（如果提供了新任务）
            if tasks:
                existing_tasks = existing.get("tasks", [])
                existing_ids = {t["id"] for t in existing_tasks}
                for t in tasks:
                    if t["id"] not in existing_ids:
                        existing_tasks.append({
                            "id": t["id"],
                            "desc": t["desc"],
                            "status": "pending",
                        })
                existing["tasks"] = existing_tasks
            existing["updated_at"] = self._now_iso()
            self._save_plan(existing)
            self._current_plan_id = existing["plan_id"]
            return existing["plan_id"]

        # 创建新 plan
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "goal_history": [f"v1: {goal}"],
            "status": "in_progress",
            "current_task": tasks[0]["id"] if tasks else "",
            "tasks": [
                {"id": t["id"], "desc": t["desc"], "status": "pending"}
                for t in (tasks or [])
            ],
            "gaps_found": [],
            "created_at": self._now_iso(),
            "updated_at": self._now_iso(),
        }
        self._save_plan(plan)
        self._current_plan_id = plan_id
        return plan_id

    def mark_done(self, task_id: str) -> None:
        """标记指定任务完成。"""
        plan = self._load_current_plan()
        if not plan:
            logger.debug("PlanTracker: no active plan to mark task done")
            return
        for task in plan.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = "done"
                break
        # 自动推进到下一个 pending 任务
        for task in plan.get("tasks", []):
            if task["status"] == "pending":
                plan["current_task"] = task["id"]
                break
        plan["updated_at"] = self._now_iso()
        self._save_plan(plan)

    def add_gap(self, gap: str) -> None:
        """探索中发现的盲区追加到计划。"""
        plan = self._load_current_plan()
        if not plan:
            logger.debug("PlanTracker: no active plan to add gap")
            return
        if gap not in plan.get("gaps_found", []):
            plan.setdefault("gaps_found", []).append(gap)
            plan["updated_at"] = self._now_iso()
            self._save_plan(plan)

    def refine_goal(self, new_goal: str) -> None:
        """发现用户认知不够时调整目标。"""
        plan = self._load_current_plan()
        if not plan:
            logger.debug("PlanTracker: no active plan to refine goal")
            return
        version = len(plan.get("goal_history", [])) + 1
        plan.setdefault("goal_history", []).append(f"v{version}: {new_goal}")
        plan["goal"] = new_goal
        plan["updated_at"] = self._now_iso()
        self._save_plan(plan)

    def get_status(self) -> dict:
        """返回当前 plan 的状态摘要。"""
        plan = self._load_current_plan()
        if not plan:
            return {"has_active_plan": False}

        tasks = plan.get("tasks", [])
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "done")
        pending = sum(1 for t in tasks if t["status"] == "pending")
        in_progress_count = sum(1 for t in tasks if t["status"] == "in_progress")

        return {
            "has_active_plan": True,
            "plan_id": plan["plan_id"],
            "goal": plan["goal"],
            "goal_history": plan.get("goal_history", []),
            "status": plan["status"],
            "progress": f"{done}/{total}",
            "done_count": done,
            "pending_count": pending,
            "in_progress_count": in_progress_count,
            "total_count": total,
            "current_task": plan.get("current_task", ""),
            "gaps_found": plan.get("gaps_found", []),
        }

    def get_current_plan_id(self) -> str | None:
        """返回当前 in_progress 的 plan_id。"""
        if self._current_plan_id:
            return self._current_plan_id
        plan = self._find_in_progress_plan()
        if plan:
            self._current_plan_id = plan["plan_id"]
            return plan["plan_id"]
        return None

    def load_plan(self, plan_id: str) -> dict | None:
        """读取指定 plan 的 JSON。"""
        path = self._plans_dir / f"{plan_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("PlanTracker: failed to load plan %s: %s", plan_id, e)
            return None

    def list_plans(self) -> list[dict]:
        """列出所有 plan（按创建时间倒序）。"""
        plans = []
        for f in sorted(self._plans_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                plans.append({
                    "plan_id": data.get("plan_id", f.stem),
                    "goal": data.get("goal", ""),
                    "status": data.get("status", ""),
                    "task_count": len(data.get("tasks", [])),
                    "created_at": data.get("created_at", ""),
                })
            except Exception:
                continue
        return plans

    @staticmethod
    def validate_plan(plan: dict) -> bool:
        """校验 plan 结构完整性。"""
        required_keys = {"plan_id", "goal", "status", "tasks", "created_at", "updated_at"}
        if not all(k in plan for k in required_keys):
            return False
        if plan["status"] not in ("in_progress", "completed", "cancelled"):
            return False
        for task in plan.get("tasks", []):
            if not all(k in task for k in ("id", "desc", "status")):
                return False
            if task["status"] not in ("pending", "in_progress", "done"):
                return False
        return True

    # -- 内部方法 --

    def _find_in_progress_plan(self) -> dict | None:
        """扫描 plans 目录找到 in_progress 的 plan。"""
        for f in sorted(self._plans_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("status") == "in_progress":
                    return data
            except Exception:
                continue
        return None

    def _load_current_plan(self) -> dict | None:
        """加载当前 plan。"""
        plan_id = self.get_current_plan_id()
        if not plan_id:
            return None
        return self.load_plan(plan_id)

    def _save_plan(self, plan: dict) -> None:
        """持久化 plan 到 JSON 文件。"""
        plan_id = plan.get("plan_id", "unknown")
        path = self._plans_dir / f"{plan_id}.json"
        try:
            path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("PlanTracker: failed to save plan %s: %s", plan_id, e)

    @staticmethod
    def _now_iso() -> str:
        """返回当前 UTC 时间的 ISO 格式字符串。"""
        return datetime.now(timezone.utc).isoformat()
