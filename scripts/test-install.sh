#!/usr/bin/env bash
# Offline contract tests for the DeepAgent CLI Alpha installer.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install-release.sh"
TEST_ROOT="$(mktemp -d)"
PASS=0
FAIL=0

cleanup_test() { rm -rf "$TEST_ROOT"; }
trap cleanup_test EXIT INT TERM

pass() { PASS=$((PASS + 1)); printf '✓ %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '✗ %s\n' "$1" >&2; }

assert_success() {
    local name="$1"
    shift
    if "$@"; then pass "$name"; else fail "$name"; fi
}

assert_failure() {
    local name="$1"
    shift
    if "$@"; then fail "$name"; else pass "$name"; fi
}

test_syntax() {
    assert_success "installer has valid Bash syntax" bash -n "$INSTALL_SCRIPT"
    assert_success "installer is executable" test -x "$INSTALL_SCRIPT"
}

test_function_contract() {
    local function_name
    for function_name in \
        parse_args detect_platform validate_product_home classify_existing_home \
        resolve_release_manifest verify_artifact validate_tarball validate_existing_layout_paths prepare_data_layout \
        install_core create_launcher write_install_manifest smoke_test; do
        if grep -Eq "^${function_name}\(\)" "$INSTALL_SCRIPT"; then
            pass "function exists: $function_name"
        else
            fail "function missing: $function_name"
        fi
    done
}

test_arguments() {
    local output
    output="$(bash "$INSTALL_SCRIPT" --help 2>&1)"
    if echo "$output" | grep -q "macOS Apple Silicon"; then
        pass "help documents the supported platform"
    else
        fail "help omits the supported platform"
    fi

    output="$(bash -c "source '$INSTALL_SCRIPT'; parse_args --version v0.9.0-alpha.2 --dir '$TEST_ROOT/product' --skip-setup; printf '%s|%s|%s' \"\$VERSION\" \"\$DEEPAGENT_HOME\" \"\$SKIP_SETUP\"")"
    if [ "$output" = "0.9.0-alpha.2|$TEST_ROOT/product|true" ]; then
        pass "arguments are parsed without running the installer"
    else
        fail "argument parsing returned: $output"
    fi
    assert_failure "unknown arguments fail closed" bash "$INSTALL_SCRIPT" --not-a-real-option
}

test_platform_gate() {
    assert_success "Darwin arm64 is accepted" bash -c "source '$INSTALL_SCRIPT'; uname(){ if [ \"\$1\" = -s ]; then echo Darwin; else echo arm64; fi; }; detect_platform"
    assert_failure "Linux is rejected" bash -c "source '$INSTALL_SCRIPT'; uname(){ if [ \"\$1\" = -s ]; then echo Linux; else echo arm64; fi; }; detect_platform"
    assert_failure "Intel macOS is rejected" bash -c "source '$INSTALL_SCRIPT'; uname(){ if [ \"\$1\" = -s ]; then echo Darwin; else echo x86_64; fi; }; detect_platform"
}

test_home_guard() {
    mkdir -p "$TEST_ROOT/home/.hermes" "$TEST_ROOT/home/.config/opencode" "$TEST_ROOT/home/.deepagent"
    assert_success "default DeepAgent path is accepted" bash -c "source '$INSTALL_SCRIPT'; HOME='$TEST_ROOT/home'; DEEPAGENT_HOME='$TEST_ROOT/home/.deepagent'; validate_product_home"
    assert_failure "Hermes path is rejected" bash -c "source '$INSTALL_SCRIPT'; HOME='$TEST_ROOT/home'; DEEPAGENT_HOME='$TEST_ROOT/home/.hermes'; validate_product_home"
    assert_failure "OpenCode path is rejected" bash -c "source '$INSTALL_SCRIPT'; HOME='$TEST_ROOT/home'; DEEPAGENT_HOME='$TEST_ROOT/home/.config/opencode'; validate_product_home"
    assert_failure "filesystem root is rejected" bash -c "source '$INSTALL_SCRIPT'; DEEPAGENT_HOME='/'; validate_product_home"
}

