# Plan: Add Z-Order Support

## Context

Currently all map entities (points, polylines, polygons) are drawn in the order their log messages appear. This means a polygon drawn after a polyline will visually cover it, even if the polygon should semantically be a "background" layer. The task requires a mechanism to explicitly control draw order so, e.g., "feasible road lanes" polygons always appear beneath "recommended road lanes" polylines regardless of log message order.

## Approach

Add a `zorder` parameter (integer, default `0`) to all three commands (`add-point`, `add-polyline`, `add-polygon`). In the browser, use Leaflet's **custom panes** to honor z-order: each distinct zorder value gets its own pane with `z-index = 400 + zorder`. Leaflet panes are DOM containers with explicit z-indices, so features in a lower-zorder pane are always rendered below features in a higher-zorder pane, regardless of insertion order.

## Files to Modify

### 1. `commands.py`
Add `zorder` default (cast to `int`) in all three handlers:

- `handle_add_point`: add `params.setdefault('zorder', 0)` then `params['zorder'] = int(params['zorder'])`
- `handle_add_polyline`: same
- `handle_add_polygon`: same
- Help text: document `zorder=<int>` for each command, including the safe range `-400` to `+600`

### 2. `static/index.html`
In the `addFeature()` function:

- Maintain a `panesCreated` object that caches already-created pane names.
- For each feature, read `msg.params.zorder` (default `0`).
- If a pane for that zorder doesn't exist yet, call `map.createPane('z' + zorder)` and set its `style.zIndex = 400 + zorder`.
- Pass `{ pane: 'z' + zorder }` as an option to `L.circleMarker(...)`, `L.polyline(...)`, and `L.polygon(...)`.

> Note: pass `pane` to each child layer inside the polyline layer group (line + markers), not the group itself.

### 3. `tests/test_commands.py`
Add test cases:
- Default `zorder` is `0` when not specified.
- `zorder` string is coerced to int.
- `zorder` is preserved in broadcast message params.

### 4. `README.md`
Document `zorder=<int>` alongside existing parameters for `add-point`, `add-polyline`, and `add-polygon` in the protocol spec section.

## No Changes Needed

- `parser.py` — already accepts any `key=value` pair
- `state.py` — stores all params generically
- `server.py` — broadcasts all params generically

## Example Usage

```
add-polygon (52.1,13.1);(52.2,13.2);(52.15,13.15) color=lightblue opacity=0.3 zorder=-10 label="Feasible lanes"
add-polyline (52.15,13.12);(52.18,13.18) color=green width=3 zorder=10 label="Recommended lanes"
```

The polygon (`zorder=-10`) will always render below the polyline (`zorder=10`).

## Verification

1. Run `pytest` — all existing tests pass, new zorder tests pass.
2. Start `mapcat` and send commands with different `zorder` values.
3. Confirm in the browser that lower-zorder features are visually underneath higher-zorder ones regardless of the order the commands were sent.
