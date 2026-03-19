"""
Frontend tests for mapcat/static/index.html.

Each test uses the `mock_page` fixture which:
  - Serves index.html via the real mapcat HTTP server.
  - Replaces the MapLibre GL CDN bundle with a lightweight spy mock.
  - Exposes window.__mapCalls to verify map API interactions.
  - Exposes window.features / window.autofocus etc. for state assertions.

Tests drive the page by calling JS functions (e.g. renderFeature / handleMessage)
directly via page.evaluate(), simulating the messages a WebSocket would deliver.
"""
import pytest
from playwright.sync_api import Page


# ── Helpers ────────────────────────────────────────────────────────────────────

def map_calls(page: Page) -> list[dict]:
    """Return the list of recorded map mock calls."""
    return page.evaluate('window.__mapCalls')


def methods(calls: list[dict]) -> list[str]:
    """Return the list of method names from recorded calls."""
    return [c['method'] for c in calls]


def calls_for(calls: list[dict], method: str) -> list[dict]:
    """Filter calls by method name."""
    return [c for c in calls if c['method'] == method]


# ── Coordinate helpers ─────────────────────────────────────────────────────────

def test_to_geo_coord_flips_lat_lng(mock_page: Page):
    result = mock_page.evaluate('toGeoCoord([52.5, 13.4])')
    assert result == [13.4, 52.5]


def test_to_geo_coord_zero_zero(mock_page: Page):
    result = mock_page.evaluate('toGeoCoord([0, 0])')
    assert result == [0, 0]


def test_to_geo_coords_flips_multiple(mock_page: Page):
    result = mock_page.evaluate('toGeoCoords([[52.5, 13.4], [52.6, 13.5]])')
    assert result == [[13.4, 52.5], [13.5, 52.6]]


# ── add-point ─────────────────────────────────────────────────────────────────

def test_add_point_updates_features_state(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'point', id: 'p1',
            coords: [52.5, 13.4],
            params: { color: '#ff0000', opacity: 1.0, radius: 4, border: 2 }
        })
    """)
    feature_ids = mock_page.evaluate('Object.keys(features)')
    assert 'p1' in feature_ids


def test_add_point_calls_add_source_and_layer(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'point', id: 'p2',
            coords: [52.5, 13.4],
            params: { color: '#ff0000', opacity: 1.0, radius: 4, border: 2 }
        })
    """)
    calls = map_calls(mock_page)
    assert 'addSource' in methods(calls)
    assert 'addLayer' in methods(calls)


def test_add_point_source_id_matches_feature_id(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'point', id: 'p3',
            coords: [48.8, 2.3],
            params: {}
        })
    """)
    src_calls = calls_for(map_calls(mock_page), 'addSource')
    assert any(c['args'][0] == 'src-p3' for c in src_calls)


def test_add_point_layer_type_is_circle(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'point', id: 'p4',
            coords: [48.8, 2.3],
            params: {}
        })
    """)
    layer_calls = calls_for(map_calls(mock_page), 'addLayer')
    assert any(c['args'][0]['type'] == 'circle' for c in layer_calls)


def test_add_point_geojson_coordinates_are_lng_lat(mock_page: Page):
    """Verifies the [lat,lng] → [lng,lat] flip is applied to the GeoJSON source."""
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'point', id: 'p5',
            coords: [52.5, 13.4],
            params: {}
        })
    """)
    src_calls = calls_for(map_calls(mock_page), 'addSource')
    src = next(c['args'][1] for c in src_calls if c['args'][0] == 'src-p5')
    coords = src['data']['geometry']['coordinates']
    assert coords == [13.4, 52.5]


# ── add-polyline ──────────────────────────────────────────────────────────────

def test_add_polyline_updates_features_state(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polyline', id: 'l1',
            coords: [[52.5, 13.4], [52.6, 13.5]],
            params: {}
        })
    """)
    assert 'l1' in mock_page.evaluate('Object.keys(features)')


def test_add_polyline_layer_type_is_line(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polyline', id: 'l2',
            coords: [[52.5, 13.4], [52.6, 13.5]],
            params: {}
        })
    """)
    layer_calls = calls_for(map_calls(mock_page), 'addLayer')
    assert any(c['args'][0]['type'] == 'line' for c in layer_calls)


def test_add_polyline_geojson_type_is_linestring(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polyline', id: 'l3',
            coords: [[52.5, 13.4], [52.6, 13.5]],
            params: {}
        })
    """)
    src_calls = calls_for(map_calls(mock_page), 'addSource')
    src = next(c['args'][1] for c in src_calls if c['args'][0] == 'src-l3')
    assert src['data']['geometry']['type'] == 'LineString'


