"""
Parser for command strings from logcat.
"""
import re
import sys
from typing import Optional, Dict, List, Any


def parse_command(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a command line into a structured dict.
    
    Format: <command> <coords> [key=value ...]
    
    Examples:
        add-point (52.5,13.4) color=red label="Home"
        add-polyline (52.5,13.4);(52.6,13.5) color=blue
        remove id=my-point
        clear
    
    Returns:
        Dict with 'cmd', 'coords' (list of [lat, lng]), and 'params' (dict)
        Returns None if parsing fails.
    """
    line = line.strip()
    if not line:
        return None
    
    # Split into tokens, respecting quotes
    tokens = _tokenize(line)
    if not tokens:
        return None
    
    # First token is the command
    cmd = tokens[0]
    
    # Parse coordinates (if present)
    coords = []
    params = {}
    
    # Find coordinate patterns: (lat,lng) or (lat,lng);(lat,lng)...
    coord_pattern = r'\(([^)]+)\)'
    
    for token in tokens[1:]:
        # Check if token is a coordinate
        if '(' in token and ')' in token:
            matches = re.findall(coord_pattern, token)
            for match in matches:
                parts = match.split(',')
                if len(parts) != 2:
                    _log_error(f"Invalid coordinate format: ({match})")
                    return None
                try:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                    
                    # Validate ranges
                    if not (-90 <= lat <= 90):
                        _log_error(f"Latitude out of range: {lat}")
                        return None
                    if not (-180 <= lng <= 180):
                        _log_error(f"Longitude out of range: {lng}")
                        return None
                    
                    coords.append([lat, lng])
                except ValueError:
                    _log_error(f"Invalid coordinate values: ({match})")
                    return None
        # Check if token is a parameter (key=value)
        elif '=' in token:
            key, value = token.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes from value if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            params[key] = value
        else:
            _log_error(f"Unexpected token: {token}")
            return None
    
    return {
        'cmd': cmd,
        'coords': coords,
        'params': params
    }


def _tokenize(line: str) -> List[str]:
    """
    Split line into tokens, respecting quoted strings.
    
    Example:
        'add-point (52.5,13.4) color=red label="My Label"'
        -> ['add-point', '(52.5,13.4)', 'color=red', 'label="My Label"']
    """
    tokens = []
    current = []
    in_quotes = False
    quote_char = None
    in_parens = 0
    
    for char in line:
        if char in ('"', "'") and not in_parens:
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
            current.append(char)
        elif char == '(' and not in_quotes:
            in_parens += 1
            current.append(char)
        elif char == ')' and not in_quotes:
            in_parens -= 1
            current.append(char)
        elif char == ' ' and not in_quotes and in_parens == 0:
            if current:
                tokens.append(''.join(current))
                current = []
        else:
            current.append(char)
    
    if current:
        tokens.append(''.join(current))
    
    return tokens


def _log_error(message: str):
    """Log error to stderr."""
    print(f"Parser error: {message}", file=sys.stderr)
