---
name: nodejs-app-portable-packaging
description: Package Node.js applications into single-file executables for Windows, macOS, and Linux using pkg. Supports portable mode with data directory alongside executable.
version: 1.0.0
metadata:
  hermes:
    tags: [nodejs, pkg, portable, executable, distribution, cross-platform, usb]
---

# Node.js Application Portable Packaging

Package Node.js applications into single-file executables for distribution without requiring Node.js runtime on target machines.

## Trigger Conditions

Use when:
- User wants to distribute a Node.js app as a single executable
- Need cross-platform binaries (Windows, macOS, Linux)
- Target machines shouldn't need Node.js installed
- Creating portable USB-drive applications

## Prerequisites

- Node.js 23.0.0+ (or matching your pkg target)
- npm or yarn
- ~2GB disk space for builds

## Installation

```bash
npm install -g pkg@latest
```

Verify installation:
```bash
pkg --version
```

## Basic Usage

### Single Platform
```bash
pkg . --targets node23-linux-x64 --output myapp-linux
```

### Multiple Platforms
```bash
# Windows
pkg . --targets node23-win-x64 --output myapp-windows.exe

# Linux x64
pkg . --targets node23-linux-x64 --output myapp-linux

# Linux ARM64
pkg . --targets node23-linux-arm64 --output myapp-linux-arm64

# macOS Intel
pkg . --targets node23-macos-x64 --output myapp-macos-x64

# macOS Apple Silicon
pkg . --targets node23-macos-arm64 --output myapp-macos-arm64
```

## Portable Mode Pattern

For true portable apps (data stored alongside executable, not in user home):

### 1. Patch Server Entry

Add to the beginning of your server's entry file (e.g., `dist/server/index.js`):

```javascript
// === Portable Mode ===
const path = require('path');
const fs = require('fs');

const isPortable = process.env.MYAPP_PORTABLE === 'true' || 
                   process.argv.includes('--portable');

if (isPortable) {
  const exeDir = path.dirname(process.execPath);
  const dataDir = path.join(exeDir, 'data');
  
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  // Override environment variables to redirect data storage
  process.env.HOME = dataDir;
  process.env.USERPROFILE = dataDir;  // Windows
  process.env.MYAPP_HOME = path.join(dataDir, '.myapp');
  
  console.log('[Portable] Data directory:', dataDir);
}
// === End Portable Mode ===
```

### 2. Create Launch Scripts

**Windows (start.bat)**:
```batch
@echo off
chcp 65001 >nul
echo.
echo [Portable Mode]
echo.

set MYAPP_PORTABLE=true
set "DATA_DIR=%~dp0data"

if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

set "HOME=%DATA_DIR%"
set "USERPROFILE=%DATA_DIR%"
set "MYAPP_HOME=%DATA_DIR%\.myapp"

"%~dp0myapp-windows.exe" --portable %*
```

**macOS/Linux (start.sh)**:
```bash
#!/bin/bash
echo ""
echo "[Portable Mode]"
echo ""

export MYAPP_PORTABLE=true
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

mkdir -p "$DATA_DIR"

export HOME="$DATA_DIR"
export USERPROFILE="$DATA_DIR"
export MYAPP_HOME="$DATA_DIR/.myapp"

# Detect platform and select correct binary
OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" = "Darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        EXEC="./myapp-macos-arm64"
    else
        EXEC="./myapp-macos-x64"
    fi
else
    EXEC="./myapp-linux"
fi

cd "$SCRIPT_DIR"
"$EXEC" --portable "$@"
```

Make executable:
```bash
chmod +x start.sh
```

## Complete Build Script

Create `scripts/build-portable.js`:

```javascript
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PROJECT_DIR = path.dirname(__dirname);
const OUTPUT_DIR = path.join(PROJECT_DIR, 'portable');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function patchServerEntry(serverEntry) {
  let content = fs.readFileSync(serverEntry, 'utf8');
  
  if (content.includes('Portable Mode')) {
    console.log('⊘ Already patched');
    return;
  }
  
  const patch = `// === Portable Mode ===
const path = require('path');
const fs = require('fs');

const isPortable = process.env.MYAPP_PORTABLE === 'true' || 
                   process.argv.includes('--portable');

