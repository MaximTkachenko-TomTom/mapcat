# Code Review: Task-10 Z-Order Support

## Developer → Reviewer

Hi,

The implementation for task-10 (Z-order support) is ready for review on branch `feature/z-order`.

**What was changed:**
- `mapcat/commands.py` — Added `zorder` parameter (int, default `0`) to `add-point`, `add-polyline`, and `add-polygon` handlers. Documented it in help text with the safe range (`-400` to `+600`).
- `mapcat/static/index.html` — Added `getOrCreatePane(zorder)` helper that lazily creates a Leaflet pane with `z-index = 400 + zorder`. The `pane` option is passed to each layer constructor (`L.circleMarker`, `L.polyline`, `L.polygon`), including per-point markers inside polyline groups.
- `tests/test_commands.py` — Updated existing params assertion + added 3 new tests covering default value, int coercion, and param propagation.
- `README.md` — Documented `zorder` in the common parameters reference.

**Things worth double-checking:**
- Leaflet pane behavior when `zorder` values are reused across features of different types (e.g. a point and a polygon sharing `zorder=10` — they'll share a pane, which should be fine).
- The `zorder || 0` fallback in `getOrCreatePane` — if `zorder` is `0` the expression is falsy, but `0 || 0` is still `0` so it works correctly.

All 86 tests pass.

Thanks

---

## Reviewer → Developer

Reviewed the diff on `feature/z-order`. **LGTM — approved.**

### ✅ Looks Good

- `commands.py`: zorder defaulting and int coercion is correct in all three handlers. Help text includes safe range.
- `index.html`: `getOrCreatePane` is clean. Pane option correctly passed to all child layers including per-point markers inside polyline groups — good.
- `tests/test_commands.py`: All three cases covered (default, coercion, propagation). Existing assertion updated correctly.
- `README.md`: Documented in the right place (common parameters section).

### 🔍 One Minor Note

`params.zorder || 0` in `getOrCreatePane`: as you flagged, `0 || 0` is `0` so it works. But since `commands.py` always sets `zorder` before broadcasting, this fallback is never actually hit. Consider `params.zorder ?? 0` (nullish coalescing) to be more explicit about intent — it's cleaner and avoids any future confusion if someone passes a falsy-but-valid value. Non-blocking; take it or leave it.

### Summary

All plan items implemented. Both issues from the plan review addressed. Tests pass. Ready to merge.

---

## Reviewer → Developer (Test Coverage Follow-up)

The three new tests cover the happy-path well, but there's a gap worth fixing before merge.

**Issue: invalid `zorder` crashes instead of failing gracefully.**

`int(params['zorder'])` sits outside the `try/except` block in all three handlers. Passing `zorder=abc` raises an unhandled `ValueError` — violating the project rule *"never crash on malformed input."*

A test that should exist (and would currently fail):

```python
def test_zorder_invalid_value_does_not_crash():
    state = State()
    parsed = {'cmd': 'add-point', 'coords': [[52.5, 13.4]], 'params': {'zorder': 'bad'}}
    result = handle_add_point(state, parsed)
    assert result is None  # should fail gracefully, not raise
```

Note: the same bug exists for `radius`, `border`, `width`, etc. — it's pre-existing and not introduced by this PR. Up to you whether to fix it only for `zorder` or for all params at once. Either way, the test should be added.

This is the only thing blocking a clean merge.

---

## Developer → Reviewer (Follow-up)

Both issues addressed in a second commit on `feature/z-order`:

- **Invalid zorder crash (blocking)**: Wrapped `int(params['zorder'])` in a `try/except (ValueError, TypeError)` in all three handlers. Invalid values now log an error to stderr and return `None`, consistent with how other errors are handled. Added `test_zorder_invalid_value_does_not_crash` covering all three commands.
- **`||` → `??` (non-blocking)**: Switched to nullish coalescing in `getOrCreatePane` — cleaner and correct.

87 tests pass. Ready for re-review.

---

## Reviewer → Developer (Re-review)

Both fixes verified. **Approved — ready to merge.**

- Error handling: `try/except (ValueError, TypeError)` in all three handlers, logs to stderr, returns `None`. Correct and consistent with project conventions.
- Test covers all three commands in one loop — clean.
- `??` in `getOrCreatePane` — good.
