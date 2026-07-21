---
name: desktop-automation
description: >
  Unified desktop automation on Linux — screenshots, semantic UI inspection,
  OCR, input automation, MCP server integration. Covers both PeekabooX
  (Rust CLI/daemon/MCP) and AT-SPI Python scripts. When the user asks to
  "see the screen", "take a screenshot", "click a button on desktop",
  "automate a GUI", "control the mouse/keyboard", or "give Hermes eyes".
tags: [desktop, screenshot, automation, mcp, peekaboo, at-spi, ocr]
compatibility: Requires X11 or Wayland display. Ubuntu 22.04+ recommended.
---

# Desktop Automation Skill

Give Hermes "eyes and hands" — screenshot the desktop, inspect UI elements semantically, run OCR, and automate clicks/typing.

## Two tools, one skill

This skill covers two complementary toolsets:

### 1. PeekabooX (Rust CLI + MCP server)
**Installed at:** `/usr/bin/peekaboox` (v1.1.2)
**Best for:** Screenshots, window management, daemon mode, MCP agent integration, desktop profiles, vision fallback.

Key capabilities:
- `peekaboox capture` — full screen, region, or window screenshots
- `peekaboox see --annotate` — screenshot + semantic metadata
- `peekaboox windows` — list/manage windows
- `peekaboox elements` — semantic UI element query with vision fallback
- `peekaboox ocr` — Tesseract-backed OCR
- `peekaboox desktop profiles` — named targets per app
- `peekaboox doctor` — environment diagnostics
- MCP server for agent-facing APIs

Reference: `references/peekaboox.md`

### 2. AT-SPI Python scripts (ubuntu-desktop-control)
**Location:** `scripts/desktop.py`
**Best for:** Semantic element finding by role/name, wait-for-element with backoff, pre-click verification.

Key capabilities:
- `find-element` — AT-SPI tree search with OCR fallback
- `find-text` — OCR-only text search
- `click-element` — find + click by name/role
- `wait-for` — poll for element with exponential backoff
- `list-elements` — enumerate all interactive elements

## Environment setup

```bash
export DISPLAY=:0
export XAUTHORITY=/run/user/1000/gdm/Xauthority
```

**Pitfall:** Non-GDM shell sessions (SSH, systemd, cron) won't have these. Always export before use.

## Screen locked → black screenshots

If screenshots are all black, GNOME screen saver may be active:

```bash
# Check
gdbus call --session --dest org.gnome.ScreenSaver \
  --object-path /org/gnome/ScreenSaver \
  --method org.gnome.ScreenSaver.GetActive

# Unlock
gdbus call --session --dest org.gnome.ScreenSaver \
  --object-path /org/gnome/ScreenSaver \
  --method org.gnome.ScreenSaver.SetActive false
```

## Quick decision: which tool?

| Need | Use |
|------|-----|
| Quick screenshot | `peekaboox capture --output shot.png` |
| Screenshot + semantic info | `peekaboox see --annotate --json` |
| Find button by name | `python3 scripts/desktop.py find-element --name "OK" --role button` |
| Wait for element to appear | `python3 scripts/desktop.py wait-for --name "Success" --timeout 30` |
| OCR on image | `peekaboox ocr --image shot.png --json` |
| Click by name | `python3 scripts/desktop.py click-element --name "Submit"` |
| MCP agent integration | `peekaboox mcp.server` |
| Daemon for persistent sessions | `peekabooxd run --profile operator` |
| Desktop profile automation | `peekaboox desktop click --app telegram --target search-input` |
| Vision fallback (no AT-SPI) | `peekaboox elements --selector "role=button" --vision-fallback` |

## Browser Control Workflow

PeekabooX's `desktop focus` and `desktop click` only support built-in profiles (telegram, paint, drawing, pinta, kolourpaint, text-editor). **Browsers (Chrome, Firefox) are NOT supported by desktop profiles.**

To control browsers, combine PeekabooX input commands with xdotool for window management:

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

**Important**: xdotool `windowactivate` can fail with `BadMatch` on some window managers. If so, use `xdotool windowfocus` instead, or send key events with `--window <WID>` flag.

## Pitfalls

1. **DISPLAY not set** — Always `export DISPLAY=:0` and `export XAUTHORITY=/run/user/1000/gdm/Xauthority` in non-interactive shells.
2. **Screen locked** — Black screenshots. Use `gdbus` to check/unlock screen saver.
3. **Python MCP needs ≥3.12** — PeekabooX CLI works with Python 3.11, but the Python MCP server package requires 3.12+.
4. **xdotool can't get active window** — Usually means DISPLAY/XAUTHORITY not set correctly, or no desktop session is running.
5. **OCR slow on first run** — Tesseract initializes language data on first use. Subsequent runs are fast.
6. **AT-SPI limitations with Chrome** — Chrome's AT-SPI accessibility tree often returns empty bounds (0x0) and GetChildren/GetRoleName errors. `peekaboox elements` returns many `text` role entries with 0x0 bounds — not useful for targeting. For Chrome interaction, prefer coordinate-based `peekaboox click --x --y` over element-based targeting.
7. **OCR failures with peekaboox** — `peekaboox ocr` can fail with "scrot created an empty file". Fallback: use `peekaboox capture` + external `tesseract` directly: `tesseract image.png output -l eng+chi_sim --psm 6`. Tesseract accuracy on Chinese text from screenshots is low — consider using vision models instead.
8. **Screen capture captures everything** — `peekaboox capture` captures the entire screen (all monitors/overlays), not just the focused window. To capture a specific window region, use `peekaboox capture --region x,y,w,h` with coordinates from `peekaboox windows --json`.
9. **Vision analysis SSL timeouts** — `vision_analyze` may fail with SSL timeouts on large images — try reducing image size or using JPEG format. `peekaboox see --annotate --json` provides semantic tree but elements may have null bounds.
10. **xdotool windowactivate BadMatch** — Some window managers reject `windowactivate`. Use `xdotool windowfocus` or send key events with `--window <WID>` flag instead.
