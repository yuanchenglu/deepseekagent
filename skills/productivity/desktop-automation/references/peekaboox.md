# PeekabooX — Compiled Rust Desktop Automation

Alternative to the Python AT-SPI scripts. Faster, daemon-capable, MCP-integrated.

## Installation (v1.1.2)

```bash
cd /tmp
# Rust CLI/daemon
curl -sLO https://github.com/nordbyte/PeekabooX/releases/download/v1.1.2/peekaboox_1.1.2_amd64.deb
sudo apt install -y ./peekaboox_1.1.2_amd64.deb

# Python MCP server (requires Python ≥3.12)
curl -sLO https://github.com/nordbyte/PeekabooX/releases/download/v1.1.2/peekaboox-1.1.2-py3-none-any.whl
python3 -m pip install ./peekaboox-1.1.2-py3-none-any.whl
```

## Environment setup (headless shells)

```bash
export DISPLAY=:0
export XAUTHORITY=/run/user/1000/gdm/Xauthority
```

**Pitfall:** Shell sessions from SSH/systemd/non-GDM-login won't have these set. Always export before use.

For shell persistence, add to `~/.zshrc` or `~/.bashrc`:
```bash
export DISPLAY=:0
export XAUTHORITY=/run/user/1000/gdm/Xauthority
```

## Screen locked → black screenshots

If `peekaboox capture` returns a black image, GNOME screen saver may be active:

```bash
# Check
gdbus call --session --dest org.gnome.ScreenSaver \
  --object-path /org/gnome/ScreenSaver \
  --method org.gnome.ScreenSaver.GetActive
# Returns (true,) if locked

# Unlock
gdbus call --session --dest org.gnome.ScreenSaver \
  --object-path /org/gnome/ScreenSaver \
  --method org.gnome.ScreenSaver.SetActive false
```

## Core commands

```bash
# Full screen
peekaboox capture --output screenshot.png

# Region
peekaboox capture --region 0,0,400,300 --output region.png

# Specific window
peekaboox capture --window-id window-1 --output window.png

# By app name (only built-in profiles: telegram, paint, text-editor)
peekaboox capture --app calculator --title-regex Calculator --json --output calc.png

# Annotated snapshot (screenshot + semantic metadata)
peekaboox see --annotate --json

# List windows
peekaboox windows --json

# Focus a window
peekaboox window focus --app telegram

# OCR
peekaboox ocr --image screenshot.png --json

# Environment diagnostics
peekaboox doctor --json

# Semantic element query
peekaboox elements --selector "role=push button,label=Submit" --vision-fallback
```

## Browser Control Workflow

**Browsers (Chrome, Firefox) are NOT supported by PeekabooX desktop profiles.** Only telegram, paint, drawing, pinta, kolourpaint, text-editor are supported.

To control browsers, combine PeekabooX input commands with xdotool:

```bash
# 1. Find browser window ID
DISPLAY=:0 XAUTHORITY=... xdotool search --name "Google Chrome"
# Returns numeric WID like 8388612

# 2. Activate the window
DISPLAY=:0 XAUTHORITY=... xdotool windowactivate <WID>

# 3. Use peekaboox for keyboard/mouse input
DISPLAY=:0 XAUTHORITY=... peekaboox hotkey ctrl+l      # focus address bar
DISPLAY=:0 XAUTHORITY=... peekaboox type "https://..."  # type URL
DISPLAY=:0 XAUTHORITY=... peekaboox press Return        # navigate

# 4. Wait for page load, then capture
sleep 5
DISPLAY=:0 XAUTHORITY=... peekaboox capture --output /tmp/page.png
```

**xdotool `windowactivate` can fail with `BadMatch`** on some window managers. If so:
- Use `xdotool windowfocus` instead
- Or send key events with `--window <WID>` flag: `xdotool key --window <WID> ctrl+l`

## AT-SPI limitations with Chrome

- Chrome's AT-SPI accessibility tree often returns empty bounds (0x0) and GetChildren/GetRoleName errors
- `peekaboox elements` returns many `text` role entries with 0x0 bounds — not useful for targeting
- For Chrome interaction, prefer coordinate-based `peekaboox click --x --y` over element-based targeting

## OCR fallback

`peekaboox ocr` can fail with "scrot created an empty file". Use external tesseract:

```bash
# Capture first
peekaboox capture --output /tmp/screenshot.png

# Then OCR with tesseract
tesseract /tmp/screenshot.png /tmp/output -l eng+chi_sim --psm 6
cat /tmp/output.txt
```

Tesseract accuracy on Chinese text from screenshots is low — consider using vision models instead.

## MCP server

```bash
PYTHONPATH=python/src python3 -m peekaboox.mcp.server --list-tools
PYTHONPATH=python/src python3 -m peekaboox.mcp.server
PYTHONPATH=python/src python3 -m peekaboox.mcp.server --transport http --port 47778
```

## Doctor output (this machine, 2026-06-11)

- **Capture:** scrot ✅, imagemagick-import ✅, DMA-BUF ⚠️ (UnsupportedSession — normal for X11)
- **Desktop:** AT-SPI ✅, xdotool ✅, gtk-launch ✅
- **Input:** click ✅, type ✅, paste ✅, hotkey ✅
- **OCR:** tesseract ✅
- **Profiles:** telegram, paint, text-editor ✅
- **Python gRPC:** ⚠️ needs `grpcio` dependency (CLI works without it)
