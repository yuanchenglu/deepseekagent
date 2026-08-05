#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION")"
VERSION="${VERSION#v}"
DIST_DIR="$PROJECT_ROOT/dist/releases"
ARTIFACT="$DIST_DIR/deepagent-${VERSION}.tar.gz"
MANIFEST="$DIST_DIR/deepagent-manifest-${VERSION}.json"
TEST_ROOT="$(mktemp -d)"
HOST_UV_CACHE="${DEEPAGENT_UV_CACHE_DIR:-$HOME/.cache/uv}"

cleanup() {
    rm -rf "$TEST_ROOT"
}
trap cleanup EXIT INT TERM

[ -f "$ARTIFACT" ] || {
    echo "Build the Core artifact first: bash scripts/build-release.sh --core-only --version $VERSION" >&2
    exit 1
}
[ -f "$MANIFEST" ] || {
    echo "Release manifest is missing: $MANIFEST" >&2
    exit 1
}

RELEASE_ROOT="$TEST_ROOT/releases"
TEST_HOME="$TEST_ROOT/home"
PRODUCT_HOME="$TEST_HOME/.deepagent"
mkdir -p "$RELEASE_ROOT/manifests" "$TEST_HOME/.hermes" \
    "$TEST_HOME/.config/opencode" "$TEST_HOME/.opencode"
cp "$ARTIFACT" "$RELEASE_ROOT/"
cp "$MANIFEST" "$RELEASE_ROOT/manifests/${VERSION}.json"

printf 'hermes-protected\n' > "$TEST_HOME/.hermes/marker"
printf 'opencode-config-protected\n' > "$TEST_HOME/.config/opencode/marker"
printf 'opencode-home-protected\n' > "$TEST_HOME/.opencode/marker"

run_installer() {
    HOME="$TEST_HOME" \
    DEEPAGENT_RELEASE_BASE_URL="file://$RELEASE_ROOT" \
    DEEPAGENT_UV="${DEEPAGENT_UV:-/Users/bluth/.local/bin/uv}" \
    DEEPAGENT_PYTHON="${DEEPAGENT_PYTHON:-$PROJECT_ROOT/venv/bin/python}" \
    UV_CACHE_DIR="$HOST_UV_CACHE" \
    UV_NO_PROGRESS=1 \
    bash "$PROJECT_ROOT/scripts/install-release.sh" \
        --version "$VERSION" --dir "$PRODUCT_HOME" --skip-setup
}

assert_protected_products() {
    grep -q '^hermes-protected$' "$TEST_HOME/.hermes/marker"
    grep -q '^opencode-config-protected$' "$TEST_HOME/.config/opencode/marker"
    grep -q '^opencode-home-protected$' "$TEST_HOME/.opencode/marker"
}

run_installer
HOME="$TEST_HOME" "$TEST_HOME/.local/bin/deepagent" --version
"$PRODUCT_HOME/current/.venv/bin/python" \
    "$PRODUCT_HOME/current/scripts/audit-python-licenses.py" \
    --output "$TEST_ROOT/python-licenses.json"
test -s "$TEST_ROOT/python-licenses.json"
test "$(readlink "$PRODUCT_HOME/current")" = "versions/$VERSION"
grep -q "$(awk '{print $1}' "$ARTIFACT.sha256")" \
    "$PRODUCT_HOME/versions/$VERSION/.release-sha256"
assert_protected_products

# A covering install of the same immutable release must reuse it safely.
run_installer
HOME="$TEST_HOME" "$TEST_HOME/.local/bin/deepagent" --version
assert_protected_products

HOME="$TEST_HOME" "$TEST_HOME/.local/bin/deepagent" uninstall --keep-data --yes
test -d "$PRODUCT_HOME/config"
test -d "$PRODUCT_HOME/data"
test ! -e "$TEST_HOME/.local/bin/deepagent"
assert_protected_products

run_installer
HOME="$TEST_HOME" "$TEST_HOME/.local/bin/deepagent" uninstall --full --yes
test ! -e "$TEST_HOME/.local/bin/deepagent"
test ! -e "$PRODUCT_HOME/install-manifest.json"
assert_protected_products

echo "Release E2E passed: install, covering install, keep-data uninstall, reinstall, full uninstall, coexistence."
