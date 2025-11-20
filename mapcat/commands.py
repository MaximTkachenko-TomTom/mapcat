"""
Command handlers for geospatial features.
"""
import sys
from typing import Optional, Dict, Any
from mapcat.state import State

# ANSI color codes
RED = '\033[91m'
RESET = '\033[0m'


def handle_add_point(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle add-point command.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict with 'cmd', 'coords', 'params'
    
    Returns:
        Broadcast message dict or None on error
    """
    # Validate: exactly 1 coordinate required
    if len(parsed_cmd['coords']) != 1:
        _log_error("add-point", f"add-point requires exactly 1 coordinate, got {len(parsed_cmd['coords'])}", parsed_cmd)
        return None
    
    user_id = parsed_cmd['params'].get('id')
    
    # Apply defaults for parameters
    params = parsed_cmd['params'].copy()
    if 'color' not in params:
        params['color'] = '#007cff'
    if 'opacity' not in params:
        params['opacity'] = 1.0
    else:
        params['opacity'] = float(params['opacity'])
    if 'radius' not in params:
        params['radius'] = 4
    else:
        params['radius'] = int(params['radius'])
    if 'border' not in params:
        params['border'] = 2
    else:
        params['border'] = int(params['border'])
    
    try:
        feature_id = state.add_feature('point', parsed_cmd['coords'], params, feature_id=user_id)
        return {
            'action': 'add',
            'id': feature_id,
            'type': 'point',
            'coords': parsed_cmd['coords'][0],  # Single point [lat, lng]
            'params': params
        }
    except ValueError as e:
        _log_error("add-point", str(e), parsed_cmd)
        return None


def handle_add_polyline(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle add-polyline command.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict
    
    Returns:
        Broadcast message dict or None on error
    """
    # Validate: at least 2 coordinates required
    if len(parsed_cmd['coords']) < 2:
        _log_error("add-polyline", f"add-polyline requires at least 2 coordinates, got {len(parsed_cmd['coords'])}", parsed_cmd)
        return None
    
    user_id = parsed_cmd['params'].get('id')
    
    # Apply defaults for parameters
    params = parsed_cmd['params'].copy()
    if 'color' not in params:
        params['color'] = '#007cff'
    if 'opacity' not in params:
        params['opacity'] = 1.0
    else:
        params['opacity'] = float(params['opacity'])
    if 'width' not in params:
        params['width'] = 2
    else:
        params['width'] = int(params['width'])
    if 'markers' not in params:
        params['markers'] = 0
    else:
        params['markers'] = int(params['markers'])
    if 'markerBorder' not in params:
        params['markerBorder'] = 2
    else:
        params['markerBorder'] = int(params['markerBorder'])
    
    try:
        feature_id = state.add_feature('polyline', parsed_cmd['coords'], params, feature_id=user_id)
        return {
            'action': 'add',
            'id': feature_id,
            'type': 'polyline',
            'coords': parsed_cmd['coords'],  # Array of points
            'params': params
        }
    except ValueError as e:
        _log_error("add-polyline", str(e), parsed_cmd)
        return None


def handle_add_polygon(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle add-polygon command.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict
    
    Returns:
        Broadcast message dict or None on error
    """
    # Validate: at least 3 coordinates required
    if len(parsed_cmd['coords']) < 3:
        _log_error("add-polygon", f"add-polygon requires at least 3 coordinates, got {len(parsed_cmd['coords'])}", parsed_cmd)
        return None
    
    user_id = parsed_cmd['params'].get('id')
    
    # Apply defaults for parameters
    params = parsed_cmd['params'].copy()
    if 'color' not in params:
        params['color'] = '#007cff'
    if 'opacity' not in params:
        params['opacity'] = 0.3
    else:
        params['opacity'] = float(params['opacity'])
    if 'border' not in params:
        params['border'] = 2
    else:
        params['border'] = int(params['border'])
    
    try:
        feature_id = state.add_feature('polygon', parsed_cmd['coords'], params, feature_id=user_id)
        return {
            'action': 'add',
            'id': feature_id,
            'type': 'polygon',
            'coords': parsed_cmd['coords'],  # Array of points
            'params': params
        }
    except ValueError as e:
        _log_error("add-polygon", str(e), parsed_cmd)
        return None


def handle_remove(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle remove command.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict
    
    Returns:
        Broadcast message dict or None on error
    """
    feature_id = parsed_cmd['params'].get('id')
    tag = parsed_cmd['params'].get('tag')
    
    if not feature_id and not tag:
        _log_error("remove", "remove command requires either id or tag parameter", parsed_cmd)
        return None
    
    if feature_id and tag:
        _log_error("remove", "remove command accepts either id or tag, not both", parsed_cmd)
        return None
    
    if feature_id:
        # Remove by ID
        if state.remove_feature(feature_id):
            return {
                'action': 'remove',
                'id': feature_id
            }
        else:
            _log_error("remove", f"Feature with id '{feature_id}' not found", parsed_cmd)
            return None
    else:
        # Remove by tag
        removed_ids = state.remove_features_by_tag(tag)
        if removed_ids:
            return {
                'action': 'remove-by-tag',
                'tag': tag,
                'ids': removed_ids
            }
        else:
            _log_error("remove", f"No features found with tag '{tag}'", parsed_cmd)
            return None


def handle_clear(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle clear command.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict
    
    Returns:
        Broadcast message dict
    """
    removed_ids = state.clear_all()
    return {
        'action': 'clear',
        'ids': removed_ids
    }


def handle_update_current_position(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle update-current-position command.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict
    
    Returns:
        Broadcast message dict or None on error
    """
    # Validate: exactly 1 coordinate required
    if len(parsed_cmd['coords']) != 1:
        _log_error("update-current-position", f"update-current-position requires exactly 1 coordinate, got {len(parsed_cmd['coords'])}", parsed_cmd)
        return None
    
    return {
        'action': 'update-current-position',
        'coords': parsed_cmd['coords'][0],  # [lat, lng]
        'params': parsed_cmd['params']
    }


def handle_help(state: State, parsed_cmd: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle help command - shows available commands and parameters.
    
    Args:
        state: The State instance
        parsed_cmd: Parsed command dict
    
    Returns:
        None (prints to stdout instead of broadcasting)
    """
    help_text = """
Available Commands:
===================

add-point (lat,lng) [parameters]
  Add a point marker to the map
  Parameters:
    id=<id>           - Unique identifier (auto-generated if not provided)
    tag=<tag>         - Tag for grouping features
    color=<color>     - CSS color (named: red, blue; hex: #FF5733; default: #007cff)
    label=<text>      - Label text (use quotes for spaces: label="My Point")
    opacity=<0.0-1.0> - Transparency (default: 1.0)
    radius=<pixels>   - Circle radius in pixels (default: 4)
    border=<pixels>   - Border width in pixels (default: 2)
  Example: add-point (52.5,13.4) color=red label="Home" radius=6 border=3

add-polyline (lat,lng);(lat,lng);... [parameters]
  Add a line connecting multiple points
  Parameters:
    id=<id>           - Unique identifier
    tag=<tag>         - Tag for grouping
    color=<color>     - Line color (default: #007cff)
    width=<pixels>    - Line width in pixels (default: 2)
    opacity=<0.0-1.0> - Transparency (default: 1.0)
    markers=<pixels>  - Circle radius at points (0=off, default: 0)
    label=<text>      - Label text
  Example: add-polyline (52.5,13.4);(52.6,13.5) color=blue width=5

add-polygon (lat,lng);(lat,lng);... [parameters]
  Add a filled polygon area
  Parameters:
    id=<id>           - Unique identifier
    tag=<tag>         - Tag for grouping
    color=<color>     - Fill and border color (default: #007cff)
    opacity=<0.0-1.0> - Fill transparency (default: 1.0)
    label=<text>      - Label text
  Example: add-polygon (52.1,13.1);(52.2,13.2);(52.15,13.15) color=green opacity=0.5

update-current-position (lat,lng)
  Update the current position marker (blue chevron)
  Example: update-current-position (52.5,13.4)

remove id=<id>
  Remove a feature by its ID
  Example: remove id=my-point

remove tag=<tag>
  Remove all features with a specific tag
  Example: remove tag=traffic

clear
  Remove all features from the map
  Example: clear

help
  Show this help message

Tips:
-----
- Coordinates: (latitude,longitude) - e.g., (52.5,13.4)
- Multiple coordinates: separate with semicolons - (52.5,13.4);(52.6,13.5)
- String values with spaces: use quotes - label="My Label"
- Colors: Multiple formats supported:
  * Named colors: red, blue, green, yellow, orange, purple, pink, cyan, brown, black, white, gray
  * Dark variants: darkred, darkblue, darkgreen, darkorange, darkgray, etc.
  * Light variants: lightblue, lightgreen, lightcoral, lightgray, lightyellow, etc.
  * Extended names: crimson, navy, teal, indigo, violet, magenta, lime, gold, silver
  * Hex codes: #FF0000 (red), #0000FF (blue), #00FF00 (green), #FF5733 (orange)
- Auto-focus and Follow Position can be toggled via web UI buttons
- Map can be cleared via web UI Clear button
"""
    print(help_text)
    return None


# Command registry
COMMAND_HANDLERS = {
    'add-point': handle_add_point,
    'add-polyline': handle_add_polyline,
    'add-polygon': handle_add_polygon,
    'remove': handle_remove,
    'clear': handle_clear,
    'update-current-position': handle_update_current_position,
    'help': handle_help,
}


def _log_error(cmd: str, message: str, parsed_cmd: Dict[str, Any] = None):
    """
    Log error to stderr in red.
    
    Args:
        cmd: Command name
        message: Error message
        parsed_cmd: Optional parsed command dict (to extract original line)
    """
    original_line = parsed_cmd.get('_original_line', '') if parsed_cmd else ''
    
    if original_line:
        # Extract parameters (everything after command name)
        parts = original_line.split(None, 1)  # Split on first whitespace
        params = parts[1] if len(parts) > 1 else ""
        
        # Take first 20 characters of params, add "..." if truncated
        if len(params) > 20:
            params_preview = params[:20] + "..."
        else:
            params_preview = params
        
        print(f"{RED}FAIL: {cmd} {params_preview}{RESET}", file=sys.stderr)
    else:
        print(f"{RED}FAIL: {cmd}{RESET}", file=sys.stderr)
    print(f"{RED}FAIL: {message}{RESET}", file=sys.stderr)
