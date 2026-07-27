#!/bin/bash
set -euo pipefail

PRODUCT_NAME="DeepAgent"
BUNDLE_ID="org.starseas.deepagent"
TARGET_APP="/Applications/${PRODUCT_NAME}.app"
USER_BIN="${HOME}/.local/bin"
DESKTOP_SHIM="${USER_BIN}/deepagent-desktop"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_APP=""

# The helper is shipped in two locations:
# 1. DMG root as "Install DeepAgent.command".
# 2. DeepAgent.app/Contents/Resources/build/post-install.sh.
if [[ -d "${SCRIPT_DIR}/${PRODUCT_NAME}.app" ]]; then
  SOURCE_APP="$(cd "${SCRIPT_DIR}/${PRODUCT_NAME}.app" && pwd -P)"
elif [[ -d "${SCRIPT_DIR}/../${PRODUCT_NAME}.app" ]]; then
  SOURCE_APP="$(cd "${SCRIPT_DIR}/../${PRODUCT_NAME}.app" && pwd -P)"
elif [[ "${SCRIPT_DIR}" == *"/${PRODUCT_NAME}.app/Contents/Resources/build" ]]; then
  SOURCE_APP="$(cd "${SCRIPT_DIR}/../../.." && pwd -P)"i

if [[ -z "${SOURCE_APP}" || ! -d "${SOURCE_APP}/Contents" ]]; then
  echo "Unable to locate ${PRODUCT_NAME}.app next to this installer." >&2
  exit 1
fi

INFO_PLIST="${SOURCE_APP}/Contents/Info.plist"
if [[ ! -f "${INFO_PLIST}" ]]; then
  echo "Invalid application bundle: ${INFO_PLIST} is missing." >&2
  exit 1
fi

ACTUAL_BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "${INFO_PLIST}" 2>/dev/null || true)"
if [[ "${ACTUAL_BUNDLE_ID}" != "${BUNDLE_ID}" ]]; then
  echo "Refusing to install an unexpected bundle (${ACTUAL_BUNDLE_ID:-unknown})." >&2
  exit 1
fi

run_with_required_privilege() {
  if [[ -w "/Applications" ]]; then
    "$@"
  else
    /usr/bin/sudo "$@"
  fi
}

echo "Installing ${PRODUCT_NAME} from: ${SOURCE_APP}"

if [[ "${SOURCE_APP}" != "${TARGET_APP}" ]]; then
  if [[ -e "${TARGET_APP}" ]]; then
    read -r -p "Replace the existing ${TARGET_APP}? [y/N] " answer
    case "${answer}" in
      y|Y|yes|YES) ;;
      *) echo "Installation cancelled."; exit 0 ;;
    esac
    run_with_required_privilege /bin/rm -rf -- "${TARGET_APP}"
  fi
  run_with_required_privilege /usr/bin/ditto --noqtn "${SOURCE_APP}" "${TARGET_APP}"
fi

/bin/mkdir -p "${USER_BIN}"
/bin/chmod 0755 "${USER_BIN}"
TMP_SHIM="$(/usr/bin/mktemp "${USER_BIN}/.deepagent-desktop.XXXXXX")"
cleanup() {
  /bin/rm -f -- "${TMP_SHIM}" 2>/dev/null || true
}
trap cleanup EXIT

cat > "${TMP_SHIM}" <<'SHIM'
#!/bin/sh
exec /usr/bin/open -a "DeepAgent" --args "$@"
SHIM
/bin/chmod 0755 "${TMP_SHIM}"
/bin/mv -f -- "${TMP_SHIM}" "${DESKTOP_SHIM}"
trap - EXIT

cat <<EOF

${PRODUCT_NAME} was installed at:
  ${TARGET_APP}

Desktop launcher installed at:
  ${DESKTOP_SHIM}

The existing 'deepagent' CLI command was not modified.
Because this Preview is unsigned, macOS may block the first launch.
Use Finder: Applications -> DeepAgent -> right-click -> Open.
EOF
