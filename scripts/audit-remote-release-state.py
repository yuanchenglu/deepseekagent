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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
USER_AGENT = "deepagent-remote-release-audit/1"
CHANNELS = {
    "cli-alpha": "https://deepseekagent.starseas.org/releases/channels/alpha.json",
    "webui-beta": "https://deepseekagent.starseas.org/releases/channels/beta.json",
    "core-stable": "https://deepseekagent.starseas.org/releases/channels/stable.json",
    "electron-preview": "https://deepseekagent.starseas.org/releases/desktop/channels/preview.json",
    "electron-stable": "https://deepseekagent.starseas.org/releases/desktop/channels/stable.json",
}
FAILURE_STATUSES = [
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "startup_failure",
    "stale",
]
ACTIVE_STATUSES = ["queued", "in_progress", "waiting", "requested", "pending"]


def github_request(url: str, token: str) -> tuple[Any, dict[str, str]]:
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
        body = json.loads(response.read().decode("utf-8"))
        headers = {key.lower(): value for key, value in response.headers.items()}
        return body, headers


def paginate(endpoint: str, token: str) -> list[Any]:
    values: list[Any] = []
    page = 1
    while True:
        separator = "&" if "?" in endpoint else "?"
        body, _ = github_request(f"{endpoint}{separator}per_page=100&page={page}", token)
        if not isinstance(body, list):
            raise RuntimeError(f"Expected list response from {endpoint}")
        values.extend(body)
        if len(body) < 100:
            return values
        page += 1
        if page > 100:
            raise RuntimeError(f"Pagination exceeded safety limit for {endpoint}")


def action_runs(api_base: str, token: str, statuses: list[str]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    results: list[dict[str, Any]] = []
    for status in statuses:
        encoded = urllib.parse.urlencode({"status": status, "per_page": 100})
        body, _ = github_request(f"{api_base}/actions/runs?{encoded}", token)
        for run in body.get("workflow_runs", []):
            run_id = int(run["id"])
            if run_id in seen:
                continue
            seen.add(run_id)
            results.append(
                {
                    "id": run_id,
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
            )
    return sorted(results, key=lambda item: item.get("updated_at") or "", reverse=True)


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


def markdown(snapshot: dict[str, Any]) -> str:
    tags = snapshot["github"]["tags"]
    releases = snapshot["github"]["releases"]
    active = snapshot["github"]["active_workflow_runs"]
    failed = snapshot["github"]["failed_workflow_runs"]
    channels = snapshot["public_channels"]

    lines = [
        "# GitHub Tag、Release、Actions 与公开渠道远程审计",
        "",
        f"> 观测时间（UTC）：`{snapshot['observed_at']}`  ",
        f"> 仓库：`{snapshot['repository']}`  ",
        f"> 审计 Head：`{snapshot['head_sha']}`  ",
        "> 性质：只读审计；未创建、修改或删除 Tag、Release、Channel 或 Secret。",
        "",
        "## 1. 摘要",
        "",
        f"- Tags：{len(tags)}",
        f"- Releases：{len(releases)}",
        f"- Active Actions（queued/in progress/waiting/requested/pending）：{len(active)}",
        f"- Recent failed-class Actions：{len(failed)}",
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

    def append_runs(title: str, values: list[dict[str, Any]]) -> None:
        lines.extend(["", title, ""])
        if not values:
            lines.append("无。")
            return
        lines.extend(["| Run | Workflow | Status | Conclusion | Event | Branch | Updated |", "|---:|---|---|---|---|---|---|"])
        for item in values:
            lines.append(
                f"| {item['id']} | {item['name'] or ''} | {item['status'] or ''} | "
                f"{item['conclusion'] or ''} | {item['event'] or ''} | {item['head_branch'] or ''} | "
                f"{item['updated_at'] or ''} |"
            )

    append_runs("## 4. 当前 Active Actions", active)
    append_runs("## 5. 失败类 Actions（API 当前可返回范围）", failed)

    lines.extend(["", "## 6. 公开渠道", "", "| Channel | HTTP | JSON | SHA-256 |", "|---|---:|---|---|"])
    for item in channels:
        json_state = "valid" if item["json"] is not None else (item["parse_error"] or "none")
        lines.append(
            f"| `{item['name']}` | {item['http_status'] if item['http_status'] is not None else 'network-error'} | "
            f"{json_state} | `{item['sha256'] or ''}` |"
        )

    lines.extend(
        [
            "",
            "## 7. 渠道内容（公开 JSON）",
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
            "## 8. 判定纪律",
            "",
            "- 本报告只证明观测时点的远程状态。",
            "- Draft Release、Prerelease、Tag 和公开 Channel 必须分别判断，不能相互替代。",
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
    output_dir = Path(os.environ.get("AUDIT_OUTPUT_DIR", "dist/remote-release-audit"))
    if not repository or "/" not in repository:
        print("GITHUB_REPOSITORY is required", file=sys.stderr)
        return 2
    if not token:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    api_base = f"https://api.github.com/repos/{repository}"
    tags_raw = paginate(f"{api_base}/tags", token)
    releases_raw = paginate(f"{api_base}/releases", token)
    branches_raw = paginate(f"{api_base}/branches", token)

    snapshot = {
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "head_sha": head_sha,
        "github": {
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
            "active_workflow_runs": action_runs(api_base, token, ACTIVE_STATUSES),
            "failed_workflow_runs": action_runs(api_base, token, FAILURE_STATUSES),
        },
        "public_channels": [fetch_channel(name, url) for name, url in CHANNELS.items()],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "remote-release-audit.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "remote-release-audit.md").write_text(markdown(snapshot) + "\n", encoding="utf-8")
    print(markdown(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
