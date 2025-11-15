# Task 06: Split Components - Execution Plan

## Goal
Separate mapcat into independent web page server and Python WebSocket client.

## Architecture Changes

### Current (Before)
```
mapcat Python program
├── HTTP server (serves HTML on port 8080)
├── WebSocket server (port 8081)
└── Browser connects to both
```

### New (After)
```
Web Page Server (always running)
├── HTTP server (serves HTML)
├── WebSocket SERVER (listens on port 4444)
└── Accepts connections from mapcat clients

mapcat Python program
└── WebSocket CLIENT (connects to port 4444)
```

## Decisions

1. **WebSocket Port**: Fixed at **4444** (not configurable)

2. **Multiple mapcat clients**: 
   - Multiple Python clients can connect simultaneously
   - Data is **merged** - all features from all clients shown together
   - No separation per client (no layers, no different colors)

3. **Persistence**: 
   - When all mapcat clients disconnect, **keep all features displayed**
   - Map state persists until explicitly cleared (via Clear button)

4. **Connection Indicator**:
   - **Location**: In control panel, **above** all buttons
   - **Visual**: Circle indicator
     - **Green**: At least one mapcat client connected
     - **Red**: No mapcat clients connected

## Implementation Steps

### Phase 1: Web Page Updates

#### 1.1 Add WebSocket Server to HTML
- Remove WebSocket client code
- Add WebSocket server (listening on port 4444)
- Track connected clients
- Handle client connections/disconnections
- Broadcast to all clients when features change

#### 1.2 Add Connection Indicator
- Add visual indicator to control panel (above buttons)
- CSS styling for green/red circle
- Update indicator state on client connect/disconnect
- Show count of connected clients (optional)

#### 1.3 Remove Auto-open Browser
- Web page is now standalone
- User opens it manually in browser

### Phase 2: Python Client Updates

#### 2.1 Remove Server Code
- Remove HTTP server (StaticHandler, start_http_server)
- Remove WebSocket server code
- Remove browser auto-open (webbrowser.open)

#### 2.2 Add WebSocket Client
- Connect to ws://localhost:4444
- Send JSON messages for all commands
- Handle connection errors gracefully
- Auto-reconnect on disconnect (optional)

#### 2.3 Update Main Loop
- Remove server initialization
- Initialize WebSocket client connection
- Send commands as WebSocket messages
- Handle disconnection gracefully

#### 2.4 Update CLI Arguments
- Remove --port argument (no longer needed)
- Remove --no-open argument (no longer needed)
- Keep simple invocation: `python -m mapcat.main`

### Phase 3: Documentation Updates

#### 3.1 Update README
- Document new architecture
- Explain how to start web page server
- Explain how to start mapcat client
- Update usage examples

#### 3.2 Update Instructions
- Two-step startup process:
  1. Start web page server
  2. Start mapcat client(s)

## Technical Details

### WebSocket Message Protocol
No changes to message format:
```json
{"action": "add", "id": "...", "type": "point", "coords": [...], "params": {...}}
{"action": "remove", "id": "..."}
{"action": "remove-by-tag", "tag": "...", "ids": [...]}
{"action": "clear", "ids": [...]}
{"action": "update-current-position", "coords": [...]}
```

### Web Page Server Technology
**TO BE DECIDED** - Options:
- Simple static HTML with embedded WebSocket server (via JavaScript library)
- Node.js simple HTTP + WebSocket server
- Python simple HTTP server script
- Other?

## Testing Plan

1. Start web page server
2. Open in browser - see red indicator
3. Start mapcat client - indicator turns green
4. Add features - appear on map
5. Start second mapcat client - both work, data merged
6. Stop one client - features remain, indicator stays green
7. Stop all clients - features remain, indicator turns red
8. Restart client - reconnects, can add more features

## Notes

- Web page server runs independently, can stay open 24/7
- Multiple mapcat instances can connect/disconnect freely
- Map state persists across client connections
- Only way to clear map is via Clear button or clear command
