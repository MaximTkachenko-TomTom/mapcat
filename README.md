# mapcat

A command-line tool for visualizing geographic data from Android logcat in real-time on an interactive web map.

## Overview

`mapcat` receives geographic data piped from `adb logcat` and displays points, lines, and polygons on a live web map.

```bash
adb logcat -v raw -s Mapcat | mapcat
```

## Tech Stack

- **CLI Tool**: Python
- **Web Server**: WebSocket for real-time communication
- **Map Library**: Leaflet.js with OpenStreetMap tiles
- **Frontend**: Static HTML page served locally

## Command Format

Commands are logged to Android logcat with the `Mapcat` tag. The tool filters by tag, so no additional prefix is needed:

```bash
adb logcat -v raw -s Mapcat | mapcat
```

**Command syntax:**
```
add-point (52.424234,4.313123) color=red label="Home"
add-line (52.517867,13.377402);(52.517851,13.377303) color=blue width=3
add-polygon (52.1,13.1);(52.2,13.2);(52.3,13.1) color=green opacity=0.5
clear
```

**Format:**
- Coordinates are in parentheses: `(lat,lng)`
- Multiple coordinates separated by semicolons: `(lat1,lng1);(lat2,lng2)`
- Optional parameters use key=value syntax
- String values with spaces use quotes: `label="My Label"`

## Features

- Real-time visualization of geographic data
- Support for points, lines, and polygons
- Color-coded markers and shapes
- Auto-opens browser on start
- No API keys required

## Installation

_Coming soon_

## Usage

_Coming soon_

## Development

_Coming soon_
