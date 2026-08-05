#!/usr/bin/env python3
"""Generate immutable release and alpha-channel manifests for CLI Core."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


RELEASE_BASE_URL = "https://deepseekagent.starseas.org/releases"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", choices=("alpha", "beta"), default="alpha")
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--webui-artifact", type=Path)
    parser.add_argument("--deepcode-artifact", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    artifact = args.artifact.resolve()
    output_dir = args.output_dir.resolve()
    if not artifact.is_file():
        raise SystemExit(f"artifact not found: {artifact}")
    webui_artifact = args.webui_artifact.resolve() if args.webui_artifact else None
    if webui_artifact is not None and not webui_artifact.is_file():
        raise SystemExit(f"webui artifact not found: {webui_artifact}")
    deepcode_artifact = args.deepcode_artifact.resolve() if args.deepcode_artifact else None
    if deepcode_artifact is not None and not deepcode_artifact.is_file():
        deepcode_artifact = None
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "core": {
            "filename": artifact.name,
            "url": f"/{artifact.name}",
            "size": artifact.stat().st_size,
            "sha256": sha256(artifact),
        }
    }
    if webui_artifact is not None:
        artifacts["webui"] = {
            "filename": webui_artifact.name,
            "url": f"/{webui_artifact.name}",
            "size": webui_artifact.stat().st_size,
            "sha256": sha256(webui_artifact),
            "license": "BSL-1.1",
        }
    if deepcode_artifact is not None:
        artifacts["deepcode"] = {
            "filename": deepcode_artifact.name,
            "url": f"/{deepcode_artifact.name}",
            "size": deepcode_artifact.stat().st_size,
            "sha256": sha256(deepcode_artifact),
            "license": "MIT",
            "upstream": "https://github.com/anomalyco/opencode",
        }

    release_manifest = {
        "schema_version": 1,
        "product": "deepagent",
        "channel": args.channel,
        "version": version,
        "platform": {"os": "darwin", "arch": "arm64"},
        "artifacts": artifacts,
    }
    release_name = f"deepagent-manifest-{version}.json"
    release_path = output_dir / release_name
    release_path.write_text(json.dumps(release_manifest, indent=2) + "\n", encoding="utf-8")

    channel_manifest = {
        "schema_version": 1,
        "product": "deepagent",
        "channel": args.channel,
        "version": version,
        "manifest_url": f"{RELEASE_BASE_URL}/manifests/{version}.json",
    }
    channel_path = output_dir / f"deepagent-channel-{args.channel}.json"
    channel_path.write_text(json.dumps(channel_manifest, indent=2) + "\n", encoding="utf-8")

    print(release_path)
    print(channel_path)


if __name__ == "__main__":
    main()
