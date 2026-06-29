"""Tests for PlanTracker — 计划状态机管理器。"""

import pytest
import json
from agent.plan_tracker import PlanTracker


@pytest.fixture
def tracker(tmp_path):
    """创建临时目录的 PlanTracker 实例。"""
    plans_dir = tmp_path / "plans"
    return PlanTracker(str(plans_dir))


class TestCreatePlan:
    """创建和追加 plan 的测试。"""

    def test_creates_plan_and_returns_id(self, tracker):
        """创建新 plan 返回以 plan- 开头的 ID。"""
        plan_id = tracker.create_or_update("测试目标", [
            {"id": "t1", "desc": "第一步"},
        ])
        assert plan_id.startswith("plan-")
        assert tracker.get_current_plan_id() == plan_id

    def test_appends_to_existing_plan(self, tracker):
        """任务追加到已有 in_progress 的 plan。"""
        pid1 = tracker.create_or_update("目标", [{"id": "t1", "desc": "第一步"}])
        pid2 = tracker.create_or_update("目标", [{"id": "t2", "desc": "第二步"}])
        assert pid1 == pid2  # 同一个 plan
        plan = tracker.load_plan(pid1)
        assert len(plan["tasks"]) == 2

    def test_creates_new_when_prev_completed(self, tracker):
        """前一个 plan 已完成时创建新 plan。"""
        pid1 = tracker.create_or_update("目标A", [{"id": "t1", "desc": "A"}])
        plan = tracker.load_plan(pid1)
        plan["status"] = "completed"
        tracker._save_plan(plan)
        pid2 = tracker.create_or_update("目标B", [{"id": "t2", "desc": "B"}])
        assert pid1 != pid2


class TestManageTasks:
    """任务管理操作测试。"""

    def test_mark_done_advances_to_next(self, tracker):
        """标记一个任务完成时自动推进到下一个。"""
        tracker.create_or_update("目标", [
            {"id": "t1", "desc": "任务1"},
            {"id": "t2", "desc": "任务2"},
        ])
        tracker.mark_done("t1")
        plan = tracker.load_plan(tracker.get_current_plan_id())
        assert plan["tasks"][0]["status"] == "done"
        assert plan["current_task"] == "t2"

    def test_add_gap_deduplicates(self, tracker):
        """添加重复盲区自动去重。"""
        tracker.create_or_update("目标", [{"id": "t1", "desc": "任务"}])
        tracker.add_gap("发现盲区A")
        tracker.add_gap("发现盲区A")
        plan = tracker.load_plan(tracker.get_current_plan_id())
        assert len(plan["gaps_found"]) == 1

    def test_refine_goal_records_history(self, tracker):
        """调整目标时自动记录版本历史。"""
        tracker.create_or_update("原始目标", [{"id": "t1", "desc": "任务"}])
        tracker.refine_goal("调整后的目标")
        plan = tracker.load_plan(tracker.get_current_plan_id())
        assert len(plan["goal_history"]) == 2
        assert "调整后的目标" in plan["goal_history"][1]


class TestGetStatus:
    """状态查询测试。"""

    def test_no_active_plan(self, tracker):
        """无活跃 plan 时返回 has_active_plan=False。"""
        status = tracker.get_status()
        assert status["has_active_plan"] is False

    def test_returns_progress_summary(self, tracker):
        """有活跃 plan 时返回进度摘要。"""
        tracker.create_or_update("目标", [
            {"id": "t1", "desc": "任务1"},
            {"id": "t2", "desc": "任务2"},
            {"id": "t3", "desc": "任务3"},
        ])
        tracker.mark_done("t1")
        status = tracker.get_status()
        assert status["has_active_plan"] is True
        assert status["progress"] == "1/3"
        assert status["done_count"] == 1
        assert status["pending_count"] == 2


class TestValidatePlan:
    """Plan 结构校验测试。"""

    def test_validates_correct_plan(self, tracker):
        """结构正确的 plan 通过校验。"""
        plan = {
            "plan_id": "test-1",
            "goal": "test",
            "status": "in_progress",
            "tasks": [{"id": "t1", "desc": "task", "status": "pending"}],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        assert tracker.validate_plan(plan) is True

    def test_rejects_missing_keys(self, tracker):
        """缺少必需字段的 plan 不通过校验。"""
        assert tracker.validate_plan({"plan_id": "test"}) is False

    def test_rejects_invalid_status(self, tracker):
        """无效的 status 值不通过校验。"""
        plan = {
            "plan_id": "test-1",
            "goal": "test",
            "status": "invalid_status",
            "tasks": [],
            "created_at": "",
            "updated_at": "",
        }
        assert tracker.validate_plan(plan) is False
