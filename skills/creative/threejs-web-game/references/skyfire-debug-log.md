# SKYFIRE 3D Game — Session Debug Log

## Date: 2026-06-27

## Issues Found & Fixed

### 1. Black Screen (2D version)
**Root Cause**: `frameCount++` used but `let frameCount = 0` was removed by OpenCode during variable cleanup.
**Fix**: Re-add `let frameCount = 0` to variable declarations.

### 2. Object Pool Not Declared (2D version)
**Root Cause**: `bulletPool`, `particlePool`, `enemyPool` used throughout code but never instantiated as Pool objects.
**Fix**: Add pool instances AFTER all class definitions:
```javascript
const bulletPool = new Pool(() => new Bullet(), (b) => { b.alive = false; }, 50);
const particlePool = new Pool(() => new Particle(), (p) => { p.alive = false; }, 100);
const enemyPool = new Pool(() => new Enemy(), (e) => { e.alive = false; }, 20);
```

### 3. Duplicate Pool Declarations (3D version)
**Root Cause**: OpenCode auto-generated pool declarations at line 1064 AND my manual fix added them at line 971. Both existed → `Identifier 'bulletPool' has already been declared`.
**Fix**: Remove the duplicate section.

### 4. Enemies Invisible (3D version)
**Root Cause**: SPAWN_Z = -350, but Fog near=100, far=200. Camera at z=15. Fog ends at z=-185. Enemies at z=-350 are completely fogged out.
**Fix**: Change SPAWN_Z to -120, increase fog to (100, 500), camera far to 1000.

### 5. Enemies Too Slow (3D version)
**Root Cause**: Scout speed=12, SPAWN_Z=-120 → 10 seconds to reach player. Way too slow.
**Fix**: Increase speeds: Scout=30, Fighter=24, Tank=17.

### 6. Bullets Not Hitting Enemies (3D version)
**Root Cause**: Collision radius `0.3 + enemy.radius` (1.5-2.1 total) vs bullet speed 120 units/s = 2 units/frame. Tunneling possible.
**Fix**: Increase collision radius to `1.5 + enemy.radius`.

### 7. Bloom Destroying Model Details
**Root Cause**: UnrealBloomPass strength=1.2, radius=0.4, threshold=0.5. Too aggressive.
**Fix**: Reduce to strength=0.6, radius=0.3, threshold=0.7. Also increase ambient light from 0.5 to 0.8 and directional from 0.8 to 1.2.

### 8. ES Module Variables Not Accessible
**Root Cause**: `<script type="module">` scoping prevents global access from console.
**Fix**: Add `window._dbg = () => ({...})` and `window._fire = () => {...}` for debugging.

## Free 3D Model Sources Discovered
- opensource3dassets.com — 991+ CC0 GLB models, JSON database on GitHub
- sketchfab.com — CC-licensed, needs auth for download
- Three.js examples — guaranteed CDN-compatible
- itch.io — free game assets, direct download

## Key Three.js Parameters
- Bloom: strength=0.5-0.6, radius=0.3, threshold=0.7 (subtle glow, preserves detail)
- Fog: `(color, near=100, far=500)` for space games
- Camera: PerspectiveCamera(60, aspect, 0.1, 1000) for large play areas
- Lighting: AmbientLight(0x445566, 0.8) + DirectionalLight(0xffffff, 1.2) + DirectionalLight(0x8888ff, 0.5) for metallic materials
