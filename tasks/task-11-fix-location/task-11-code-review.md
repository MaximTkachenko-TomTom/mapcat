# Task 11 — Fix Location Marker: Code Review

## Developer → Reviewer

Hi, please review the fix for the location marker alignment bug.

**Bug:** The blue triangle marker was visually offset from the actual geo-coordinate at all non-zero bearings.

**Root cause:** The triangle was rendered as a CSS border triangle on a `width:0; height:0` div. Zero-size elements have `transform-origin` at `(0,0)` by default — the triangle's tip — so `transform: rotate()` pivoted around the tip instead of the visual center. This caused the marker to drift away from the geo-point as the bearing changed.

**Fix:** Replaced the CSS border triangle with a 20×20 SVG polygon. The SVG has explicit `transform-origin: 10px 10px`, matching the `iconAnchor: [10, 10]` already set on the Leaflet `divIcon`. Both rotation and anchoring now reference the same center point, so the marker stays exactly on the geo-coordinate regardless of bearing.

**Changed file:** `mapcat/static/index.html` — one line changed in `updateCurrentPosition()`.

**Verification:** Ran `demo-location-circle.sh` (also included in this folder) which sends `update-current-position` commands tracing a full 360° circle with a red reference dot at each geo-point. After the fix, the triangle center coincides with every red dot at all bearings.

Please let me know if you have any concerns.

— Developer

---

## Reviewer → Developer

Hi, the SVG fix is correct and approved. The `transform-origin: 10px 10px` aligns perfectly with `iconAnchor: [10, 10]`, and the triangle geometry looks right at all bearings. Nice, minimal change.

One thing I noticed while reviewing — unrelated to your fix — there's a pre-existing bug in the `'clear'` WebSocket message handler (`index.html` ~line 228):

The handler only calls `clearAllFeatures()` but doesn't remove the location marker or reset `previousPosition`. The UI's clear button does handle this correctly (lines 168–171). The result: after a `clear` command arrives via stdin, the blue triangle stays on the map, and the next `update-current-position` computes bearing from the stale previous position rather than defaulting to North.

Your demo script sends `clear` at startup — running it twice without a browser refresh would expose this.

Suggested fix:
```javascript
} else if (msg.action === 'clear') {
    clearAllFeatures();
    if (currentPositionMarker) {
        map.removeLayer(currentPositionMarker);
        currentPositionMarker = null;
        previousPosition = null;
    }
```

Up to you whether to fold it into this task or track it separately. Either way, the location marker fix itself is good to go. ✅

— Reviewer
