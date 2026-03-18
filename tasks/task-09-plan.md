# Plan: Task 09 — Change Map Style to TomTom

## Problem
Mapcat uses Leaflet + OpenStreetMap tiles. The map-playground reference project uses **MapLibre GL** with a TomTom vector style. We need to migrate to MapLibre GL and add a user-triggered style-switching flow, while keeping OSM as the default (no key needed).

## Approach

Map style is a **frontend concern only** — no changes to the Python backend.

1. **Frontend migration (`index.html`)** — Replace Leaflet with MapLibre GL v5.16.0:
   - Default style: inline OSM raster source (no API key, no prompt on launch).
   - Rewrite all feature rendering using MapLibre GL GeoJSON sources + layers (one source+layer set per feature ID):
     - **point**: `circle` layer.
     - **polyline**: `line` layer + optional `circle` layers at vertices.
     - **polygon**: `fill` layer + `line` layer for border.
     - **current-position**: rotatable `maplibregl.Marker` (DOM-based chevron).
   - Preserve all behaviours: autofocus, follow-position, clear, hover highlight, tooltips, WebSocket protocol.
   - **Note:** MapLibre GL uses `[lng, lat]` (GeoJSON), but protocol sends `[lat, lng]` — flip coordinates in JS.

2. **"Change map style" UI flow (`index.html`)**:
   - Add a **"Change map style"** button to the controls panel.
   - Clicking opens an inline panel with:
     - A text input for the style URL (hint: paste a MapLibre GL style URL or TomTom Orbis URL with `<api_key>` placeholder).
     - **Apply** / **Cancel** buttons.
   - In the **existing top-right controls panel**, add a "Map style" toggle button (below Clear, separated by a divider). Clicking expands an inline sub-section within the same panel:
     ```
     ┌─────────────────────────┐
     │  Auto-focus: ON         │
     │  Follow Position: OFF   │
     │  ─────────────────────  │
     │  Clear                  │
     │  ─────────────────────  │
     │  ▼ Map style            │
     │  ┌───────────────────┐  │
     │  │ Style URL...      │  │
     │  └───────────────────┘  │
     │  [Apply]  [Cancel]      │
     │  Reset to default       │
     └─────────────────────────┘
     ```
   - If the URL contains `<api_key>`, a second input for the key appears.
   - On Apply: replace `<api_key>` with key, call `map.setStyle(resolvedUrl)`, save raw URL + key to `localStorage` (`mapcat_style_url`, `mapcat_api_key`), collapse sub-section.
   - On Cancel: collapse without changes.
   - On Reset: clear `localStorage` keys, revert map to default OSM style, collapse sub-section.
   - On page load: read `localStorage` and apply saved style automatically.

3. **README update**: add a "Map Style" section explaining the default OSM style, the style-change button, the `<api_key>` placeholder flow, and `localStorage` persistence.

## Files Changed
| File | Change |
|---|---|
| `mapcat/static/index.html` | Full rewrite: Leaflet → MapLibre GL + style-change UI |
| `README.md` | Add Map Style section |

## Notes
- TomTom Orbis style URL (from map-playground): `https://api.tomtom.com/maps/orbis/assets/styles/0.0.*/style?key=<api_key>&map=basic_street-light-driving&hillshade=hillshade_light&navigationAndRoute=navigation_and_route_light&poi=poi_light&range=range_light&apiVersion=1&renderer=premium`
- OSM fallback style: MapLibre GL inline style with raster tiles from `https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png`.
- `localStorage` is the appropriate choice for persistence — data survives browser restarts (equivalent to a config file), standard browser API.
