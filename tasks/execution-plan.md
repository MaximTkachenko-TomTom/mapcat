# mapcat - Execution Plan

## Overview
Build a Python CLI that reads Android logcat (tag: Mapcat), parses geographic commands, and displays them in real-time on a Leaflet-based web map via WebSocket.

## Phase 1: Project Scaffold

### 1.1 Project Structure
Create directory structure:
```
mapcat/
├── mapcat/
│   ├── __init__.py
│   ├── main.py          # Entry point, argparse, orchestration
│   ├── parser.py        # Parse command strings
│   ├── commands.py      # Command handlers
│   ├── state.py         # In-memory geo feature store
│   ├── server.py        # HTTP + WebSocket server
│   └── static/
│       └── index.html   # Leaflet map UI
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   └── test_commands.py
├── requirements.txt
├── setup.py (or pyproject.toml)
└── README.md (already exists)
```

### 1.2 Dependencies
Create `requirements.txt`:
```
websockets>=11.0
```

### 1.3 Entry Point (main.py)
- Parse CLI arguments:
  - `--port` (default: 8080)
  - `--no-open` (skip auto-opening browser)
- Start HTTP + WebSocket server
- Open browser to `http://localhost:8080`
- Read stdin line-by-line in async loop

### 1.4 Static HTML (static/index.html)
- Minimal Leaflet map (based on tmp/interactive-map.html)
- WebSocket client connection
- Message handler to render features
- Keep it simple: no UI controls initially, just map rendering

### 1.5 Basic Server (server.py)
- HTTP server to serve index.html
- WebSocket endpoint for bidirectional communication
- Track connected clients
- Broadcast function to send JSON to all clients

**Milestone:** Run `echo "test" | python -m mapcat.main` → browser opens with empty map, WebSocket connects

---

## Phase 2: Core Functionality

### 2.1 Parser (parser.py)
Implement `parse_command(line: str) -> dict | None`:
- Extract command name (add-point, add-polyline, add-polygon, clear)
- Parse coordinates: `(lat,lng);(lat,lng)...`
- Parse key=value parameters (handle quoted strings)
- Return structured dict or None if invalid
- Log warnings to stderr for malformed lines

Example:
```python
parse_command('add-point (52.5,13.4) color=red label="Home"')
# Returns:
{
    'cmd': 'add-point',
    'coords': [[52.5, 13.4]],
    'params': {'color': 'red', 'label': 'Home'}
}
```

### 2.2 State Management (state.py)
Class `State`:
- Store features: `{id: {type, coords, params}}`
- Random ID generator (8-char hex if not provided by user)
- Track used IDs to prevent duplicates
- Methods:
  - `add_feature(type, coords, params, id=None) -> id`  # generate if None
  - `get_feature(id) -> dict | None`
  - `remove_feature(id) -> bool`  # returns True if removed
  - `clear_all() -> list[id]`  # returns removed IDs

### 2.3 Command Handlers (commands.py)
Registry pattern:
```python
COMMAND_HANDLERS = {
    'add-point': handle_add_point,
    'add-polyline': handle_add_polyline,
    'add-polygon': handle_add_polygon,
    'remove': handle_remove,
    'clear': handle_clear,
}

def handle_add_point(state, parsed_cmd):
    """Add point to state, return broadcast message."""
    user_id = parsed_cmd['params'].get('id')
    feature_id = state.add_feature('point', parsed_cmd['coords'], parsed_cmd['params'], id=user_id)
    return {
        'action': 'add',
        'id': feature_id,
        'type': 'point',
        'coords': parsed_cmd['coords'][0],  # Single point
        'params': parsed_cmd['params']
    }
```

Each handler:
- Validates input (coord count, lat/lng ranges)
- Updates State
- Returns JSON-serializable dict for broadcast
- Logs errors to stderr, returns None on failure

### 2.4 Main Loop Integration (main.py)
Async stdin reader:
```python
async def process_stdin(state, broadcaster):
    async for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        parsed = parser.parse_command(line)
        if not parsed:
            continue  # Already logged warning
        
        handler = COMMAND_HANDLERS.get(parsed['cmd'])
        if not handler:
            log_warning(f"Unknown command: {parsed['cmd']}")
            continue
        
        message = handler(state, parsed)
        if message:
            await broadcaster.send(message)
```

