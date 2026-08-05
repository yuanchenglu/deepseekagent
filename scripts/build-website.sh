#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEBSITE_DIR="$PROJECT_ROOT/website"
LANDING_DIR="$PROJECT_ROOT/landingpage"
DOCS_BUILD_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$DOCS_BUILD_DIR"
}
trap cleanup EXIT INT TERM

cd "$WEBSITE_DIR"
npm ci --ignore-scripts
npm run typecheck
npm run test:functions
npm run build -- --out-dir "$DOCS_BUILD_DIR"

rm -rf "$WEBSITE_DIR/build"
mkdir -p "$WEBSITE_DIR/build/docs"
cp -R "$LANDING_DIR"/. "$WEBSITE_DIR/build/"
cp -R "$DOCS_BUILD_DIR"/. "$WEBSITE_DIR/build/docs/"
cp "$PROJECT_ROOT/scripts/install-release.sh" "$WEBSITE_DIR/build/install-release.sh"

test -s "$WEBSITE_DIR/build/install-release.sh"
test -s "$WEBSITE_DIR/build/index.html"
test -s "$WEBSITE_DIR/build/docs/index.html"
bash -n "$WEBSITE_DIR/build/install-release.sh"
echo "Website build contains the landing page, strict Alpha docs, and canonical installer."
