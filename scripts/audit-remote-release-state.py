#!/usr/bin/env python3
"""Create a redacted, read-only snapshot of GitHub release state and public channels."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
USER_AGENT = "deepagent-remote-release-audit/3"
CHANNELS = {
    "cli-alpha": "https://deepseekagent.starseas.org/releases/channels/alpha.json",
    "webui-beta": "https://deepseekagent.starseas.org/releases/channels/beta.json",
    "core-stable": "https://deepseekagent.starseas.org/releases/channels/stable.json",
    "electron-preview": "https://deepseekagent.starseas.org/releases/desktop/channels/preview.json",
    "electron-stable": "https://deepseekagent.starseas.org/releases/desktop/channels/stable.json",
}
FAILURE_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "startup_failure",
    "stale",
}
ACTIVE_STATUSES = ["queued", "in_progress", "waiting", "requested", "pending"]


def github_request(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def paginate_list(endpoint: str, token: str) -> list[Any]:
    values: list[Any] = []
    for page in range(1, 101):
        separator = "&" if "?" in endpoint else "?"
        body = github_request(f"{endpoint}{separator}per_page=100&page={page}", token)
        if not isinstance(body, list):
            raise RuntimeError(f"Expected list response from {endpoint}")
        values.extend(body)
        if len(body) < 100:
            return values
    raise RuntimeError(f"Pagination exceeded safety limit for {endpoint}")


def run_record(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(run["id"]),
        "name": run.get("name"),
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "head_branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
        "run_number": run.get("run_number"),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "html_url": run.get("html_url"),
    }


def action_runs(api_base: str, token: str, statuses: list[str]) -> list[dict[str, Any]]:
    """List active workflow runs using only documented status filters."""
    seen: set[int] = set()
    results: list[dict[str, Any]] = []
    for status in statuses:
        for page in range(1, 101):
            encoded = urllib.parse.urlencode({"status": status, "per_page": 100, "page": page})
            body = github_request(f"{api_base}/actions/runs?{encoded}", token)
            values = body.get("workflow_runs", [])
            for run in values:
                run_id = int(run["id"])
                if run_id in seen:
                    continue
                seen.add(run_id)
                results.append(run_record(run))
            if len(values) < 100:
                break
        else:
            raise RuntimeError(f"Action run pagination exceeded safety limit for status={status}")
    return sorted(results, key=lambda item: item.get("updated_at") or "", reverse=True)


def completed_failure_runs(api_base: str, token: str) -> list[dict[str, Any]]:
    """Query documented status=completed and filter failure conclusions locally.

    GitHub caps a filtered workflow-run search at 1,000 results. The extra page
    request fails closed if that cap would truncate this audit.
    """
    results: list[dict[str, Any]] = []
    seen: set[int] = set()
    for page in range(1, 12):
        encoded = urllib.parse.urlencode({"status": "completed", "per_page": 100, "page": page})
        body = github_request(f"{api_base}/actions/runs?{encoded}", token)
        values = body.get("workflow_runs", [])
        if page == 11 and values:
            raise RuntimeError("Completed workflow-run audit exceeded GitHub's 1,000-result search cap")
        for run in values:
            if run.get("conclusion") not in FAILURE_CONCLUSIONS:
                continue
            run_id = int(run["id"])
            if run_id in seen:
                continue
            seen.add(run_id)
            results.append(run_record(run))
        if len(values) < 100:
            return sorted(results, key=lambda item: item.get("updated_at") or "", reverse=True)
    raise RuntimeError("Completed workflow-run audit did not terminate within pagination safety limit")


def fetch_channel(name: str, url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise RuntimeError(f"Channel response too large: {name}")
            text = raw.decode("utf-8", errors="replace")
            parsed: Any = None
            parse_error: str | None = None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as error:
                parse_error = str(error)
            return {
                "name": name,
                "url": url,
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "json": parsed,
                "parse_error": parse_error,
            }
    except urllib.error.HTTPError as error:
        raw = error.read(65_536)
        return {
            "name": name,
            "url": url,
            "http_status": int(error.code),
            "content_type": error.headers.get("Content-Type") if error.headers else None,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "json": None,
            "parse_error": None,
        }
    except (urllib.error.URLError, TimeoutError) as error:
        return {
            "name": name,
            "url": url,
            "http_status": None,
            "content_type": None,
            "sha256": None,
            "json": None,
            "parse_error": f"network-error: {error}",
        }


def release_record(release: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": release.get("id"),
        "tag_name": release.get("tag_name"),
        "name": release.get("name"),
        "draft": release.get("draft"),
        "prerelease": release.get("prerelease"),
        "created_at": release.get("created_at"),
        "published_at": release.get("published_at"),
        "target_commitish": release.get("target_commitish"),
        "html_url": release.get("html_url"),
        "assets": [
            {
                "name": asset.get("name"),
                "size": asset.get("size"),
                "content_type": asset.get("content_type"),
                "download_count": asset.get("download_count"),
            }
            for asset in release.get("assets", [])
        ],
    }


def append_runs(lines: list[str], title: str, values: list[dict[str, Any]]) -> None:
    lines.extend(["", title, ""])
    if not values:
        lines.append("无。")
        return
    lines.extend(
        [
            "| Run | Workflow | Status | Conclusion | Event | Branch | Head | Updated |",
            "|---:|---|---|---|---|---|---|---|",
        ]
    )
    for item in values:
        lines.append(
            f"| {item['id']} | {item['name'] or ''} | {item['status'] or ''} | "
            f"{item['conclusion'] or ''} | {item['event'] or ''} | {item['head_branch'] or ''} | "
            f"`{(item['head_sha'] or '')[:12]}` | {item['updated_at'] or ''} |"
        )


def markdown(snapshot: dict[str, Any]) -> str:
    github = snapshot["github"]
    tags = github["tags"]
    releases = github["releases"]
    active = github["active_workflow_runs"]
    actionable_failed = github["actionable_failed_workflow_runs"]
    historical_failed = github["historical_failed_workflow_runs"]
    channels = snapshot["public_channels"]
    historical_by_conclusion = Counter(item.get("conclusion") or "unknown" for item in historical_failed)
    historical_by_branch = Counter(item.get("head_branch") or "<none>" for item in historical_failed)

    lines = [
        "# GitHub Tag、Release、Actions 与公开渠道远程审计",
        "",
        f"> 观测时间（UTC）：`{snapshot['observed_at']}`  ",
        f"> 仓库：`{snapshot['repository']}`  ",
        f"> 审计 Head：`{snapshot['head_sha']}`  ",
        "> 性质：只读审计；未创建、修改或删除 Tag、Release、Channel 或 Secret。",
        "",
        "## 1. 当前事实摘要",
        "",
        f"- 默认分支：`{github['default_branch']}` @ `{github['default_branch_head']}`",
        f"- 开放 PR：{len(github['open_pull_requests'])}",
        f"- Tags：{len(tags)}",
        f"- Releases：{len(releases)}",
        f"- 当前 Active Actions（已排除本审计自身）：{len(active)}",
        f"- 当前引用 Head 上的失败类 Actions：{len(actionable_failed)}",
        f"- 历史/已被新 Head 取代的失败类 Actions：{len(historical_failed)}",
        "",
        "“当前引用 Head”包括默认分支最新 Head 和所有开放 PR 的最新 Head。旧 PR Commit、旧分支 Commit 或已被后续提交替代的失败运行保留为历史证据，不算当前阻塞。",
        "",
        "## 2. Tags",
        "",
    ]
    if not tags:
        lines.append("未发现 Tag。")
    else:
        lines.extend(["| Tag | Commit |", "|---|---|"])
        lines.extend(f"| `{item['name']}` | `{item['commit_sha']}` |" for item in tags)

    lines.extend(["", "## 3. Releases", ""])
    if not releases:
        lines.append("未发现 GitHub Release（包括 Draft 和 Prerelease）。")
    else:
        lines.extend(["| Tag | 名称 | Draft | Prerelease | Published at | Assets |", "|---|---|---:|---:|---|---:|"])
        for item in releases:
            lines.append(
                f"| `{item['tag_name']}` | {item['name'] or ''} | {item['draft']} | "
                f"{item['prerelease']} | {item['published_at'] or ''} | {len(item['assets'])} |"
            )

    append_runs(lines, "## 4. 当前 Active Actions", active)
    append_runs(lines, "## 5. 当前引用 Head 上的失败类 Actions", actionable_failed)

    lines.extend(["", "## 6. 历史失败/取消 Actions 汇总", ""])
    lines.append(f"完整扫描记录数：**{len(historical_failed)}**。完整逐条记录保存在同一 workflow artifact 的 `remote-release-audit.json`。")
    lines.extend(["", "### 按 conclusion", "", "| Conclusion | 数量 |", "|---|---:|"])
    for key, count in sorted(historical_by_conclusion.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(["", "### 按分支（前 20）", "", "| Branch | 数量 |", "|---|---:|"])
    for key, count in historical_by_branch.most_common(20):
        lines.append(f"| `{key}` | {count} |")

    lines.extend(["", "## 7. 公开渠道", "", "| Channel | HTTP | JSON | SHA-256 |", "|---|---:|---|---|"])
    for item in channels:
        json_state = "valid" if item["json"] is not None else (item["parse_error"] or "none")
        lines.append(
            f"| `{item['name']}` | {item['http_status'] if item['http_status'] is not None else 'network-error'} | "
            f"{json_state} | `{item['sha256'] or ''}` |"
        )

    lines.extend(
        [
            "",
            "## 8. 渠道内容（公开 JSON）",
            "",
            "以下只记录公开端点返回的 JSON，不包含 GitHub Secret 或私密凭据。",
            "",
        ]
    )
    for item in channels:
        lines.extend([f"### {item['name']}", "", f"URL：`{item['url']}`", ""])
        if item["json"] is None:
            lines.append(f"状态：`HTTP {item['http_status']}`；`{item['parse_error'] or 'no JSON body'}`")
        else:
            lines.extend(["```json", json.dumps(item["json"], ensure_ascii=False, indent=2), "```"])
        lines.append("")

    lines.extend(
        [
            "## 9. 判定纪律",
            "",
            "- 本报告只证明观测时点的远程状态。",
            "- Draft Release、Prerelease、Tag 和公开 Channel 必须分别判断，不能相互替代。",
            "- 历史失败运行不能覆盖同一 PR 最终 Head 的成功证据，也不能被删除来伪造成功。",
            "- 公开渠道 HTTP 200 也不证明安装、升级、回滚、签名、公证或用户验收通过。",
            "- 凭据 Owner Gate 未关闭前，不得执行历史重写或发布渠道提升。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    head_sha = os.environ.get("GITHUB_SHA", "").strip()
    current_run_id = int(os.environ.get("GITHUB_RUN_ID", "0") or 0)
    output_dir = Path(os.environ.get("AUDIT_OUTPUT_DIR", "dist/remote-release-audit"))
    if not repository or "/" not in repository:
        print("GITHUB_REPOSITORY is required", file=sys.stderr)
        return 2
    if not token:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    api_base = f"https://api.github.com/repos/{repository}"
    repo = github_request(api_base, token)
    default_branch = repo["default_branch"]
    default_branch_record = github_request(f"{api_base}/branches/{urllib.parse.quote(default_branch, safe='')}", token)
    default_branch_head = default_branch_record["commit"]["sha"]
    tags_raw = paginate_list(f"{api_base}/tags", token)
    releases_raw = paginate_list(f"{api_base}/releases", token)
    branches_raw = paginate_list(f"{api_base}/branches", token)
    pulls_raw = paginate_list(f"{api_base}/pulls?state=open", token)

    open_pull_requests = [
        {
            "number": item.get("number"),
            "title": item.get("title"),
            "head_branch": item.get("head", {}).get("ref"),
            "head_sha": item.get("head", {}).get("sha"),
            "base_branch": item.get("base", {}).get("ref"),
            "draft": item.get("draft"),
            "html_url": item.get("html_url"),
        }
        for item in pulls_raw
    ]
    current_reference_shas = {default_branch_head}
    current_reference_shas.update(
        item["head_sha"] for item in open_pull_requests if item.get("head_sha")
    )

    active_runs = [
        item for item in action_runs(api_base, token, ACTIVE_STATUSES)
        if item["id"] != current_run_id
    ]
    failed_runs = completed_failure_runs(api_base, token)
    actionable_failed = [item for item in failed_runs if item.get("head_sha") in current_reference_shas]
    historical_failed = [item for item in failed_runs if item.get("head_sha") not in current_reference_shas]

    snapshot = {
        "schema_version": 3,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "head_sha": head_sha,
        "audit_run_id": current_run_id,
        "github": {
            "default_branch": default_branch,
            "default_branch_head": default_branch_head,
            "open_pull_requests": open_pull_requests,
            "current_reference_shas": sorted(current_reference_shas),
            "tags": [
                {"name": item.get("name"), "commit_sha": item.get("commit", {}).get("sha")}
                for item in tags_raw
            ],
            "releases": [release_record(item) for item in releases_raw],
            "branches": [
                {
                    "name": item.get("name"),
                    "commit_sha": item.get("commit", {}).get("sha"),
                    "protected": item.get("protected"),
                }
                for item in branches_raw
            ],
            "active_workflow_runs": active_runs,
            "actionable_failed_workflow_runs": actionable_failed,
            "historical_failed_workflow_runs": historical_failed,
        },
        "public_channels": [fetch_channel(name, url) for name, url in CHANNELS.items()],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "remote-release-audit.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = markdown(snapshot) + "\n"
    (output_dir / "remote-release-audit.md").write_text(report, encoding="utf-8")
    print(report)
    return 1 if active_runs or actionable_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
