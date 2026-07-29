from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_remaining_work_plan.py"
SPEC = importlib.util.spec_from_file_location("validate_remaining_work_plan", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

PLAN_PATH = ROOT / "docs" / "open-source-readiness" / "remaining-work-plan.json"
RUNBOOK_PATH = ROOT / "docs" / "open-source-readiness" / "16-REMAINING-WORK-EXECUTION-RUNBOOK.md"
CATALOG_PATH = ROOT / "docs" / "open-source-readiness" / "18-WORK-ID-ACCEPTANCE-CATALOG.md"
PROMPT_PATH = ROOT / "docs" / "open-source-readiness" / "17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md"


def evidence(number: int = 101) -> dict[str, object]:
    return {
        "evidence_file": f"docs/open-source-readiness/evidence/BOOT-001-2026-07-{number % 30 + 1:02d}.md",
        "pr_number": number,
        "final_head_sha": "a" * 40,
        "merge_sha": "b" * 40,
    }


class RemainingWorkPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_repository_plan_and_docs_are_valid(self) -> None:
        tasks = MODULE.validate_graph(copy.deepcopy(self.plan))
        MODULE.validate_docs(tasks, RUNBOOK_PATH, CATALOG_PATH, PROMPT_PATH)
        self.assertEqual(len(tasks), 65)
        self.assertEqual(tasks[0]["id"], "BOOT-001")
        self.assertEqual(tasks[-1]["id"], "STB-012")

    def test_valid_ready_progression_is_accepted(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["tasks"][0]["status"] = "PASSED"
        plan["tasks"][0]["evidence"] = evidence()
        plan["tasks"][1]["status"] = "READY"
        MODULE.validate_graph(plan)

    def test_valid_in_progress_frontier_is_accepted(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["tasks"][0]["status"] = "IN_PROGRESS"
        plan["tasks"][0]["execution"] = {
            "branch": "work/boot-001-remote-audit",
            "started_at": "2026-07-29T04:00:00Z",
        }
        MODULE.validate_graph(plan)

    def test_valid_blocked_frontier_is_accepted(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["tasks"][0]["status"] = "BLOCKED"
        plan["tasks"][0]["blocker"] = {
            "reason": "GitHub authentication unavailable",
            "required_input": "Repository read access",
            "owner_action": "Reconnect the GitHub integration",
        }
        MODULE.validate_graph(plan)

    def test_passed_without_evidence_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][0]["status"] = "PASSED"
        invalid["tasks"][1]["status"] = "READY"
        with self.assertRaisesRegex(ValueError, "PASSED requires object field evidence"):
            MODULE.validate_graph(invalid)

    def test_in_progress_without_execution_metadata_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][0]["status"] = "IN_PROGRESS"
        with self.assertRaisesRegex(ValueError, "requires object field execution"):
            MODULE.validate_graph(invalid)

    def test_blocked_without_blocker_metadata_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][0]["status"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "requires object field blocker"):
            MODULE.validate_graph(invalid)

    def test_second_task_cannot_unlock_before_frontier_completes(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][1]["status"] = "READY"
        with self.assertRaises(ValueError):
            MODULE.validate_graph(invalid)

    def test_task_after_frontier_must_remain_locked(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][0]["status"] = "PASSED"
        invalid["tasks"][0]["evidence"] = evidence()
        invalid["tasks"][1]["status"] = "READY"
        invalid["tasks"][2]["status"] = "BLOCKED"
        invalid["tasks"][2]["blocker"] = {
            "reason": "test",
            "required_input": "test",
            "owner_action": "test",
        }
        with self.assertRaisesRegex(ValueError, "task after frontier must remain LOCKED"):
            MODULE.validate_graph(invalid)

    def test_wrong_task_count_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"].pop()
        with self.assertRaisesRegex(ValueError, "expected 65 tasks"):
            MODULE.validate_graph(invalid)

    def test_duplicate_id_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][1]["id"] = invalid["tasks"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate task id"):
            MODULE.validate_graph(invalid)

    def test_duplicate_order_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][1]["order"] = invalid["tasks"][0]["order"]
        with self.assertRaisesRegex(ValueError, "duplicate order"):
            MODULE.validate_graph(invalid)

    def test_unknown_dependency_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][2]["depends_on"] = ["MISSING-999"]
        with self.assertRaisesRegex(ValueError, "unknown dependency"):
            MODULE.validate_graph(invalid)

    def test_forward_dependency_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["tasks"][1]["depends_on"] = ["SEC-001"]
        with self.assertRaisesRegex(ValueError, "dependency must precede"):
            MODULE.validate_graph(invalid)

    def test_irreversible_without_authorization_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.plan)
        task = next(item for item in invalid["tasks"] if item["id"] == "HIST-006")
        task["authorization_required"] = False
        with self.assertRaisesRegex(ValueError, "irreversible task must require authorization"):
            MODULE.validate_graph(invalid)

    def test_missing_task_reference_in_catalog_is_rejected(self) -> None:
        tasks = MODULE.validate_graph(copy.deepcopy(self.plan))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runbook = root / "runbook.md"
            catalog = root / "catalog.md"
            prompt = root / "prompt.md"
            runbook.write_text(RUNBOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            catalog.write_text(CATALOG_PATH.read_text(encoding="utf-8").replace("STB-012", "STB-FINAL"), encoding="utf-8")
            prompt.write_text(PROMPT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "catalog does not mention"):
                MODULE.validate_docs(tasks, runbook, catalog, prompt)

    def test_missing_prompt_safeguard_is_rejected(self) -> None:
        tasks = MODULE.validate_graph(copy.deepcopy(self.plan))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runbook = root / "runbook.md"
            catalog = root / "catalog.md"
            prompt = root / "prompt.md"
            runbook.write_text(RUNBOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            catalog.write_text(CATALOG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            prompt.write_text(PROMPT_PATH.read_text(encoding="utf-8").replace("AUTHORIZE STABLE-PUBLISH", "AUTHORIZE RELEASE"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prompt missing required safeguards"):
                MODULE.validate_docs(tasks, runbook, catalog, prompt)


if __name__ == "__main__":
    unittest.main()
