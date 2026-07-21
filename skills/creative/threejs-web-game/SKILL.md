---
name: threejs-web-game
description: "Build and deploy browser-based 3D games using Three.js. Covers architecture, common pitfalls, visual debugging, and Cloudflare Worker deployment. Use when creating web games, interactive 3D demos, or browser-based simulations with Three.js."
tags: [threejs, web-game, 3d, canvas, browser-game, cloudflare]
---

# Three.js Web Game Development

## Architecture

### Single-File Game Pattern
- All CSS + JS inlined in one `index.html`
- Three.js loaded via importmap from CDN (jsdelivr/unpkg)
- Post-processing: EffectComposer + RenderPass + UnrealBloomPass
- ES module scope (`<script type="module">`) — variables NOT accessible from browser console

### Project Structure
```
project/
├── index.html          # Complete game (CSS + JS inline)
├── docs/
│   └── design.md       # Game design document
└── .gitignore
```

## Critical Pitfalls (Lessons Learned)

### 1. ES Module Scope Debugging
Variables in `<script type="module">` are NOT globally accessible from browser console.
**Fix**: Add debug exposure at module top:
```javascript
setTimeout(() => {
  window._dbg = () => ({ gameState, enemies: enemies.length, score: playerScore });
  window._fire = () => { mouseDown = true; };
}, 100);
```

### 2. Bloom Post-Processing Too Strong
Bloom strength > 0.8 destroys model details, making everything look like glowing blocks.
**Fix**: Use `UnrealBloomPass(size, 0.5, 0.3, 0.7)` — strength=0.5, radius=0.3, threshold=0.7

### 3. Fog Range vs Spawn Distance
Enemies spawned beyond fog range are invisible. Fog distance is from camera, not origin.
**Example**: Camera at z=15, fog near=100 → objects beyond z=-85 are partially fogged.
**Fix**: Ensure SPAWN_Z < camera.z + fog.near. Or increase fog range: `Fog(color, 100, 500)`

### 4. Object Pool Declaration Order
OpenCode may declare pool instances before the classes they reference. Classes in JS are NOT hoisted like functions.
**Fix**: Always place Pool instances AFTER all class definitions.

### 5. Collision Tunneling in 3D
Fast bullets (120+ units/s) can skip past enemies in one frame (2 units/frame at 60fps).
**Fix**: Increase collision radius: `if (dist < 1.5 + enemy.radius)` instead of `0.3 + enemy.radius`

### 6. Input Event Dispatch
Synthetic `mousedown` on canvas triggers `handlePointerDown()` which may start game WITHOUT setting `mouseDown=true` (returns early from MENU state). Need second click to start firing.

## Testing Workflow

### Visual Testing Requirements
1. **ALWAYS switch to vision-capable model** (MIMO V2.5) before testing visual output
2. Start local HTTP server: `python3 -m http.server PORT`
3. Navigate browser to localhost
4. Use `browser_vision` to inspect visual output
5. Use `browser_console` to check game state via debug functions

### Console Debugging Pattern
```javascript
// Check game state
window._dbg()
// Force actions
window._fire()
// Check for errors
browser_console(clear=true)
```

### Screenshot Documentation
Save screenshots to user's ~/Downloads/ for review:
```bash
cp /path/to/screenshot.png ~/Downloads/project-name-state.png
```

## 3D Model Sources (Free)

When code-generated geometry isn't sufficient:
- **Sketchfab** (sketchfab.com) — CC-licensed, needs auth for download
- **Open Source 3D Assets** (opensource3dassets.com) — 991+ CC0 GLB models
- **itch.io** — Free game assets, direct download
- **Three.js examples** — Guaranteed to work with Three.js

### Download Pattern
```bash
curl -sL --max-time 15 "URL" -o models/model.glb
```

## Cloudflare Worker Deployment

See `cloudflare-static-hosting` skill for full deployment guide.
Key: Use Worker embedded page pattern for single-file games.

## Code Generation with OpenCode

### Prompt Template
```
READ docs/design.md for full spec.

TASK: Create index.html - a complete [game type] using Three.js.

CRITICAL: Declare ALL variables before use. OpenCode has a history of:
- Using pool instances that were never declared
- Removing variable declarations during cleanup
- Using variables from inner scopes

Requirements:
1. Three.js via importmap CDN
2. Post-processing with Bloom
3. Procedural 3D models (or loaded from /models/)
4. Game systems: [list specific systems]
5. HTML overlay UI
6. Mouse/touch/keyboard controls

Verify: balanced braces, no undeclared variables, all pools declared.
```

### Post-Generation Validation
```bash
# Check syntax
node --check /tmp/_check_syntax.mjs
# Check brace balance
grep -c '{' file && grep -c '}' file
# Check pool declarations
grep -n "Pool\|pool" file
```