### 2.5 Broadcaster (server.py)
- Serialize message dict to JSON
- Send to all connected WebSocket clients
- Handle disconnected clients gracefully

### 2.6 Client-side Rendering (static/index.html)
WebSocket message handler:
```javascript
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    if (msg.action === 'add') {
        if (msg.type === 'point') {
            const marker = L.circleMarker(msg.coords, {
                color: msg.params.color || 'blue',
                radius: 8
            }).addTo(map);
            features[msg.id] = marker;
            
            if (msg.params.label) {
                marker.bindTooltip(msg.params.label);
            }
        }
        // Similar for line, polygon
    } else if (msg.action === 'remove') {
        const feature = features[msg.id];
        if (feature) {
            feature.remove();
            delete features[msg.id];
        }
    } else if (msg.action === 'clear') {
        Object.values(features).forEach(f => f.remove());
        features = {};
    }
};
```

**Milestone:** End-to-end flow works:
```bash
echo "add-point (52.5,13.4) color=red" | python -m mapcat.main
# → Red marker appears on map
```

---

## Phase 3: Testing & Validation

### 3.1 Unit Tests
- `test_parser.py`: Test all command formats, edge cases, malformed input
- `test_commands.py`: Test handlers with mock State
- Run with: `pytest tests/`

### 3.2 Integration Testing
Create `test_commands.txt`:
```
add-point (52.5,13.4) id=start color=red label="Start"
add-polyline (52.5,13.4);(52.6,13.5) id=route color=blue width=3
add-polygon (52.1,13.1);(52.2,13.2);(52.15,13.15) color=green opacity=0.5
remove id=start
clear
add-point (52.52,13.41) color=yellow
```

Test: `cat test_commands.txt | python -m mapcat.main`

### 3.3 Real Android Testing
```bash
# Terminal 1: Start mapcat
python -m mapcat.main

# Terminal 2: Stream logcat
adb logcat -s Mapcat | python -m mapcat.main
```

Android code example (Kotlin/Java):
```kotlin
Log.i("Mapcat", "add-point (52.527913,13.416302) color=red label=\"Current Location\"")
```

**Milestone:** All tests pass, manual testing successful with real Android device

---

## Phase 4: Polish & Extensibility

### 4.1 Enhanced Features
- Support all Leaflet styling params: width, opacity, fillColor, fillOpacity
- Validate coordinate ranges: lat ∈ [-90, 90], lng ∈ [-180, 180]
- Auto-fit map bounds when features added
- Connection status indicator in UI

### 4.2 Performance
- Batch updates: collect commands for 100ms, send single broadcast
- Throttle if > 100 features/sec
- Add feature limit (e.g., max 10k features in memory)

### 4.3 Future Commands
Extend COMMAND_HANDLERS:
- `update id=123 (52.5,13.4) color=blue` (modify existing feature)
- `set-view (52.5,13.4) zoom=15`
- `add-geojson {...}` (inline GeoJSON)

### 4.4 Documentation
Update README.md:
- Installation instructions
- Usage examples
- Command reference
- Troubleshooting

### 4.5 Packaging
Option A: Simple install script
```bash
pip install -e .
```

Option B: PyPI package (future)
```bash
pip install mapcat
```

**Milestone:** Production-ready tool, documented, extensible

---

## Phase 5: Optional Enhancements (Future)

- Save/restore session (export features to GeoJSON file)
- Multiple map layers
- Time-series playback (replay logged commands)
- Recording mode (save commands to file)
- Custom tile providers (satellite view, etc.)
- Dark mode UI
- Feature search/filter in UI

---

## Development Workflow

### Iteration Order
1. Parser (can test standalone)
2. State (can test standalone)
3. Commands (depends on State)
4. Server (static HTML + WebSocket echo)
5. Main (wire everything together)
6. Client rendering (JavaScript)
7. End-to-end testing
8. Polish

### Testing Strategy
- Write unit tests as you build each module
- Use `echo` and `cat` for quick manual tests
- Test with real Android device last

### Git Workflow
- Commit after each working module
- Use commit message style from copilot-instructions.md
- Keep commits focused and atomic

---

## Next Steps

Start with Phase 1.1 - create project structure and empty module files.
