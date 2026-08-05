#!/usr/bin/env bash
# DeepAgent macOS Apple Silicon CLI Alpha installer.
# This is the canonical source for https://deepseekagent.starseas.org/install.sh.

set -euo pipefail

PRODUCT="deepagent"
SCHEMA_VERSION=1
RELEASE_BASE_URL="${DEEPAGENT_RELEASE_BASE_URL:-https://deepseekagent.starseas.org/releases}"
RELEASE_BASE_URL="${RELEASE_BASE_URL%/}"
DEEPAGENT_HOME="${DEEPAGENT_HOME:-$HOME/.deepagent}"
INSTALL_DIR="$DEEPAGENT_HOME"
CHANNEL="${DEEPAGENT_CHANNEL:-alpha}"
VERSION_WAS_EXPLICIT=false
if [ -n "${DEEPAGENT_VERSION:-}" ]; then
    VERSION="$DEEPAGENT_VERSION"
    VERSION_WAS_EXPLICIT=true
else
    VERSION="latest-${CHANNEL}"
fi
SKIP_SETUP=false
TMP_DIR=""
UV_CMD=""
PYTHON_PATH=""
MANIFEST_FILE=""
CORE_NAME=""
CORE_URL=""
CORE_SIZE=""
CORE_SHA256=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_info() { echo -e "${CYAN}→${NC} $*"; }
log_success() { echo -e "${GREEN}✓${NC} $*"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*" >&2; }

usage() {
    cat <<'EOF'
Usage: install-release.sh [options]

Options:
  --version VERSION   Install an explicit version
  --channel CHANNEL   Select alpha or beta (default: alpha)
  --dir PATH          Set DEEPAGENT_HOME (must be an absolute safe path)
  --skip-setup        Do not print the setup reminder
  -h, --help          Show this help

Supported platform: macOS Apple Silicon (Darwin arm64) only.
EOF
}

parse_args() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --version)
                [ "$#" -ge 2 ] || { log_error "--version requires a value"; exit 2; }
                VERSION="${2#v}"
                VERSION_WAS_EXPLICIT=true
                shift 2
                ;;
            --channel)
                [ "$#" -ge 2 ] || { log_error "--channel requires a value"; exit 2; }
                case "$2" in alpha|beta) CHANNEL="$2" ;; *) log_error "--channel must be alpha or beta"; exit 2 ;; esac
                if [ "$VERSION_WAS_EXPLICIT" = false ]; then VERSION="latest-${CHANNEL}"; fi
                shift 2
                ;;
            --dir)
                [ "$#" -ge 2 ] || { log_error "--dir requires a value"; exit 2; }
                DEEPAGENT_HOME="$2"
                INSTALL_DIR="$2"
                shift 2
                ;;
            --skip-setup)
                SKIP_SETUP=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown argument: $1"
                usage >&2
                exit 2
                ;;
        esac
    done
}

cleanup() {
    if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}

detect_platform() {
    local os arch
    os="$(uname -s)"
    arch="$(uname -m)"
    if [ "$os" != "Darwin" ] || [ "$arch" != "arm64" ]; then
        log_error "DeepAgent CLI Alpha supports macOS Apple Silicon only."
        log_error "Detected: ${os} ${arch}"
        exit 1
    fi
}