def test_add_polyline_with_markers_creates_extra_circle_layer(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polyline', id: 'l4',
            coords: [[52.5, 13.4], [52.6, 13.5]],
            params: { markers: 5 }
        })
    """)
    layer_calls = calls_for(map_calls(mock_page), 'addLayer')
    types = [c['args'][0]['type'] for c in layer_calls]
    assert 'line' in types
    assert 'circle' in types


# ── add-polygon ───────────────────────────────────────────────────────────────

def test_add_polygon_updates_features_state(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polygon', id: 'poly1',
            coords: [[52.1, 13.1], [52.2, 13.2], [52.15, 13.15]],
            params: {}
        })
    """)
    assert 'poly1' in mock_page.evaluate('Object.keys(features)')


def test_add_polygon_creates_fill_and_outline_layers(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polygon', id: 'poly2',
            coords: [[52.1, 13.1], [52.2, 13.2], [52.15, 13.15]],
            params: {}
        })
    """)
    layer_calls = calls_for(map_calls(mock_page), 'addLayer')
    types = [c['args'][0]['type'] for c in layer_calls]
    assert 'fill' in types
    assert 'line' in types


def test_add_polygon_geojson_ring_is_closed(mock_page: Page):
    """GeoJSON polygon ring must repeat the first coord at the end."""
    mock_page.evaluate("""
        renderFeature({
            action: 'add', type: 'polygon', id: 'poly3',
            coords: [[52.1, 13.1], [52.2, 13.2], [52.15, 13.15]],
            params: {}
        })
    """)
    src_calls = calls_for(map_calls(mock_page), 'addSource')
    src = next(c['args'][1] for c in src_calls if c['args'][0] == 'src-poly3')
    ring = src['data']['geometry']['coordinates'][0]
    assert ring[0] == ring[-1], 'GeoJSON polygon ring must be closed (first == last coord)'


# ── remove by ID ──────────────────────────────────────────────────────────────

def test_remove_deletes_feature_from_state(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'rem1', coords: [52.5, 13.4], params: {} });
        removeFeature('rem1');
    """)
    assert 'rem1' not in mock_page.evaluate('Object.keys(features)')


def test_remove_calls_remove_layer_and_source(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'rem2', coords: [52.5, 13.4], params: {} });
        window.__mapCalls = [];   // reset so only removal calls are captured
        removeFeature('rem2');
    """)
    calls = map_calls(mock_page)
    assert 'removeLayer' in methods(calls)
    assert 'removeSource' in methods(calls)


def test_remove_unknown_id_does_not_crash(mock_page: Page):
    """Removing a non-existent ID should not throw."""
    mock_page.evaluate("removeFeature('does-not-exist')")
    # If we get here without an exception the test passes.


# ── remove-by-tag ─────────────────────────────────────────────────────────────

def test_remove_by_tag_removes_all_matching_features(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'tag1', coords: [52.5, 13.4], params: { tag: 'traffic' } });
        renderFeature({ action: 'add', type: 'point', id: 'tag2', coords: [52.6, 13.5], params: { tag: 'traffic' } });
        removeFeaturesByTag(['tag1', 'tag2']);
    """)
    feature_ids = mock_page.evaluate('Object.keys(features)')
    assert 'tag1' not in feature_ids
    assert 'tag2' not in feature_ids


def test_remove_by_tag_leaves_unrelated_features(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'keep1', coords: [52.5, 13.4], params: {} });
        renderFeature({ action: 'add', type: 'point', id: 'gone1', coords: [52.6, 13.5], params: {} });
        removeFeaturesByTag(['gone1']);
    """)
    feature_ids = mock_page.evaluate('Object.keys(features)')
    assert 'keep1' in feature_ids
    assert 'gone1' not in feature_ids


# ── clear ─────────────────────────────────────────────────────────────────────

def test_clear_empties_features_state(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'c1', coords: [52.5, 13.4], params: {} });
        renderFeature({ action: 'add', type: 'point', id: 'c2', coords: [52.6, 13.5], params: {} });
        clearAllFeatures();
    """)
    assert mock_page.evaluate('Object.keys(features)') == []


