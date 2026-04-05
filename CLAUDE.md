# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mapcat` is a Python CLI that reads geospatial commands (from REPL, stdin, or piped `adb logcat` output) and streams them via WebSocket to a browser-based Leaflet map for real-time visualization.

## Commands

```bash
# Install (use a virtualenv)
pip install -e .

# Run
mapcat                        # REPL mode
cat commands.txt | mapcat     # Piped mode
adb logcat -v raw -s Mapcat | mapcat  # From Android device

# Options
mapcat --port 9090            # Custom port (WebSocket = port+1)
mapcat --no-open              # Don't auto-open browser
mapcat --verbose              # Print OK messages

# Tests
pytest                        # Run all tests
pytest tests/test_parser.py   # Run single test file
```

## Architecture

```
main.py      → entry point; CLI args; async stdin loop; dispatches to parser & commands
parser.py    → tokenizes raw command strings into structured dicts
commands.py  → COMMAND_HANDLERS registry; validates args; applies defaults; returns broadcast messages
state.py     → in-memory feature store; auto-generates IDs; supports removal by ID or tag
server.py    → ThreadingHTTPServer (port 8080) serves static HTML; WebSocket server (port+1) broadcasts updates; syncs new clients with current state
chunker.py   → reassembles long commands split across multiple log lines (chunked protocol)
static/index.html → single-page Leaflet map; WebSocket client; renders points/polylines/polygons
```

**Data flow:** stdin → `parser.parse_command()` → `COMMAND_HANDLERS[cmd](state, parsed)` → `state` mutation → `server.broadcast(JSON)` → browser Leaflet render.

The HTTP and WebSocket servers run as background threads; the main async loop handles stdin.

## Key Conventions

- **Protocol spec lives in README.md** — update README first if the command format changes.
- **No heavy deps** — only `websockets` is an external dependency. Don't add pandas, flask, django, etc. without explicit user approval.
- **Never crash on malformed input** — log errors to stderr, continue processing.
- **stdout is reserved** — use stderr for diagnostics.
- **Chunked protocol** for long commands (e.g., polylines exceeding Android `Log.d` ~4000 char limit):
  ```
  begin id=abc123
  abc123 add-polyline (52.5,13.4);... seq=1
  abc123 ...continued seq=2
  commit id=abc123 total=2
  ```
- **Chunker limits**: `MAX_SESSIONS=100`, `MAX_TOTAL_CHUNKS=1000`.
- **Coordinate validation**: lat ∈ [-90, 90], lng ∈ [-180, 180].

## Coding Style

- `snake_case` for identifiers; `UPPER_CASE` for constants.
- Type hints and docstrings on public functions.
- Keep functions small with single responsibility.
- Extend commands via the `COMMAND_HANDLERS` dict in `commands.py`.

## Git Commit Messages

- Start with a capital letter, end with a period.
- Describe project state after the commit, not what was done.
- **Good:** `"Parser supports quoted labels."` **Bad:** `"Add quoted label support"`
