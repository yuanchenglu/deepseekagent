from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit-remote-release-state.py"


def load_audit_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("remote_release_state_audit", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load audit module from {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(
    run_id: int,
    *,
    workflow_id: int,
    head_sha: str = "head-current",
    event: str = "push",
    conclusion: str = "success",
    run_number: int = 1,
    run_attempt: int = 1,
) -> dict[str, object]:
    return {
        "id": run_id,
        "workflow_id": workflow_id,
        "name": f"workflow-{workflow_id}",
        "event": event,
        "status": "completed",
        "conclusion": conclusion,
        "head_branch": "develop",
        "head_sha": head_sha,
        "run_number": run_number,
        "run_attempt": run_attempt,
        "created_at": "2026-07-29T00:00:00Z",
        "updated_at": f"2026-07-29T00:00:{run_id % 60:02d}Z",
        "html_url": f"https://example.invalid/actions/runs/{run_id}",
    }


class RemoteReleaseAuditClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_audit_module()

    def test_current_audit_replaces_its_own_previous_failure(self) -> None:
        previous_failure = run(
            10,
            workflow_id=900,
            conclusion="failure",
            run_number=4,
        )

        actionable, historical = self.audit.classify_failures(
            [previous_failure],
            {"head-current"},
            current_workflow_id=900,
        )

        self.assertEqual(actionable, [])
        self.assertEqual([item["id"] for item in historical], [10])

    def test_newer_success_supersedes_previous_failure(self) -> None:
        previous_failure = run(
            20,
            workflow_id=901,
            conclusion="failure",
            run_number=7,
        )
        newer_success = run(
            21,
            workflow_id=901,
            conclusion="success",
            run_number=8,
        )

        actionable, historical = self.audit.classify_failures(
            [previous_failure, newer_success],
            {"head-current"},
            current_workflow_id=900,
        )

        self.assertEqual(actionable, [])
        self.assertEqual([item["id"] for item in historical], [20])

    def test_newer_failure_remains_actionable(self) -> None:
        previous_success = run(
            30,
            workflow_id=902,
            conclusion="success",
            run_number=2,
        )
        newer_failure = run(
            31,
            workflow_id=902,
            conclusion="timed_out",
            run_number=3,
        )

        actionable, historical = self.audit.classify_failures(
            [previous_success, newer_failure],
            {"head-current"},
            current_workflow_id=900,
        )

        self.assertEqual([item["id"] for item in actionable], [31])
        self.assertEqual(historical, [])

    def test_retry_attempt_supersedes_failed_attempt(self) -> None:
        first_attempt = run(
            40,
            workflow_id=903,
            conclusion="failure",
            run_number=5,
            run_attempt=1,
        )
        successful_retry = run(
            41,
            workflow_id=903,
            conclusion="success",
            run_number=5,
            run_attempt=2,
        )

        actionable, historical = self.audit.classify_failures(
            [first_attempt, successful_retry],
            {"head-current"},
            current_workflow_id=900,
        )

        self.assertEqual(actionable, [])
        self.assertEqual([item["id"] for item in historical], [40])

    def test_unreferenced_head_failure_is_historical(self) -> None:
        old_branch_failure = run(
            50,
            workflow_id=904,
            head_sha="old-head",
            conclusion="failure",
        )

        actionable, historical = self.audit.classify_failures(
            [old_branch_failure],
            {"head-current"},
            current_workflow_id=900,
        )

        self.assertEqual(actionable, [])
        self.assertEqual([item["id"] for item in historical], [50])

    def test_automatic_audit_reports_active_without_self_lock(self) -> None:
        active = [{"id": 60}]
        self.assertEqual(
            self.audit.audit_exit_code([], active, strict_active_gate=False),
            0,
        )

    def test_manual_strict_audit_blocks_on_active(self) -> None:
        active = [{"id": 61}]
        self.assertEqual(
            self.audit.audit_exit_code([], active, strict_active_gate=True),
            1,
        )

    def test_any_actionable_failure_blocks(self) -> None:
        failure = [{"id": 62}]
        self.assertEqual(
            self.audit.audit_exit_code(failure, [], strict_active_gate=False),
            1,
        )


if __name__ == "__main__":
    unittest.main()
