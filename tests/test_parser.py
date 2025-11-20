"""
Tests for parser module.
"""
import pytest
from mapcat.parser import parse_command


def test_parse_add_point_simple():
    result = parse_command('add-point (52.5,13.4)')
    assert result is not None
    assert result['cmd'] == 'add-point'
    assert result['coords'] == [[52.5, 13.4]]
    assert result['params'] == {}


def test_parse_add_point_with_params():
    result = parse_command('add-point (52.5,13.4) color=red label="Home"')
    assert result is not None
    assert result['cmd'] == 'add-point'
    assert result['coords'] == [[52.5, 13.4]]
    assert result['params'] == {'color': 'red', 'label': 'Home'}


def test_parse_add_point_with_id():
    result = parse_command('add-point (52.5,13.4) id=my-point color=blue')
    assert result is not None
    assert result['cmd'] == 'add-point'
    assert result['coords'] == [[52.5, 13.4]]
    assert result['params'] == {'id': 'my-point', 'color': 'blue'}


def test_parse_add_polyline():
    result = parse_command('add-polyline (52.5,13.4);(52.6,13.5) color=blue')
    assert result is not None
    assert result['cmd'] == 'add-polyline'
    assert result['coords'] == [[52.5, 13.4], [52.6, 13.5]]
    assert result['params'] == {'color': 'blue'}


def test_parse_add_polyline_multiple():
    result = parse_command('add-polyline (52.1,13.1);(52.2,13.2);(52.3,13.3) id=route')
    assert result is not None
    assert result['cmd'] == 'add-polyline'
    assert len(result['coords']) == 3
    assert result['coords'][0] == [52.1, 13.1]
    assert result['coords'][1] == [52.2, 13.2]
    assert result['coords'][2] == [52.3, 13.3]
    assert result['params'] == {'id': 'route'}


def test_parse_add_polygon():
    result = parse_command('add-polygon (52.1,13.1);(52.2,13.2);(52.15,13.15) color=green')
    assert result is not None
    assert result['cmd'] == 'add-polygon'
    assert len(result['coords']) == 3
    assert result['params'] == {'color': 'green'}


def test_parse_remove():
    result = parse_command('remove id=my-point')
    assert result is not None
    assert result['cmd'] == 'remove'
    assert result['coords'] == []
    assert result['params'] == {'id': 'my-point'}


def test_parse_clear():
    result = parse_command('clear')
    assert result is not None
    assert result['cmd'] == 'clear'
    assert result['coords'] == []
    assert result['params'] == {}


def test_parse_empty_line():
    result = parse_command('')
    assert result is None


def test_parse_whitespace_only():
    result = parse_command('   ')
    assert result is None


def test_parse_invalid_coord_format():
    result = parse_command('add-point (52.5) color=red')
    assert result is None


def test_parse_invalid_coord_values():
    result = parse_command('add-point (abc,def) color=red')
    assert result is None


def test_parse_lat_out_of_range():
    result = parse_command('add-point (91.0,13.4) color=red')
    assert result is None


def test_parse_lng_out_of_range():
    result = parse_command('add-point (52.5,181.0) color=red')
    assert result is None


def test_parse_quoted_label_with_spaces():
    result = parse_command('add-point (52.5,13.4) label="My Home Location"')
    assert result is not None
    assert result['params']['label'] == 'My Home Location'


def test_parse_single_quotes():
    result = parse_command("add-point (52.5,13.4) label='My Home'")
    assert result is not None
    assert result['params']['label'] == 'My Home'


def test_parse_multiple_params():
    result = parse_command('add-point (52.5,13.4) id=p1 color=red width=5 opacity=0.8')
    assert result is not None
    assert result['params'] == {
        'id': 'p1',
        'color': 'red',
        'width': '5',
        'opacity': '0.8'
    }


def test_parse_incomplete_coordinate_single():
    """Test that incomplete single coordinate is rejected."""
    result = parse_command('add-point (52.5,13.4')
    assert result is None


def test_parse_incomplete_coordinate_polyline():
    """Test that incomplete coordinate in polyline is rejected."""
    result = parse_command('add-polyline (52.5,13.4);(52.6,13.5);(3.44')
    assert result is None


def test_parse_incomplete_coordinate_middle():
    """Test that incomplete coordinate in the middle is rejected."""
    result = parse_command('add-polyline (52.5,13.4);(52.6,;(52.7,13.7)')
    assert result is None


def test_parse_extra_closing_paren():
    """Test that extra closing parenthesis is rejected."""
    result = parse_command('add-point (52.5,13.4))')
    assert result is None


def test_parse_unmatched_nested_parens():
    """Test that unmatched nested parentheses are rejected."""
    result = parse_command('add-point ((52.5,13.4)')
    assert result is None
