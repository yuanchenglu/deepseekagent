#!/usr/bin/env python3
"""Fail-closed license inventory for the installed CLI Alpha environment."""

from __future__ import annotations

import argparse
import json
import re
from importlib import metadata
from pathlib import Path


CLASSIFIER_LICENSES = {
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: BSD License": "BSD-3-Clause",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
}

# These packages have incomplete wheel metadata. Each override is backed by
# the linked upstream repository and must be reviewed when its version changes.
LICENSE_OVERRIDES = {
    "edge-tts": {
        "license": "LGPL-3.0-only AND MIT",
        "evidence": "https://github.com/rany2/edge-tts/blob/master/LICENSE",
    },
    "fal-client": {
        "license": "Apache-2.0",
        "evidence": "https://github.com/fal-ai/fal/blob/main/LICENSE",
    },
}


def _canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _license_from_text(text: str) -> str | None:
    normalized = " ".join(text.split()).lower()
    if "apache license" in normalized and "version 2.0" in normalized:
        return "Apache-2.0"
    if "mozilla public license version 2.0" in normalized:
        return "MPL-2.0"
    if "gnu lesser general public license" in normalized and "version 3" in normalized:
        return "LGPL-3.0-only"
    if "permission is hereby granted, free of charge" in normalized:
        return "MIT"
    if "redistribution and use in source and binary forms" in normalized:
        if "neither the name" in normalized:
            return "BSD-3-Clause"
        return "BSD-2-Clause"
    if "python software foundation license" in normalized:
        return "PSF-2.0"
    if re.search(r"\bisc license\b", normalized):
        return "ISC"
    return None


def _license_for(dist: metadata.Distribution) -> tuple[str | None, str]:
    name = _canonical_name(dist.metadata.get("Name") or "")
    override = LICENSE_OVERRIDES.get(name)
    if override:
        return override["license"], override["evidence"]

    expression = (dist.metadata.get("License-Expression") or "").strip()
    if expression and expression.upper() != "UNKNOWN":
        return expression, "package metadata: License-Expression"

    license_value = (dist.metadata.get("License") or "").strip()
    if license_value and len(license_value) < 100:
        detected = _license_from_text(license_value) or license_value
        if detected.upper() not in {"UNKNOWN", "NONE"}:
            return detected, "package metadata: License"

    for classifier in dist.metadata.get_all("Classifier", []):
        if classifier in CLASSIFIER_LICENSES:
            return CLASSIFIER_LICENSES[classifier], f"package classifier: {classifier}"

    for file in dist.files or []:
        lowered = str(file).lower()
        if "dist-info" not in lowered or not any(
            token in Path(lowered).name for token in ("license", "copying")
        ):
            continue
        try:
            detected = _license_from_text(dist.locate_file(file).read_text(errors="replace"))
        except OSError:
            continue
        if detected:
            return detected, f"installed license file: {file}"
    return None, "no recognized license metadata or installed license file"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    entries = []
    unknown = []
    for dist in sorted(metadata.distributions(), key=lambda item: (item.metadata.get("Name") or "").lower()):
        name = dist.metadata.get("Name") or "unknown"
        if _canonical_name(name) == "deepagent":
            continue
        license_id, evidence = _license_for(dist)
        entry = {
            "name": name,
            "version": dist.version,
            "license": license_id or "UNKNOWN",
            "evidence": evidence,
        }
        entries.append(entry)
        if license_id is None:
            unknown.append(f"{name}=={dist.version}")

    report = {
        "schema_version": 1,
        "product": "deepagent",
        "scope": "installed Phase 1 Python runtime",
        "dependencies": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if unknown:
        raise SystemExit("Unknown dependency licenses: " + ", ".join(unknown))
    print(f"License audit passed for {len(entries)} installed distributions: {args.output}")


if __name__ == "__main__":
    main()