def test_clear_calls_remove_layer_for_all_features(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'd1', coords: [52.5, 13.4], params: {} });
        renderFeature({ action: 'add', type: 'point', id: 'd2', coords: [52.6, 13.5], params: {} });
        window.__mapCalls = [];
        clearAllFeatures();
    """)
    calls = map_calls(mock_page)
    assert 'removeLayer' in methods(calls)


# ── autofocus ─────────────────────────────────────────────────────────────────

def test_autofocus_single_point_calls_fly_to(mock_page: Page):
    """A single point (bbox is a single coordinate) should trigger flyTo."""
    mock_page.evaluate("""
        autofocus = true;
        renderFeature({ action: 'add', type: 'point', id: 'af1', coords: [52.5, 13.4], params: {} });
    """)
    assert 'flyTo' in methods(map_calls(mock_page))


def test_autofocus_multiple_points_calls_fit_bounds(mock_page: Page):
    """Multiple points at different locations should trigger fitBounds."""
    mock_page.evaluate("""
        autofocus = true;
        renderFeature({ action: 'add', type: 'point', id: 'af2', coords: [52.5, 13.4], params: {} });
        renderFeature({ action: 'add', type: 'point', id: 'af3', coords: [53.0, 14.0], params: {} });
    """)
    assert 'fitBounds' in methods(map_calls(mock_page))


def test_autofocus_disabled_after_drag_skips_zoom(mock_page: Page):
    """After a dragstart event autofocus should be false and no zoom calls made."""
    mock_page.evaluate("""
        autofocus = true;
        map.fire('dragstart');          // triggers the dragstart handler
        window.__mapCalls = [];         // reset after drag
        renderFeature({ action: 'add', type: 'point', id: 'af4', coords: [52.5, 13.4], params: {} });
    """)
    call_methods = methods(map_calls(mock_page))
    assert 'flyTo' not in call_methods
    assert 'fitBounds' not in call_methods


def test_drag_disables_autofocus_flag(mock_page: Page):
    mock_page.evaluate("autofocus = true; map.fire('dragstart');")
    assert mock_page.evaluate('autofocus') is False


# ── update-current-position ────────────────────────────────────────────────────

def test_update_current_position_creates_marker(mock_page: Page):
    mock_page.evaluate("updateCurrentPosition([52.5, 13.4])")
    assert mock_page.evaluate('currentPositionMarker !== null')


def test_update_current_position_calls_marker_set_lng_lat(mock_page: Page):
    mock_page.evaluate("updateCurrentPosition([52.5, 13.4])")
    assert 'Marker.setLngLat' in methods(map_calls(mock_page))


def test_update_current_position_sets_previous_position(mock_page: Page):
    mock_page.evaluate("updateCurrentPosition([52.5, 13.4])")
    assert mock_page.evaluate('previousPosition') == [52.5, 13.4]


def test_update_current_position_second_call_removes_old_marker(mock_page: Page):
    mock_page.evaluate("""
        updateCurrentPosition([52.5, 13.4]);
        window.__mapCalls = [];
        updateCurrentPosition([52.6, 13.5]);
    """)
    assert 'Marker.remove' in methods(map_calls(mock_page))


def test_follow_position_calls_set_center(mock_page: Page):
    mock_page.evaluate("""
        followPosition = true;
        updateCurrentPosition([52.5, 13.4]);
    """)
    assert 'setCenter' in methods(map_calls(mock_page))


def test_follow_position_off_does_not_call_set_center(mock_page: Page):
    mock_page.evaluate("""
        followPosition = false;
        updateCurrentPosition([52.5, 13.4]);
    """)
    assert 'setCenter' not in methods(map_calls(mock_page))


# ── handleMessage dispatcher ──────────────────────────────────────────────────

def test_handle_message_add_dispatches_to_render_feature(mock_page: Page):
    mock_page.evaluate("""
        handleMessage({
            action: 'add', type: 'point', id: 'hm1',
            coords: [52.5, 13.4], params: {}
        })
    """)
    assert 'hm1' in mock_page.evaluate('Object.keys(features)')


def test_handle_message_clear_clears_all(mock_page: Page):
    mock_page.evaluate("""
        renderFeature({ action: 'add', type: 'point', id: 'hm2', coords: [52.5, 13.4], params: {} });
        handleMessage({ action: 'clear' });
    """)
    assert mock_page.evaluate('Object.keys(features)') == []


def test_handle_message_unknown_action_does_not_crash(mock_page: Page):
    mock_page.evaluate("handleMessage({ action: 'unknown-action' })")
    # No exception means success.


def test_handle_message_missing_action_does_not_crash(mock_page: Page):
    mock_page.evaluate("handleMessage({})")
