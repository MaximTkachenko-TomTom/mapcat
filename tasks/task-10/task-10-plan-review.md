# Plan Review: Task-10 Z-Order Support

Overall the plan looks solid — good approach, right tool (Leaflet panes), and the scope is well-defined.

## ✅ Looks Good

- Leaflet panes is the correct mechanism: clean, reliable, no rendering hacks.
- Defaulting `zorder` to `0` and coercing to `int` is sensible.
- Correctly identifies that `parser.py`, `state.py`, and `server.py` need no changes.
- The note about passing `pane` to child layers (line + markers) rather than the layer group is an important detail — good catch.

## ⚠️ Potential Issue: Negative Z-Order

The formula `z-index = 400 + zorder` can produce a negative or very low z-index if `zorder < -400`. Leaflet's built-in panes sit in the 200–600 range, so extreme negative values could interfere with base layers or tile rendering.

Consider either:
- Documenting the practical safe range (e.g., `-400` to `+600`), or
- Clamping/validating the value in `commands.py`.

## 📝 Missing: README Update

The plan doesn't mention updating `README.md`. Since README is the authoritative protocol spec (per project conventions), `zorder=<int>` should be documented there alongside the other parameters for each command.

## Summary

No objections to the implementation strategy. Address the two points above before or during implementation.

---

## Response

Both points addressed in the updated plan (`task-10-z-order-plan.md`):

- **Negative z-order**: No clamping added — instead the safe range (`-400` to `+600`) will be documented in help text and README. Clamping feels like unnecessary guard-railing for an internal debug tool; documenting the range is enough.
- **README update**: Added as a required change in the plan (new section 4).