validate_product_home() {
    case "$DEEPAGENT_HOME" in
        /*) ;;
        *) log_error "DEEPAGENT_HOME must be an absolute path: $DEEPAGENT_HOME"; exit 1 ;;
    esac

    case "$DEEPAGENT_HOME" in
        /|"$HOME"|"$HOME/.hermes"|"$HOME/.hermes/"*|"$HOME/.opencode"|"$HOME/.opencode/"*|"$HOME/.config/opencode"|"$HOME/.config/opencode/"*)
            log_error "Refusing unsafe or conflicting install directory: $DEEPAGENT_HOME"
            exit 1
            ;;
    esac

    if [ -d "$DEEPAGENT_HOME" ]; then
        local resolved
        resolved="$(cd "$DEEPAGENT_HOME" && pwd -P)"
        case "$resolved" in
            /|"$HOME"|"$HOME/.hermes"|"$HOME/.hermes/"*|"$HOME/.opencode"|"$HOME/.opencode/"*|"$HOME/.config/opencode"|"$HOME/.config/opencode/"*)
                log_error "Install directory resolves into a protected product path: $resolved"
                exit 1
                ;;
        esac
    fi
}

classify_existing_home() {
    [ -d "$DEEPAGENT_HOME" ] || return 0
    [ -n "$(find "$DEEPAGENT_HOME" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ] || return 0

    if [ -f "$DEEPAGENT_HOME/install-manifest.json" ]; then
        if ! grep -q '"product"[[:space:]]*:[[:space:]]*"deepagent"' "$DEEPAGENT_HOME/install-manifest.json"; then
            log_error "Existing install manifest does not belong to DeepAgent."
            exit 1
        fi
        return 0
    fi

    if [ -f "$DEEPAGENT_HOME/VERSION" ] && [ -d "$DEEPAGENT_HOME/deepagent" ]; then
        log_warn "Recognized a legacy DeepAgent installation; code will be backed up before migration."
        return 0
    fi

    local unknown=""
    local entry name
    for entry in "$DEEPAGENT_HOME"/* "$DEEPAGENT_HOME"/.[!.]* "$DEEPAGENT_HOME"/..?*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        name="$(basename "$entry")"
        case "$name" in
            .env|config.yaml|sessions.db|skills|sessions|cron|memories|logs|cache|data|config|runtime|profiles|active_profile) ;;
            *) unknown="${unknown}${name}\n" ;;
        esac
    done
    if [ -n "$unknown" ]; then
        log_error "The existing DEEPAGENT_HOME contains unrecognized files; refusing to overwrite:"
        printf '%b' "$unknown" >&2
        exit 1
    fi
}

validate_existing_layout_paths() {
    [ -d "$DEEPAGENT_HOME" ] || return 0
    local home_resolved entry resolved name link
    home_resolved="$(cd "$DEEPAGENT_HOME" && pwd -P)"

    for name in versions config data cache logs runtime skills; do
        entry="$DEEPAGENT_HOME/$name"
        if [ -L "$entry" ]; then
            log_error "Refusing symlinked DeepAgent directory: $entry"
            exit 1
        fi
        if [ -e "$entry" ] && [ ! -d "$entry" ]; then
            log_error "Expected a DeepAgent directory but found another file type: $entry"
            exit 1
        fi
        if [ -d "$entry" ]; then
            resolved="$(cd "$entry" && pwd -P)"
            case "$resolved" in
                "$home_resolved"/*) ;;
                *) log_error "DeepAgent directory escapes the product root: $entry"; exit 1 ;;
            esac
        fi
    done

    for name in .env config.yaml; do
        entry="$DEEPAGENT_HOME/$name"
        [ -L "$entry" ] || continue
        link="$(readlink "$entry")"
        case "$name:$link" in
            ".env:config/.env"|"config.yaml:config/config.yaml") ;;
            *) log_error "Refusing external or unknown compatibility symlink: $entry -> $link"; exit 1 ;;
        esac
    done

    for name in VERSION install-manifest.json config/.env config/config.yaml; do
        entry="$DEEPAGENT_HOME/$name"
        if [ -L "$entry" ]; then
            log_error "Refusing symlinked DeepAgent metadata: $entry"
            exit 1
        fi
    done

    entry="$DEEPAGENT_HOME/current"
    if [ -L "$entry" ]; then
        link="$(readlink "$entry")"
        case "$link" in
            versions/*)
                case "$link" in *..*) log_error "Unsafe current symlink: $link"; exit 1 ;; esac
                ;;
            *) log_error "Current symlink escapes the versions directory: $link"; exit 1 ;;
        esac
    elif [ -e "$entry" ]; then
        log_error "Expected current to be a managed symlink: $entry"
        exit 1
    fi
}

curl_download() {
    local url="$1" output="$2" description="$3" attempt
    for attempt in 1 2; do
        log_info "Downloading ${description} (${attempt}/2)"
        if curl -fL --connect-timeout 15 --max-time 900 --retry 0 "$url" -o "$output"; then
            return 0
        fi
    done
    log_error "Download failed: $url"
    return 1
}

install_uv() {
    if [ -n "${DEEPAGENT_UV:-}" ]; then
        UV_CMD="$DEEPAGENT_UV"
        [ -x "$UV_CMD" ] || { log_error "DEEPAGENT_UV is not executable: $UV_CMD"; exit 1; }
        return 0
    fi
    if command -v uv >/dev/null 2>&1; then
        UV_CMD="$(command -v uv)"
        return 0
    fi
    if [ -x "$HOME/.local/bin/uv" ]; then
        UV_CMD="$HOME/.local/bin/uv"
        return 0
    fi
    log_info "Installing the pinned Python environment manager"
    curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh
    UV_CMD="$HOME/.local/bin/uv"
    [ -x "$UV_CMD" ] || { log_error "uv installation failed"; exit 1; }
}

check_python() {
    if [ -n "${DEEPAGENT_PYTHON:-}" ]; then
        PYTHON_PATH="$DEEPAGENT_PYTHON"
        [ -x "$PYTHON_PATH" ] || { log_error "DEEPAGENT_PYTHON is not executable: $PYTHON_PATH"; exit 1; }
        "$PYTHON_PATH" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' || {
            log_error "DEEPAGENT_PYTHON must be Python 3.12 or newer"
            exit 1
        }
        return 0
    fi
    "$UV_CMD" python install 3.12
    PYTHON_PATH="$("$UV_CMD" python find 3.12)"
    [ -x "$PYTHON_PATH" ] || { log_error "Python 3.12 installation failed"; exit 1; }
}

json_field() {
    "$PYTHON_PATH" - "$1" "$2" <<'PY'
import json, sys
path, dotted = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    value = json.load(handle)
for part in dotted.split("."):
    value = value[part]
if isinstance(value, (dict, list)):
    raise SystemExit(f"{dotted} must be scalar")
print(value)
PY
}

validate_release_version() {
    local value="$1"
    if ! echo "$value" | grep -Eq '^[0-9A-Za-z][0-9A-Za-z._-]{0,127}$' || echo "$value" | grep -q '\.\.'; then
        log_error "Release metadata contains an unsafe version: $value"
        exit 1
    fi
}

resolve_release_manifest() {
    local manifest_url
    if [ "$VERSION" = "latest" ] || [ "$VERSION" = "latest-${CHANNEL}" ] || [ "$VERSION" = "$CHANNEL" ]; then
        local channel_file="$TMP_DIR/${CHANNEL}.json"
        local channel_schema channel_product channel_name channel_version expected_manifest_url
        curl_download "$RELEASE_BASE_URL/channels/${CHANNEL}.json" "$channel_file" "${CHANNEL} channel manifest"
        channel_schema="$(json_field "$channel_file" schema_version)"
        channel_product="$(json_field "$channel_file" product)"
        channel_name="$(json_field "$channel_file" channel)"
        channel_version="$(json_field "$channel_file" version)"
        manifest_url="$(json_field "$channel_file" manifest_url)"
        [ "$channel_schema" = "$SCHEMA_VERSION" ] || { log_error "Unsupported channel schema: $channel_schema"; exit 1; }
        [ "$channel_product" = "$PRODUCT" ] || { log_error "Channel product mismatch"; exit 1; }
        [ "$channel_name" = "$CHANNEL" ] || { log_error "Channel name mismatch"; exit 1; }
        validate_release_version "$channel_version"
        expected_manifest_url="$RELEASE_BASE_URL/manifests/${channel_version}.json"
        [ "$manifest_url" = "$expected_manifest_url" ] || {
            log_error "Channel manifest URL is outside the selected release source"
            exit 1
        }
        VERSION="$channel_version"
    else
        VERSION="${VERSION#v}"
        validate_release_version "$VERSION"
        manifest_url="$RELEASE_BASE_URL/manifests/${VERSION}.json"
    fi

    MANIFEST_FILE="$TMP_DIR/release-manifest.json"
    curl_download "$manifest_url" "$MANIFEST_FILE" "release manifest"

    local manifest_schema manifest_product manifest_channel manifest_version manifest_os manifest_arch
    manifest_schema="$(json_field "$MANIFEST_FILE" schema_version)"
    manifest_product="$(json_field "$MANIFEST_FILE" product)"
    manifest_channel="$(json_field "$MANIFEST_FILE" channel)"
    manifest_version="$(json_field "$MANIFEST_FILE" version)"
    manifest_os="$(json_field "$MANIFEST_FILE" platform.os)"
    manifest_arch="$(json_field "$MANIFEST_FILE" platform.arch)"
    [ "$manifest_schema" = "$SCHEMA_VERSION" ] || { log_error "Unsupported manifest schema: $manifest_schema"; exit 1; }
    [ "$manifest_product" = "$PRODUCT" ] || { log_error "Manifest product mismatch"; exit 1; }
    [ "$manifest_channel" = "$CHANNEL" ] || { log_error "Manifest channel mismatch"; exit 1; }
    [ "$manifest_version" = "$VERSION" ] || { log_error "Manifest version mismatch"; exit 1; }
    [ "$manifest_os" = "darwin" ] && [ "$manifest_arch" = "arm64" ] || {
        log_error "Manifest platform mismatch: ${manifest_os}-${manifest_arch}"
        exit 1
    }

    CORE_NAME="$(json_field "$MANIFEST_FILE" artifacts.core.filename)"
    CORE_URL="$(json_field "$MANIFEST_FILE" artifacts.core.url)"
    CORE_SIZE="$(json_field "$MANIFEST_FILE" artifacts.core.size)"
    CORE_SHA256="$(json_field "$MANIFEST_FILE" artifacts.core.sha256)"
    validate_release_version "$VERSION"
    case "$CORE_NAME" in
        ""|*/*|*..*) log_error "Release manifest contains an unsafe filename"; exit 1 ;;
    esac
    if ! echo "$CORE_SIZE" | grep -Eq '^[1-9][0-9]*$'; then
        log_error "Release manifest contains an invalid artifact size"
        exit 1
    fi
    case "$CORE_URL" in
        https://*) ;;
        /*) CORE_URL="${RELEASE_BASE_URL}${CORE_URL}" ;;
        *) CORE_URL="${RELEASE_BASE_URL}/${CORE_URL}" ;;
    esac
    if ! echo "$CORE_SHA256" | grep -Eq '^[0-9a-fA-F]{64}$'; then
        log_error "Release manifest contains an invalid SHA-256 digest"
        exit 1
    fi
}

verify_artifact() {
    local file="$1" expected_size="$2" expected_hash="$3"
    "$PYTHON_PATH" - "$file" "$expected_size" "$expected_hash" <<'PY'
import hashlib, pathlib, sys
path = pathlib.Path(sys.argv[1])
expected_size = int(sys.argv[2])
expected = sys.argv[3].lower()
actual_size = path.stat().st_size
if actual_size != expected_size:
    raise SystemExit(f"size mismatch: expected {expected_size}, got {actual_size}")
digest = hashlib.sha256()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
actual = digest.hexdigest()
if actual != expected:
    raise SystemExit(f"SHA-256 mismatch: expected {expected}, got {actual}")
PY
    log_success "Artifact size and SHA-256 verified"
}

validate_tarball() {
    "$PYTHON_PATH" - "$1" <<'PY'
import pathlib, sys, tarfile
archive = pathlib.Path(sys.argv[1])
with tarfile.open(archive, "r:gz") as tf:
    members = tf.getmembers()
    if not members:
        raise SystemExit("release archive is empty")
    for member in members:
        path = pathlib.PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"unsafe archive member: {member.name}")
        if member.issym() or member.islnk():
            raise SystemExit(f"archive links are not allowed: {member.name}")
PY
}

backup_legacy_install() {
    [ -f "$DEEPAGENT_HOME/VERSION" ] && [ -d "$DEEPAGENT_HOME/deepagent" ] || return 0
    local backup="$DEEPAGENT_HOME/data/legacy-backups/$(date -u +%Y%m%d-%H%M%S)"
    mkdir -p "$backup"
    local item
    for item in deepagent webui embedded .venv VERSION; do
        if [ -e "$DEEPAGENT_HOME/$item" ] || [ -L "$DEEPAGENT_HOME/$item" ]; then
            mv "$DEEPAGENT_HOME/$item" "$backup/"
        fi
    done
    log_success "Legacy code backed up to $backup"
}

prepare_data_layout() {
    mkdir -p "$DEEPAGENT_HOME"/{versions,config,data,cache,logs,runtime,skills}

    if [ -f "$DEEPAGENT_HOME/.env" ] && [ ! -L "$DEEPAGENT_HOME/.env" ]; then
        [ -e "$DEEPAGENT_HOME/config/.env" ] || mv "$DEEPAGENT_HOME/.env" "$DEEPAGENT_HOME/config/.env"
    fi
    if [ -f "$DEEPAGENT_HOME/config.yaml" ] && [ ! -L "$DEEPAGENT_HOME/config.yaml" ]; then
        [ -e "$DEEPAGENT_HOME/config/config.yaml" ] || mv "$DEEPAGENT_HOME/config.yaml" "$DEEPAGENT_HOME/config/config.yaml"
    fi
    [ -e "$DEEPAGENT_HOME/.env" ] || [ -L "$DEEPAGENT_HOME/.env" ] || ln -s "config/.env" "$DEEPAGENT_HOME/.env"
    [ -e "$DEEPAGENT_HOME/config.yaml" ] || [ -L "$DEEPAGENT_HOME/config.yaml" ] || ln -s "config/config.yaml" "$DEEPAGENT_HOME/config.yaml"
}

remove_failed_version_dir() {
    local target="$1"
    "$PYTHON_PATH" - "$target" "$DEEPAGENT_HOME/versions" <<'PY'
import pathlib, shutil, sys
target = pathlib.Path(sys.argv[1])
versions = pathlib.Path(sys.argv[2]).resolve()
if target.is_symlink() or target.resolve(strict=False).parent != versions:
    raise SystemExit(f"refusing unsafe failed-install cleanup: {target}")
if target.is_dir():
    shutil.rmtree(target)
PY
}

install_core() {
    local tarball="$TMP_DIR/$CORE_NAME"
    local extract_dir="$TMP_DIR/extract"
    local target="$DEEPAGENT_HOME/versions/$VERSION"

    curl_download "$CORE_URL" "$tarball" "$CORE_NAME"
    verify_artifact "$tarball" "$CORE_SIZE" "$CORE_SHA256"
    validate_tarball "$tarball"

    if [ -L "$target" ]; then
        log_error "Refusing symlinked immutable version directory: $target"
        exit 1
    elif [ -d "$target" ]; then
        if [ ! -f "$target/.release-sha256" ] || [ "$(tr -d '[:space:]' < "$target/.release-sha256")" != "$CORE_SHA256" ] || [ ! -x "$target/.venv/bin/deepagent" ]; then
            log_error "The immutable version directory already exists but does not match this release: $target"
            exit 1
        fi
        log_info "Reusing verified immutable version $VERSION"
    else
        mkdir -p "$extract_dir"
        tar -xzf "$tarball" -C "$extract_dir"
        [ -f "$extract_dir/pyproject.toml" ] || { log_error "Core archive does not contain pyproject.toml"; exit 1; }

        # Python virtual environments embed absolute interpreter paths and
        # cannot be moved after creation. The immutable target does not exist
        # at this point, so install there while leaving the old current link
        # untouched. A failed install removes only this new version directory.
        mv "$extract_dir" "$target"
        log_info "Installing Python dependencies in immutable version directory"
        if ! (cd "$target" && "$UV_CMD" sync --no-dev --python "$PYTHON_PATH"); then
            remove_failed_version_dir "$target"
            log_error "Dependency installation failed; the previous current version was not changed"
            exit 1
        fi
        if [ ! -x "$target/.venv/bin/deepagent" ]; then
            remove_failed_version_dir "$target"
            log_error "Installed CLI entrypoint is missing; the previous current version was not changed"
            exit 1
        fi
        if ! DEEPAGENT_HOME="$DEEPAGENT_HOME" HERMES_HOME="$DEEPAGENT_HOME" \
            "$target/.venv/bin/deepagent" version >/dev/null; then
            remove_failed_version_dir "$target"
            log_error "New version smoke test failed; the previous current version was not changed"
            exit 1
        fi
        printf '%s\n' "$CORE_SHA256" > "$target/.release-sha256"
    fi

    "$PYTHON_PATH" - "$DEEPAGENT_HOME" "$VERSION" <<'PY'
import os, pathlib, sys
home = pathlib.Path(sys.argv[1])
version = sys.argv[2]
next_link = home / "current.next"
next_link.unlink(missing_ok=True)
next_link.symlink_to(pathlib.Path("versions") / version)
os.replace(next_link, home / "current")
version_tmp = home / "VERSION.tmp"
version_tmp.write_text(version + "\n", encoding="utf-8")
os.replace(version_tmp, home / "VERSION")
PY
}

create_launcher() {
    local command_dir="$HOME/.local/bin"
    local launcher="$command_dir/deepagent"
    local temporary="$command_dir/.deepagent.tmp.$$"
    mkdir -p "$command_dir"
    cat > "$temporary" <<EOF
#!/bin/sh
# DeepAgent managed launcher
export DEEPAGENT_HOME='$DEEPAGENT_HOME'
# Internal upstream compatibility; this value is scoped to the DeepAgent process.
export HERMES_HOME="\$DEEPAGENT_HOME"
exec "\$DEEPAGENT_HOME/current/.venv/bin/deepagent" "\$@"
EOF
    chmod 0755 "$temporary"
    mv -f "$temporary" "$launcher"
}

write_install_manifest() {
    "$PYTHON_PATH" - "$DEEPAGENT_HOME" "$VERSION" "$HOME/.local/bin/deepagent" "$CHANNEL" <<'PY'
import json, os, pathlib, sys
home = pathlib.Path(sys.argv[1])
version, command, channel = sys.argv[2:]
manifest = {
    "schema_version": 1,
    "product": "deepagent",
    "platform": {"os": "darwin", "arch": "arm64"},
    "current_version": version,
    "channel": channel,
    "command_path": command,
    "code_paths": ["versions", "current", "VERSION"],
    "data_paths": ["config", "data", "cache", "logs", "runtime", "skills", ".env", "config.yaml"],
}
target = home / "install-manifest.json"
temporary = target.with_suffix(".tmp")
temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, target)
PY
}

smoke_test() {
    DEEPAGENT_HOME="$DEEPAGENT_HOME" HERMES_HOME="$DEEPAGENT_HOME" \
        "$DEEPAGENT_HOME/current/.venv/bin/deepagent" version >/dev/null
    log_success "DeepAgent CLI smoke test passed"
}

print_success() {
    echo
    echo -e "${GREEN}${BOLD}DeepAgent CLI Alpha installed${NC}"
    echo "Version: $VERSION"
    echo "Home:    $DEEPAGENT_HOME"
    echo "Command: $HOME/.local/bin/deepagent"
    if [ "$SKIP_SETUP" = false ]; then
        echo
        echo "Next: run 'deepagent setup', then 'deepagent doctor'."
    fi
}

main() {
    parse_args "$@"
    detect_platform
    validate_product_home
    classify_existing_home
    validate_existing_layout_paths
    command -v curl >/dev/null 2>&1 || { log_error "curl is required"; exit 1; }
    command -v tar >/dev/null 2>&1 || { log_error "tar is required"; exit 1; }

    TMP_DIR="$(mktemp -d)"
    trap cleanup EXIT INT TERM

    install_uv
    check_python
    resolve_release_manifest
    backup_legacy_install
    prepare_data_layout
    install_core
    create_launcher
    write_install_manifest
    smoke_test
    print_success
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    main "$@"
fi