if (isPortable) {
  const exeDir = path.dirname(process.execPath);
  const dataDir = path.join(exeDir, 'data');
  
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  process.env.HOME = dataDir;
  process.env.USERPROFILE = dataDir;
  process.env.MYAPP_HOME = path.join(dataDir, '.myapp');
  
  console.log('[Portable] Data:', dataDir);
}
// === End Portable Mode ===

`;
  
  fs.writeFileSync(serverEntry, patch + content);
  console.log('✓ Patched for portable mode');
}

async function main() {
  console.log('Building portable packages...\n');
  
  // Build project
  console.log('🔨 Building project...');
  execSync('npm run build', { cwd: PROJECT_DIR, stdio: 'inherit' });
  
  // Patch server entry
  const serverEntry = path.join(PROJECT_DIR, 'dist', 'server', 'index.js');
  patchServerEntry(serverEntry);
  
  // Package for each platform
  ensureDir(OUTPUT_DIR);
  
  const targets = [
    { target: 'node23-win-x64', name: 'myapp-windows.exe' },
    { target: 'node23-linux-x64', name: 'myapp-linux' },
    { target: 'node23-macos-x64', name: 'myapp-macos-x64' },
    { target: 'node23-macos-arm64', name: 'myapp-macos-arm64' },
  ];
  
  for (const { target, name } of targets) {
    console.log(`\n📦 Building ${target}...`);
    try {
      execSync(
        `pkg . --targets ${target} --output ${path.join(OUTPUT_DIR, name)}`,
        { cwd: PROJECT_DIR, stdio: 'inherit' }
      );
      
      if (fs.existsSync(path.join(OUTPUT_DIR, name))) {
        console.log(`✓ ${name}`);
        if (!name.endsWith('.exe')) {
          fs.chmodSync(path.join(OUTPUT_DIR, name), 0o755);
        }
      }
    } catch (err) {
      console.error(`✗ ${name} failed`);
    }
  }
  
  console.log('\n✅ Build complete!');
  console.log(`Output: ${OUTPUT_DIR}`);
}

main().catch(console.error);
```

## pkg Configuration (package.json)

```json
{
  "name": "myapp",
  "version": "1.0.0",
  "bin": "dist/server/index.js",
  "pkg": {
    "scripts": ["dist/server/**/*.js"],
    "assets": [
      "dist/client/**/*",
      "node_modules/some-native-module/build/Release/*.node"
    ],
    "targets": ["node23"]
  }
}
```

## Native Module Considerations

Native modules (like `node-pty`, `sqlite3`, `bcrypt`) contain platform-specific binaries:

### Option 1: Build on Each Target Platform (Recommended)
Most reliable but requires access to each platform.

### Option 2: Include Prebuilds
```json
{
  "pkg": {
    "assets": [
      "node_modules/node-pty/prebuilds/**/*"
    ]
  }
}
```

### Option 3: Rebuild on Target
Ship with source and run `npm rebuild` on first launch.

## Target Platforms Reference

| Target | Description |
|--------|-------------|
| `node23-win-x64` | Windows 64-bit |
| `node23-win-arm64` | Windows ARM64 |
| `node23-linux-x64` | Linux 64-bit |
| `node23-linux-arm64` | Linux ARM64 |
| `node23-macos-x64` | macOS Intel |
| `node23-macos-arm64` | macOS Apple Silicon |

## File Size

- Single executable: ~100-200MB (includes Node.js runtime)
- This is normal - you're bundling the entire Node.js runtime

## Troubleshooting

### Build fails
- Ensure Node.js version matches pkg target
- Check available disk space (~2GB needed)
- Try: `npm rebuild` before packaging

### Native module errors on target
```bash
# Rebuild for target platform
npm rebuild <module-name>
```

### App can't find files
- Use `process.execPath` not `__dirname` in packaged app
- `process.execPath` points to the binary location

### Slow startup
- First run extracts assets to temp directory
- Subsequent runs are faster

## Security Notes

- Packaged apps can be extracted with tools like `7z`
- Don't embed sensitive credentials
- Use environment variables or config files for secrets

## References

- pkg: https://github.com/vercel/pkg
- Node.js process: https://nodejs.org/api/process.html
