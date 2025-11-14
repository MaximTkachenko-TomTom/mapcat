"""
Command handlers for geospatial features.
"""
import sys
from typing import Optional, Dict, Any
from mapcat.state import State


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
        _log_error(f"add-point requires exactly 1 coordinate, got {len(parsed_cmd['coords'])}")
        return None
    
    user_id = parsed_cmd['params'].get('id')
    
    try:
        feature_id = state.add_feature('point', parsed_cmd['coords'], parsed_cmd['params'], feature_id=user_id)
        return {
            'action': 'add',
            'id': feature_id,
            'type': 'point',
            'coords': parsed_cmd['coords'][0],  # Single point [lat, lng]
            'params': parsed_cmd['params']
        }
    except ValueError as e:
        _log_error(str(e))
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
        _log_error(f"add-polyline requires at least 2 coordinates, got {len(parsed_cmd['coords'])}")
        return None
    
    user_id = parsed_cmd['params'].get('id')
    
    try:
        feature_id = state.add_feature('polyline', parsed_cmd['coords'], parsed_cmd['params'], feature_id=user_id)
        return {
            'action': 'add',
            'id': feature_id,
            'type': 'polyline',
            'coords': parsed_cmd['coords'],  # Array of points
            'params': parsed_cmd['params']
        }
    except ValueError as e:
        _log_error(str(e))
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
        _log_error(f"add-polygon requires at least 3 coordinates, got {len(parsed_cmd['coords'])}")
        return None
    
    user_id = parsed_cmd['params'].get('id')
    
    try:
        feature_id = state.add_feature('polygon', parsed_cmd['coords'], parsed_cmd['params'], feature_id=user_id)
        return {
            'action': 'add',
            'id': feature_id,
            'type': 'polygon',
            'coords': parsed_cmd['coords'],  # Array of points
            'params': parsed_cmd['params']
        }
    except ValueError as e:
        _log_error(str(e))
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
    
    if not feature_id:
        _log_error("remove command requires id parameter")
        return None
    
    if state.remove_feature(feature_id):
        return {
            'action': 'remove',
            'id': feature_id
        }
    else:
        _log_error(f"Feature with id '{feature_id}' not found")
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


# Command registry
COMMAND_HANDLERS = {
    'add-point': handle_add_point,
    'add-polyline': handle_add_polyline,
    'add-polygon': handle_add_polygon,
    'remove': handle_remove,
    'clear': handle_clear,
}


def _log_error(message: str):
    """Log error to stderr."""
    print(f"Command error: {message}", file=sys.stderr)
