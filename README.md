# mapcat

A command-line tool for visualizing geospatial data on an interactive web map. Use it as a REPL for interactive exploration or pipe commands from stdin for automated workflows.

## Usage

### REPL Mode

Start `mapcat` and type commands interactively:

```bash
mapcat
> add-point (52.5,13.4) color=red label="Home"
> add-polyline (52.5,13.4);(52.6,13.5) color=blue width=3
> add-polygon (52.1,13.1);(52.2,13.2);(52.15,13.15) color=green opacity=0.5
> update-current-position (52.52,13.41)
> remove id=my-point
> clear
> help
```

Type `help` to see all available commands and parameters.

### Piped Mode

Pipe commands from a file or another process:

```bash
# From a file
cat commands.txt | mapcat

# From echo
echo "add-point (52.5,13.4) color=red" | mapcat

# From any command
generate-commands.sh | mapcat
```

## ADB Connection

`mapcat` works with Android Debug Bridge (adb) to visualize geospatial data from Android apps in real-time.

**Setup:**
1. Log commands from your Android app using the `Mapcat` tag:
   ```kotlin
   Log.d("Mapcat", "add-point (52.5,13.4) color=blue label=\"Current Location\"");
   ```

2. Pipe adb logcat to mapcat:
   ```bash
   adb logcat -v raw -s Mapcat | mapcat
   ```

The `-v raw` displays the raw log message with no other metadata fields, `-s Mapcat` flag filters logcat output to show only messages with the `Mapcat` tag, making integration clean and efficient.

![adbmapcat](assets/adb_mapcat_1024.gif)

## Installation

```bash
# Clone the repository
git clone git@github.com:MaximTkachenko-TomTom/mapcat.git
cd mapcat

# Install in editable mode
pip install -e .
```

After installation, the `mapcat` command is available from any directory.

**Requirements:**
- Python 3.11+

## Command Reference

Run `help` in REPL mode to see detailed documentation for all commands.

**Quick reference:**

| Command | Description | Example |
|---------|-------------|---------|
| `add-point` | Add a point marker | `add-point (52.5,13.4) color=red label="Home"` |
| `add-polyline` | Add a line | `add-polyline (52.5,13.4);(52.6,13.5) color=blue width=3` |
| `add-polygon` | Add a polygon area | `add-polygon (52.1,13.1);(52.2,13.2);(52.15,13.15) color=green` |
| `update-current-position` | Update position marker | `update-current-position (52.5,13.4)` |
| `remove id=<id>` | Remove by ID | `remove id=my-point` |
| `remove tag=<tag>` | Remove by tag | `remove tag=traffic` |
| `clear` | Clear all features | `clear` |
| `help` | Show help | `help` |

**Common parameters:**
- `id=<id>` - Unique identifier (auto-generated if not provided)
- `tag=<tag>` - Group features for batch operations
- `color=<color>` - Named (`red`, `darkblue`), hex (`#FF5733`), default: `#007cff`
- `label=<text>` - Display label (use quotes for spaces: `label="My Point"`)
- `opacity=<0.0-1.0>` - Transparency level (default: `1.0`)
- `radius=<pixels>` - Point circle radius (default: `4`)
- `border=<pixels>` - Point border width (default: `2`)
- `width=<pixels>` - Line width for polylines (default: `2`)
- `markers=<pixels>` - Circle radius at polyline points (`0`=off, default: `0`)

## Features

- Real-time visualization of geographic data
- Interactive web map with Leaflet.js and OpenStreetMap
- Support for points, polylines, and polygons
- Customizable colors, opacity, and styling
- REPL and piped modes
- Position tracking with directional chevron
- Tag-based feature grouping
- Auto-focus and follow position controls
- No API keys required

## Tech Stack

- **CLI Tool**: Python 3.11+
- **Web Server**: HTTP + WebSocket
- **Map Library**: Leaflet.js with OpenStreetMap tiles
- **Frontend**: Static HTML page served locally
