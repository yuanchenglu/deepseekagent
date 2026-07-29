#!/usr/bin/env python3
"""Validate the deterministic remaining-work graph and its persisted execution state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

VALID_STATUSES = {"READY", "LOCKED", "IN_PROGRESS", "BLOCKED", "FAILED", "PASSED", "WAIVED"}
COMPLETED_STATUSES = {"PASSED", "WAIVED"}
FRONTIER_STATUSES = {"READY", "IN_PROGRESS", "BLOCKED", "FAILED"}
VALID_EXECUTORS = {"local-ai", "owner", "owner+local-ai"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "repository",
    "default_branch",
    "release_branch",
    "authoritative_runbook",
    "status_values",
    "selection_rule",
    "tasks",
}
REQUIRED_TASK_FIELDS = {
    "id",
    "order",
    "phase",
    "title",
    "depends_on",
    "executor",
    "irreversible",
    "authorization_required",
    "status",
}
STATE_METADATA_KEYS = {"execution", "evidence", "blocker", "failure", "waiver"}
ID_PATTERN = re.compile(r"^[A-Z]+-[0-9]{3}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_TASK_COUNT = 65
EXPECTED_RUNBOOK = "docs/open-source-readiness/16-REMAINING-WORK-EXECUTION-RUNBOOK.md"


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing plan file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(value, dict):
        fail("plan root must be an object")
    return value


def require_mapping(task: dict[str, Any], key: str, fields: set[str]) -> dict[str, Any]:
    value = task.get(key)
    if not isinstance(value, dict):
        fail(f"{task['id']} status {task['status']} requires object field {key}")
    missing = fields - set(value)
    if missing:
        fail(f"{task['id']} {key} missing fields: {sorted(missing)}")
    for field in fields:
        if not isinstance(value[field], str) or not value[field].strip():
            fail(f"{task['id']} {key}.{field} must be a non-empty string")
    return value


def validate_state_metadata(task: dict[str, Any]) -> None:
    status = task["status"]
    task_id = task["id"]
    present = STATE_METADATA_KEYS & set(task)

    if status in {"READY", "LOCKED"}:
        if present:
            fail(f"{task_id} status {status} must not retain state metadata: {sorted(present)}")
        return

    if status == "IN_PROGRESS":
        execution = require_mapping(task, "execution", {"branch", "started_at"})
        if not execution["branch"].startswith("work/"):
            fail(f"{task_id} execution.branch must start with work/")
        if present - {"execution"}:
            fail(f"{task_id} IN_PROGRESS has incompatible metadata: {sorted(present - {'execution'})}")
        return

    if status == "BLOCKED":
        require_mapping(task, "blocker", {"reason", "required_input", "owner_action"})
        if present - {"blocker"}:
            fail(f"{task_id} BLOCKED has incompatible metadata: {sorted(present - {'blocker'})}")
        return

    if status == "FAILED":
        require_mapping(task, "failure", {"evidence_file", "root_cause", "next_action"})
        if present - {"failure"}:
            fail(f"{task_id} FAILED has incompatible metadata: {sorted(present - {'failure'})}")
        return

    if status == "PASSED":
        evidence = task.get("evidence")
        if not isinstance(evidence, dict):
            fail(f"{task_id} PASSED requires object field evidence")
        required = {"evidence_file", "pr_number", "final_head_sha", "merge_sha"}
        missing = required - set(evidence)
        if missing:
            fail(f"{task_id} evidence missing fields: {sorted(missing)}")
        if not isinstance(evidence["evidence_file"], str) or not evidence["evidence_file"].strip():
            fail(f"{task_id} evidence.evidence_file must be a non-empty string")
        if not isinstance(evidence["pr_number"], int) or evidence["pr_number"] <= 0:
            fail(f"{task_id} evidence.pr_number must be a positive integer")
        for field in ("final_head_sha", "merge_sha"):
            if not isinstance(evidence[field], str) or not SHA_PATTERN.fullmatch(evidence[field]):
                fail(f"{task_id} evidence.{field} must be a 40-character lowercase commit SHA")
        if present - {"evidence"}:
            fail(f"{task_id} PASSED has incompatible metadata: {sorted(present - {'evidence'})}")
        return

    if status == "WAIVED":
        if task["irreversible"] or task["id"].startswith(("SEC-", "HIST-")):
            fail(f"{task_id} cannot be waived")
        if task.get("waivable") is not True:
            fail(f"{task_id} WAIVED requires explicit waivable=true in the Plan")
        require_mapping(
            task,
            "waiver",
            {"owner", "authorized_at", "rationale", "compensating_controls", "evidence_file"},
        )
        if present - {"waiver"}:
            fail(f"{task_id} WAIVED has incompatible metadata: {sorted(present - {'waiver'})}")
        return

    fail(f"unsupported status for {task_id}: {status}")


def validate_graph(plan: dict[str, Any]) -> list[dict[str, Any]]:
    missing_top = REQUIRED_TOP_LEVEL - set(plan)
    if missing_top:
        fail(f"missing top-level fields: {sorted(missing_top)}")
    if plan["schema_version"] != 1:
        fail("schema_version must be 1")
    if plan["repository"] != "yuanchenglu/deepseekagent":
        fail("repository must be yuanchenglu/deepseekagent")
    if plan["default_branch"] != "develop" or plan["release_branch"] != "master":
        fail("branch policy must remain develop -> master")
    if plan["authoritative_runbook"] != EXPECTED_RUNBOOK:
        fail(f"authoritative_runbook must be {EXPECTED_RUNBOOK}")
    if set(plan["status_values"]) != VALID_STATUSES:
        fail("status_values does not match the allowed state machine")

    tasks = plan["tasks"]
    if not isinstance(tasks, list) or not tasks:
        fail("tasks must be a non-empty list")
    if len(tasks) != EXPECTED_TASK_COUNT:
        fail(f"expected {EXPECTED_TASK_COUNT} tasks, found {len(tasks)}")

    ids: list[str] = []
    orders: list[int] = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            fail(f"task at index {index} must be an object")
        missing = REQUIRED_TASK_FIELDS - set(task)
        if missing:
            fail(f"task at index {index} missing fields: {sorted(missing)}")
        task_id = task["id"]
        if not isinstance(task_id, str) or not ID_PATTERN.fullmatch(task_id):
            fail(f"invalid task id: {task_id!r}")
        if task_id in by_id:
            fail(f"duplicate task id: {task_id}")
        if not isinstance(task["order"], int) or task["order"] <= 0:
            fail(f"invalid order for {task_id}")
        if not isinstance(task["depends_on"], list) or not all(isinstance(x, str) for x in task["depends_on"]):
            fail(f"depends_on must be a string list for {task_id}")
        if task["status"] not in VALID_STATUSES:
            fail(f"invalid status for {task_id}: {task['status']}")
        if task["executor"] not in VALID_EXECUTORS:
            fail(f"invalid executor for {task_id}: {task['executor']}")
        if not isinstance(task["irreversible"], bool) or not isinstance(task["authorization_required"], bool):
            fail(f"boolean fields invalid for {task_id}")
        if task["irreversible"] and not task["authorization_required"]:
            fail(f"irreversible task must require authorization: {task_id}")
        validate_state_metadata(task)
        ids.append(task_id)
        orders.append(task["order"])
        by_id[task_id] = task

    duplicate_orders = [order for order, count in Counter(orders).items() if count > 1]
    if duplicate_orders:
        fail(f"duplicate order values: {duplicate_orders}")
    if orders != sorted(orders):
        fail("tasks must be stored in ascending order")

    for task in tasks:
        for dependency in task["depends_on"]:
            if dependency not in by_id:
                fail(f"unknown dependency {dependency} for {task['id']}")
            if by_id[dependency]["order"] >= task["order"]:
                fail(f"dependency must precede task: {dependency} -> {task['id']}")
        if task["status"] != "LOCKED":
            incomplete_dependencies = [
                dependency
                for dependency in task["depends_on"]
                if by_id[dependency]["status"] not in COMPLETED_STATUSES
            ]
            if incomplete_dependencies:
                fail(f"{task['id']} is unlocked before dependencies complete: {incomplete_dependencies}")

    indegree = {task_id: 0 for task_id in ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        for dependency in task["depends_on"]:
            outgoing[dependency].append(task["id"])
            indegree[task["id"]] += 1
    queue = deque(task_id for task_id, value in indegree.items() if value == 0)
    visited: list[str] = []
    while queue:
        current = queue.popleft()
        visited.append(current)
        for child in outgoing[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(visited) != len(tasks):
        fail("dependency graph contains a cycle")

    frontier_index: int | None = None
    for index, task in enumerate(tasks):
        if task["status"] not in COMPLETED_STATUSES:
            frontier_index = index
            break

    if frontier_index is None:
        return tasks

    frontier = tasks[frontier_index]
    if frontier["status"] not in FRONTIER_STATUSES:
        fail(f"first incomplete task {frontier['id']} must be READY/IN_PROGRESS/BLOCKED/FAILED")

    for task in tasks[:frontier_index]:
        if task["status"] not in COMPLETED_STATUSES:
            fail(f"task before frontier is not complete: {task['id']}")
    for task in tasks[frontier_index + 1 :]:
        if task["status"] != "LOCKED":
            fail(f"task after frontier must remain LOCKED: {task['id']}={task['status']}")

    expected_prefixes = {"BOOT", "SEC", "HIST", "CLI", "WEB", "DESK", "STB"}
    actual_prefixes = {task_id.split("-", 1)[0] for task_id in ids}
    if actual_prefixes != expected_prefixes:
        fail(f"unexpected phase prefixes: {sorted(actual_prefixes)}")
    if ids[0] != "BOOT-001" or ids[-1] != "STB-012":
        fail("graph boundaries must be BOOT-001 and STB-012")

    return tasks


def validate_docs(
    tasks: list[dict[str, Any]],
    runbook_path: Path,
    catalog_path: Path,
    prompt_path: Path,
) -> None:
    try:
        runbook = runbook_path.read_text(encoding="utf-8")
        catalog = catalog_path.read_text(encoding="utf-8")
        prompt = prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        fail(f"missing documentation file: {exc.filename}")

    missing_in_catalog = [task["id"] for task in tasks if task["id"] not in catalog]
    if missing_in_catalog:
        fail(f"acceptance catalog does not mention task IDs: {missing_in_catalog}")

    required_prompt_fragments = [
        "16-REMAINING-WORK-EXECUTION-RUNBOOK.md",
        "remaining-work-plan.json",
        "BOOT-001",
        "AUTHORIZE HIST-006",
        "AUTHORIZE STABLE-PUBLISH",
        "严禁同时实施两个 Work ID",
        "Tag 触发冲突",
    ]
    missing_fragments = [fragment for fragment in required_prompt_fragments if fragment not in prompt]
    if missing_fragments:
        fail(f"weak-AI prompt missing required safeguards: {missing_fragments}")

    for required in [
        "任何歧义都按失败关闭",
        "每次只做一个 Work ID",
        "Tag 冲突检查",
        "每个旧凭据均返回认证失败或权限拒绝",
        "P0/P1",
        "最终完成判定",
    ]:
        if required not in runbook:
            fail(f"runbook missing required section or safeguard: {required}")

    for required in [
        "剩余 65 个 Work ID",
        "BOOT-001",
        "SEC-007",
        "HIST-006",
        "CLI-013",
        "WEB-011",
        "DESK-011",
        "STB-012",
    ]:
        if required not in catalog:
            fail(f"acceptance catalog missing boundary or gate: {required}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path("docs/open-source-readiness/remaining-work-plan.json"),
    )
    parser.add_argument(
        "--runbook",
        type=Path,
        default=Path("docs/open-source-readiness/16-REMAINING-WORK-EXECUTION-RUNBOOK.md"),
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("docs/open-source-readiness/18-WORK-ID-ACCEPTANCE-CATALOG.md"),
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path("docs/open-source-readiness/17-WEAK-AI-DETERMINISTIC-HANDOFF-PROMPT.md"),
    )
    args = parser.parse_args()

    try:
        plan = load_json(args.plan)
        tasks = validate_graph(plan)
        validate_docs(tasks, args.runbook, args.catalog, args.prompt)
    except ValueError as exc:
        print(f"remaining-work validation failed: {exc}", file=sys.stderr)
        return 1

    phase_counts = Counter(task["phase"] for task in tasks)
    print(f"remaining-work validation passed: {len(tasks)} tasks")
    for phase, count in phase_counts.items():
        print(f"- {phase}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
