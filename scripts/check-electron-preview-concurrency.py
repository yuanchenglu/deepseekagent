#!/usr/bin/env python3
"""Fail closed when the Electron Preview concurrency contract drifts."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/release-electron-preview.yml")

EXPECTED_TOP_LEVEL_GROUP = (
    "  group: electron-preview-${{ github.event_name == 'workflow_dispatch' "
    "&& inputs.publish && format('publish-run-{0}', github.run_id) || "
    "format('validation-{0}', github.event.pull_request.number || github.ref) }}"
)
EXPECTED_TOP_LEVEL_CANCEL = (
    "  cancel-in-progress: ${{ !(github.event_name == 'workflow_dispatch' "
    "&& inputs.publish) }}"
)


def _policy(event_name: str, publish: bool, pr_number: int | None, ref: str, run_id: int) -> tuple[str, bool]:
    """Model the intended policy independently from the workflow text."""
    is_publish = event_name == "workflow_dispatch" and publish
    if is_publish:
        return f"electron-preview-publish-run-{run_id}", False
    discriminator = pr_number if pr_number is not None else ref
    return f"electron-preview-validation-{discriminator}", True


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    lines = text.splitlines()

    concurrency_index = lines.index("concurrency:")
    jobs_index = lines.index("jobs:")
    top_lines = lines[concurrency_index + 1 : jobs_index]
    while top_lines and not top_lines[-1]:
        top_lines.pop()
    if top_lines != [EXPECTED_TOP_LEVEL_GROUP, EXPECTED_TOP_LEVEL_CANCEL]:
        raise AssertionError(f"unexpected top-level concurrency block: {top_lines!r}")

    publish_index = lines.index("  publish:")
    publish_lines = lines[publish_index:]
    expected_publish_queue = [
        "    concurrency:",
        "      group: electron-preview-publish",
        "      queue: max",
    ]
    if not any(
        publish_lines[index : index + 3] == expected_publish_queue
        for index in range(len(publish_lines) - 2)
    ):
        raise AssertionError("publish job must use the fixed serialized queue")

    if "group: electron-preview-${{ github.workflow }}-${{ github.ref }}" in text:
        raise AssertionError("legacy shared validation/release group is still present")

    # Contract truth table.
    assert _policy("pull_request", False, 42, "refs/pull/42/merge", 1001) == (
        "electron-preview-validation-42",
        True,
    )
    assert _policy("pull_request", False, 42, "refs/pull/42/merge", 1002) == (
        "electron-preview-validation-42",
        True,
    )
    assert _policy("workflow_dispatch", False, None, "refs/heads/develop", 1003) == (
        "electron-preview-validation-refs/heads/develop",
        True,
    )
    assert _policy("workflow_dispatch", True, None, "refs/tags/v1.0.0-preview.1", 1004) == (
        "electron-preview-publish-run-1004",
        False,
    )
    assert _policy("workflow_dispatch", True, None, "refs/tags/v1.0.0-preview.2", 1005) == (
        "electron-preview-publish-run-1005",
        False,
    )

    print("Electron Preview concurrency contract is valid")


if __name__ == "__main__":
    main()
