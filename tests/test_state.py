"""
Tests for state module.
"""
import pytest
from mapcat.state import State


def test_state_init():
    state = State()
    assert len(state.features) == 0
    assert len(state.used_ids) == 0


def test_add_feature_with_generated_id():
    state = State()
    feature_id = state.add_feature('point', [[52.5, 13.4]], {'color': 'red'})
    
    assert feature_id is not None
    assert len(feature_id) == 8  # 8 hex chars
    assert feature_id in state.features
    assert feature_id in state.used_ids


def test_add_feature_with_user_id():
    state = State()
    feature_id = state.add_feature('point', [[52.5, 13.4]], {'color': 'red'}, feature_id='my-point')
    
    assert feature_id == 'my-point'
    assert 'my-point' in state.features
    assert 'my-point' in state.used_ids


def test_add_feature_duplicate_id_raises():
    state = State()
    state.add_feature('point', [[52.5, 13.4]], {}, feature_id='dup')
    
    with pytest.raises(ValueError, match="already exists"):
        state.add_feature('point', [[52.6, 13.5]], {}, feature_id='dup')


def test_add_multiple_features():
    state = State()
    id1 = state.add_feature('point', [[52.5, 13.4]], {'color': 'red'})
    id2 = state.add_feature('polyline', [[52.5, 13.4], [52.6, 13.5]], {'color': 'blue'})
    
    assert id1 != id2
    assert len(state.features) == 2


def test_get_feature():
    state = State()
    feature_id = state.add_feature('point', [[52.5, 13.4]], {'color': 'red'}, feature_id='test')
    
    feature = state.get_feature('test')
    assert feature is not None
    assert feature['type'] == 'point'
    assert feature['coords'] == [[52.5, 13.4]]
    assert feature['params'] == {'color': 'red'}


def test_get_feature_not_found():
    state = State()
    feature = state.get_feature('nonexistent')
    assert feature is None


def test_remove_feature():
    state = State()
    feature_id = state.add_feature('point', [[52.5, 13.4]], {}, feature_id='to-remove')
    
    result = state.remove_feature('to-remove')
    assert result is True
    assert 'to-remove' not in state.features
    assert 'to-remove' not in state.used_ids


def test_remove_feature_not_found():
    state = State()
    result = state.remove_feature('nonexistent')
    assert result is False


def test_clear_all():
    state = State()
    id1 = state.add_feature('point', [[52.5, 13.4]], {})
    id2 = state.add_feature('point', [[52.6, 13.5]], {})
    id3 = state.add_feature('polyline', [[52.5, 13.4], [52.6, 13.5]], {})
    
    removed = state.clear_all()
    
    assert len(removed) == 3
    assert id1 in removed
    assert id2 in removed
    assert id3 in removed
    assert len(state.features) == 0
    assert len(state.used_ids) == 0


def test_clear_all_empty():
    state = State()
    removed = state.clear_all()
    assert removed == []


def test_generated_ids_are_unique():
    state = State()
    ids = set()
    for _ in range(100):
        feature_id = state.add_feature('point', [[52.5, 13.4]], {})
        ids.add(feature_id)
    
    # All IDs should be unique
    assert len(ids) == 100
    assert len(state.features) == 100
