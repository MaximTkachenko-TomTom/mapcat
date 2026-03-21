# Task 11 Plan: Styles in Settings

## Problem
The settings panel has OSM Default and Driving light as style options, but:
- Driving light has no URL (`null` placeholder)
- Custom styles only store a single URL, no naming, no list persistence in UI
- No API key auto-prompt when a TomTom style is selected without a saved key
- Active style indicator is incomplete (doesn't highlight predefined/custom styles correctly)

## Approach
Refactor the styles section of `mapcat/static/index.html` (JS + minimal HTML).

### Storage Schema (replace `mapcat_style_url`)
| Key | Value |
|-----|-------|
| `mapcat_active_style` | `"default"` \| `"driving-light"` \| `"custom:0"` \| `"custom:1"` \| … |
| `mapcat_custom_styles` | JSON array of `{ id: number, url: string }` — `id` is a stable auto-increment, display name "Custom N" is derived from list position |
| `mapcat_api_key` | unchanged |

### Changes
1. **Hardcode Driving light URL** in `PREDEFINED_STYLES['driving-light']`.
2. **Migrate** `resolveInitialStyle()` to use new storage schema.
3. **`loadCustomStyles()`** — on page load, read `mapcat_custom_styles` and inject `<li data-style="custom:{id}">` items into `#styleList` with `title=URL` for hover tooltip and display names ("Custom 1", "Custom 2", … by position).
4. **`updateActiveStyle()`** — read `mapcat_active_style`, find matching `<li>` by `data-style`, mark it `.active`.
5. **Predefined style click handler** — for styles that need an API key (`<api_key>` in URL) and none is saved: show API key form, defer applying style until key saved; cancel → stay on current style.
6. **Custom style apply handler** — generate next stable `id` (max existing id + 1), append `{ id, url }` to array, add `<li data-style="custom:{id}">` to DOM, set `mapcat_active_style = "custom:{id}"`, apply style (with same API key prompt logic if needed).
7. **API key save handler** — after saving key, also handle the "pending style" case (deferred style from step 5).

## Notes
- "1st time" = no `mapcat_api_key` in localStorage (global, not per-style).
- Custom style display names are derived from list position ("Custom 1" = first in list, etc.); `id` is stable so renaming later won't break active style tracking.
- Custom styles cannot be deleted.
- `0.0.*` in TomTom URL is literal, use as-is.
- Hover tooltip = HTML `title` attribute on `<li>`.
