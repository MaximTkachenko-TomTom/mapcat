"""
Tests for command handlers.
"""
import pytest
from mapcat.state import State
from mapcat.commands import (
    handle_add_point,
    handle_add_polyline,
    handle_add_polygon,
    handle_remove,
    handle_clear,
    COMMAND_HANDLERS
)


def test_handle_add_point():
    state = State()
    parsed = {
        'cmd': 'add-point',
        'coords': [[52.5, 13.4]],
        'params': {'color': 'red'}
    }
    
    result = handle_add_point(state, parsed)
    
    assert result is not None
    assert result['action'] == 'add'
    assert result['type'] == 'point'
    assert result['coords'] == [52.5, 13.4]
    assert result['params'] == {'color': 'red', 'opacity': 1.0, 'radius': 4, 'border': 2}
    assert 'id' in result
    assert len(state.features) == 1


def test_handle_add_point_with_user_id():
    state = State()
    parsed = {
        'cmd': 'add-point',
        'coords': [[52.5, 13.4]],
        'params': {'id': 'my-point', 'color': 'blue'}
    }
    
    result = handle_add_point(state, parsed)
    
    assert result is not None
    assert result['id'] == 'my-point'
    assert state.get_feature('my-point') is not None


def test_handle_add_point_invalid_coord_count():
    state = State()
    parsed = {
        'cmd': 'add-point',
        'coords': [[52.5, 13.4], [52.6, 13.5]],  # Too many
        'params': {}
    }
    
    result = handle_add_point(state, parsed)
    assert result is None
    assert len(state.features) == 0


def test_handle_add_point_duplicate_id():
    state = State()
    parsed1 = {
        'cmd': 'add-point',
        'coords': [[52.5, 13.4]],
        'params': {'id': 'dup'}
    }
    parsed2 = {
        'cmd': 'add-point',
        'coords': [[52.6, 13.5]],
        'params': {'id': 'dup'}
    }
    
    result1 = handle_add_point(state, parsed1)
    assert result1 is not None
    
    result2 = handle_add_point(state, parsed2)
    assert result2 is None  # Should fail


def test_handle_add_polyline():
    state = State()
    parsed = {
        'cmd': 'add-polyline',
        'coords': [[52.5, 13.4], [52.6, 13.5]],
        'params': {'color': 'blue'}
    }
    
    result = handle_add_polyline(state, parsed)
    
    assert result is not None
    assert result['action'] == 'add'
    assert result['type'] == 'polyline'
    assert len(result['coords']) == 2


def test_handle_add_polyline_insufficient_coords():
    state = State()
    parsed = {
        'cmd': 'add-polyline',
        'coords': [[52.5, 13.4]],  # Only 1 coord
        'params': {}
    }
    
    result = handle_add_polyline(state, parsed)
    assert result is None


def test_handle_add_polygon():
    state = State()
    parsed = {
        'cmd': 'add-polygon',
        'coords': [[52.1, 13.1], [52.2, 13.2], [52.15, 13.15]],
        'params': {'color': 'green'}
    }
    
    result = handle_add_polygon(state, parsed)
    
    assert result is not None
    assert result['action'] == 'add'
    assert result['type'] == 'polygon'
    assert len(result['coords']) == 3


def test_handle_add_polygon_insufficient_coords():
    state = State()
    parsed = {
        'cmd': 'add-polygon',
        'coords': [[52.1, 13.1], [52.2, 13.2]],  # Only 2 coords
        'params': {}
    }
    
    result = handle_add_polygon(state, parsed)
    assert result is None


def test_handle_remove():
    state = State()
    state.add_feature('point', [[52.5, 13.4]], {}, feature_id='to-remove')
    
    parsed = {
        'cmd': 'remove',
        'coords': [],
        'params': {'id': 'to-remove'}
    }
    
    result = handle_remove(state, parsed)
    
    assert result is not None
    assert result['action'] == 'remove'
    assert result['id'] == 'to-remove'
    assert len(state.features) == 0


def test_handle_remove_not_found():
    state = State()
    parsed = {
        'cmd': 'remove',
        'coords': [],
        'params': {'id': 'nonexistent'}
    }
    
    result = handle_remove(state, parsed)
    assert result is None


def test_handle_remove_missing_id():
    state = State()
    parsed = {
        'cmd': 'remove',
        'coords': [],
        'params': {}
    }
    
    result = handle_remove(state, parsed)
    assert result is None


def test_handle_clear():
    state = State()
    id1 = state.add_feature('point', [[52.5, 13.4]], {})
    id2 = state.add_feature('polyline', [[52.5, 13.4], [52.6, 13.5]], {})
    
    parsed = {
        'cmd': 'clear',
        'coords': [],
        'params': {}
    }
    
    result = handle_clear(state, parsed)
    
    assert result is not None
    assert result['action'] == 'clear'
    assert len(result['ids']) == 2
    assert id1 in result['ids']
    assert id2 in result['ids']
    assert len(state.features) == 0


def test_command_handlers_registry():
    assert 'add-point' in COMMAND_HANDLERS
    assert 'add-polyline' in COMMAND_HANDLERS
    assert 'add-polygon' in COMMAND_HANDLERS
    assert 'remove' in COMMAND_HANDLERS
    assert 'clear' in COMMAND_HANDLERS
