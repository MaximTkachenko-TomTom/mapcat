# Copilot Instructions for mapcat

Date: 2025-11-13

## Project Summary
mapcat is a Python CLI that reads filtered Android logcat output (tag: Mapcat) and streams geospatial commands to a local Leaflet-based web UI for real-time visualization.

## Tech / Conventions
- Language: Python 3.11+
- Networking: asyncio + websockets (or aiohttp if HTTP needed)
- Frontend: Single static HTML (Leaflet + OSM tiles). Avoid heavy JS frameworks.
- Keep dependencies minimal.

## Command Protocol
Refer to README.md (Command Format section) for the authoritative specification. Do not duplicate the protocol here; keep a single source of truth. Update README first if the protocol changes, then adjust references here only if needed.

## Architecture Guidelines
Modules (suggested):
- parser.py: parse raw command lines into structured dicts.
- commands.py: handler functions (add_point, add_line, add_polygon, clear).
- state.py: in-memory store of features.
- server.py: websocket/HTTP serving.
- broadcast.py: batching & sending updates.

## Coding Style
- snake_case; UPPER_CASE for constants.
- Type hints & docstrings for public functions.
- Keep functions small; single responsibility.

## Error Handling
- Never crash on malformed input; log to stderr.
- Use custom exceptions internally; do not expose stack traces to clients.

## Logging
- Stderr for diagnostics.
- Do not pollute stdout (reserved for future piping if needed).

## Extensibility Targets
Plan for future commands:
- update-point id=... (lat,lng)
- remove id=...
- set-style target=... color=... opacity=...
- add-geojson file=... (or inline JSON)
Design parser to dispatch via a registry: COMMAND_HANDLERS = {"add-point": func, ...}.

## Performance (Future)
- If volume high: coalesce rapid updates (e.g., flush every 100ms).
- Consider spatial indexing only if required (not now).

## Testing
- Unit tests for parser and command handlers.
- Mock websocket layer.
- No external network calls.

## Do NOT
- Change protocol format silently (update README if changed).
- Introduce heavy deps (pandas, flask, django) without explicit request.
- Execute arbitrary code from input.

## Security
- Treat all input as untrusted.
- Validate numeric ranges for lat (-90..90) lng (-180..180).

## Asking for Clarification
If large refactor or dependency addition seems useful—prompt user first.

## GIT
- Commit message
    - Start sencence with capital letter, end with a dot.
        - GOOD: "Project has a README file."
        - BAD: "project has a README file"
    - Use short commit messages, that describe the state of the project after this commit.
        - GOOD: "Project has a README file."
        - BAD: "Add README file."

---
These instructions guide Copilot / assistants working in this repo. Modify only with user approval.
