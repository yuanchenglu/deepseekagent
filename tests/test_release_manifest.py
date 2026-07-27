import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate-release-manifest.py"
BUILD_SCRIPT = Path(__file__).parents[1] / "scripts" / "build-release.sh"
INSTALL_SCRIPT = Path(__file__).parents[1] / "scripts" / "install-release.sh"


def test_release_manifest_matches_artifact_and_alpha_channel(tmp_path):
    artifact = tmp_path / "deepagent-core-0.9.0-alpha.1.tar.gz"
    artifact.write_bytes(b"immutable release artifact")
    output = tmp_path / "output"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--version", "v0.9.0-alpha.1",
            "--artifact", str(artifact),
            "--output-dir", str(output),
        ],
        check=True,
    )

    release = json.loads((output / "deepagent-manifest-0.9.0-alpha.1.json").read_text())
    core = release["artifacts"]["core"]
    assert release["product"] == "deepagent"
    assert release["channel"] == "alpha"
    assert release["version"] == "0.9.0-alpha.1"
    assert release["platform"] == {"os": "darwin", "arch": "arm64"}
    assert core["filename"] == artifact.name
    assert core["size"] == artifact.stat().st_size
    assert core["sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()

    channel = json.loads((output / "deepagent-channel-alpha.json").read_text())
    assert channel["version"] == release["version"]
    assert channel["manifest_url"].endswith("/manifests/0.9.0-alpha.1.json")


def test_release_manifest_refuses_missing_artifact(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--version", "0.9.0-alpha.1",
            "--artifact", str(tmp_path / "missing.tar.gz"),
            "--output-dir", str(tmp_path / "output"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "artifact not found" in completed.stderr


def test_release_manifest_can_publish_separately_licensed_webui(tmp_path):
    core = tmp_path / "deepagent-0.9.0-beta.1.tar.gz"
    webui = tmp_path / "deepagent-webui-server-0.9.0-beta.1.tar.gz"
    core.write_bytes(b"core")
    webui.write_bytes(b"webui")
    output = tmp_path / "output"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--version", "0.9.0-beta.1",
            "--channel", "beta",
            "--artifact", str(core),
            "--webui-artifact", str(webui),
            "--output-dir", str(output),
        ],
        check=True,
    )

    manifest = json.loads((output / "deepagent-manifest-0.9.0-beta.1.json").read_text())
    assert manifest["channel"] == "beta"
    assert (output / "deepagent-channel-beta.json").is_file()
    assert manifest["artifacts"]["webui"] == {
        "filename": webui.name,
        "url": f"/{webui.name}",
        "size": len(b"webui"),
        "sha256": hashlib.sha256(b"webui").hexdigest(),
        "license": "BSL-1.1",
    }


def test_release_manifest_can_publish_managed_deepcode_runtime(tmp_path):
    core = tmp_path / "deepagent-0.9.0-beta.1.tar.gz"
    deepcode = tmp_path / "deepagent-deepcode-0.9.0-beta.1.tar.gz"
    core.write_bytes(b"core")
    deepcode.write_bytes(b"deepcode")
    output = tmp_path / "output"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--version", "0.9.0-beta.1",
            "--artifact", str(core),
            "--deepcode-artifact", str(deepcode),
            "--output-dir", str(output),
        ],
        check=True,
    )

    manifest = json.loads((output / "deepagent-manifest-0.9.0-beta.1.json").read_text())
    assert manifest["artifacts"]["deepcode"] == {
        "filename": deepcode.name,
        "url": f"/{deepcode.name}",
        "size": len(b"deepcode"),
        "sha256": hashlib.sha256(b"deepcode").hexdigest(),
        "license": "MIT",
        "upstream": "https://github.com/anomalyco/opencode",
    }


def test_release_builder_refuses_version_file_mismatch():
    completed = subprocess.run(
        ["bash", str(BUILD_SCRIPT), "--core-only", "--version", "99.99.99-alpha.test"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "VERSION" in completed.stdout


def test_release_installer_refuses_channel_manifest_url_outside_selected_source(tmp_path):
    channel = tmp_path / "channel.json"
    channel.write_text(json.dumps({
        "schema_version": 1,
        "product": "deepagent",
        "channel": "alpha",
        "version": "0.9.0-alpha.1",
        "manifest_url": "https://attacker.invalid/release.json",
    }))
    command = f'''
source "{INSTALL_SCRIPT}"
TMP_DIR="{tmp_path}"
PYTHON_PATH="{sys.executable}"
RELEASE_BASE_URL="https://deepseekagent.starseas.org/releases"
VERSION="latest-alpha"
CHANNEL="alpha"
curl_download() {{ cp "{channel}" "$2"; }}
resolve_release_manifest
'''

    completed = subprocess.run(
        ["bash", "-c", command],
        env={**os.environ, "HOME": str(tmp_path / "home")},
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "outside the selected release source" in completed.stderr


def test_release_installer_refuses_channel_identity_mismatch(tmp_path):
    channel = tmp_path / "channel.json"
    channel.write_text(json.dumps({
        "schema_version": 1,
        "product": "deepagent",
        "channel": "beta",
        "version": "0.9.0-alpha.1",
        "manifest_url": "https://deepseekagent.starseas.org/releases/manifests/0.9.0-alpha.1.json",
    }))
    command = f'''
source "{INSTALL_SCRIPT}"
TMP_DIR="{tmp_path}"
PYTHON_PATH="{sys.executable}"
RELEASE_BASE_URL="https://deepseekagent.starseas.org/releases"
VERSION="latest-alpha"
CHANNEL="alpha"
curl_download() {{ cp "{channel}" "$2"; }}
resolve_release_manifest
'''

    completed = subprocess.run(
        ["bash", "-c", command],
        env={**os.environ, "HOME": str(tmp_path / "home")},
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "Channel name mismatch" in completed.stderr