test_checksum_and_archive() {
    local payload="$TEST_ROOT/payload.txt"
    local digest
    printf 'deepagent-alpha\n' > "$payload"
    digest="$(shasum -a 256 "$payload" | awk '{print $1}')"
    local size
    size="$(wc -c < "$payload" | tr -d '[:space:]')"
    assert_success "correct size and SHA-256 are accepted" bash -c "source '$INSTALL_SCRIPT'; PYTHON_PATH='$(command -v python3)'; verify_artifact '$payload' '$size' '$digest'"
    assert_failure "incorrect SHA-256 is rejected" bash -c "source '$INSTALL_SCRIPT'; PYTHON_PATH='$(command -v python3)'; verify_artifact '$payload' '$size' '0000000000000000000000000000000000000000000000000000000000000000'"
    assert_failure "incorrect artifact size is rejected" bash -c "source '$INSTALL_SCRIPT'; PYTHON_PATH='$(command -v python3)'; verify_artifact '$payload' '1' '$digest'"

    mkdir -p "$TEST_ROOT/archive"
    printf '[project]\nname="fixture"\n' > "$TEST_ROOT/archive/pyproject.toml"
    tar -czf "$TEST_ROOT/safe.tar.gz" -C "$TEST_ROOT/archive" pyproject.toml
    assert_success "safe archive members are accepted" bash -c "source '$INSTALL_SCRIPT'; PYTHON_PATH='$(command -v python3)'; validate_tarball '$TEST_ROOT/safe.tar.gz'"
}

test_launcher_and_manifest() {
    local fake_home="$TEST_ROOT/home"
    local product="$fake_home/.deepagent"
    mkdir -p "$product/versions/0.9.0-alpha.1/.venv/bin" "$fake_home/.local/bin"
    assert_success "managed launcher and manifest are generated" bash -c "source '$INSTALL_SCRIPT'; HOME='$fake_home'; DEEPAGENT_HOME='$product'; VERSION='0.9.0-alpha.1'; PYTHON_PATH='$(command -v python3)'; create_launcher; write_install_manifest"
    if grep -q "# DeepAgent managed launcher" "$fake_home/.local/bin/deepagent" && \
       grep -q "export DEEPAGENT_HOME='$product'" "$fake_home/.local/bin/deepagent" && \
       grep -q '"product": "deepagent"' "$product/install-manifest.json"; then
        pass "launcher is isolated and manifest declares ownership"
    else
        fail "launcher or manifest contract is incomplete"
    fi
}

test_layout_isolation() {
    local product="$TEST_ROOT/layout-home"
    mkdir -p "$product"
    assert_success "data layout can be prepared twice" bash -c "source '$INSTALL_SCRIPT'; DEEPAGENT_HOME='$product'; prepare_data_layout; prepare_data_layout"

    local external="$TEST_ROOT/external-hermes"
    local linked="$TEST_ROOT/linked-home"
    mkdir -p "$external" "$linked"
    ln -s "$external" "$linked/config"
    assert_failure "external config directory symlink is rejected" bash -c "source '$INSTALL_SCRIPT'; DEEPAGENT_HOME='$linked'; validate_existing_layout_paths"

    local compat="$TEST_ROOT/compat-home"
    mkdir -p "$compat"
    ln -s "$external/credentials" "$compat/.env"
    assert_failure "external credential symlink is rejected" bash -c "source '$INSTALL_SCRIPT'; DEEPAGENT_HOME='$compat'; validate_existing_layout_paths"
}

main() {
    test_syntax
    test_function_contract
    test_arguments
    test_platform_gate
    test_home_guard
    test_checksum_and_archive
    test_launcher_and_manifest
    test_layout_isolation
    printf '\nPassed: %s  Failed: %s\n' "$PASS" "$FAIL"
    [ "$FAIL" -eq 0 ]
}

main "$@"
