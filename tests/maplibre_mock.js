/**
 * Lightweight MapLibre GL spy mock for frontend testing.
 *
 * Replaces window.maplibregl with a spy that records all map method calls
 * to window.__mapCalls = [{ method, args }, ...] and tracks which sources /
 * layers exist so getSource / getLayer return accurate truthy/null values.
 *
 * The mock Map also exposes map.fire(event) so tests can simulate DOM events
 * (e.g. 'dragstart') that the application registers via map.on().
 */
(function () {
    'use strict';

    window.__mapCalls = [];

    function record(method, args) {
        window.__mapCalls.push({ method: method, args: Array.prototype.slice.call(args) });
    }

    function createMap(/* options */) {
        var sources = {};
        var layers  = {};
        var handlers = {};  // event → [callback, ...]

        var map = {
            addSource: function (id, data) {
                record('addSource', arguments);
                sources[id] = data;
                return map;
            },
            addLayer: function (layer) {
                record('addLayer', arguments);
                layers[layer.id] = layer;
                return map;
            },
            removeLayer: function (id) {
                record('removeLayer', arguments);
                delete layers[id];
                return map;
            },
            removeSource: function (id) {
                record('removeSource', arguments);
                delete sources[id];
                return map;
            },
            getLayer: function (id) {
                return layers[id] || null;
            },
            getSource: function (id) {
                return sources[id] || null;
            },
            fitBounds: function (bounds, opts) {
                record('fitBounds', arguments);
                return map;
            },
            flyTo: function (opts) {
                record('flyTo', arguments);
                return map;
            },
            setCenter: function (center) {
                record('setCenter', arguments);
                return map;
            },
            setStyle: function (style) {
                record('setStyle', arguments);
                // Simulate style reload — app re-renders all features on this event
                (handlers['style.load'] || []).forEach(function (cb) { cb(); });
                return map;
            },
            setPaintProperty: function (layerId, prop, value) {
                record('setPaintProperty', arguments);
                return map;
            },
            getZoom: function () {
                return 14;
            },
            getCanvas: function () {
                return { style: {} };
            },
            on: function (event, layerOrCb, maybeCb) {
                // Supports both map.on('event', cb) and map.on('event', layerId, cb)
                var cb = (typeof layerOrCb === 'function') ? layerOrCb : maybeCb;
                if (!handlers[event]) handlers[event] = [];
                handlers[event].push(cb);
                return map;
            },
            /** Test helper: dispatch a named event to all registered handlers. */
            fire: function (event, eventData) {
                (handlers[event] || []).forEach(function (cb) { cb(eventData || {}); });
                return map;
            }
        };

        return map;
    }

    function createPopup(/* options */) {
        var p = {
            setLngLat: function () { return p; },
            setHTML:   function () { return p; },
            addTo:     function () { return p; },
            remove:    function () { return p; }
        };
        return p;
    }

    function createMarker(options) {
        var m = {
            setLngLat: function (lnglat) {
                record('Marker.setLngLat', arguments);
                return m;
            },
            addTo: function () {
                record('Marker.addTo', arguments);
                return m;
            },
            remove: function () {
                record('Marker.remove', arguments);
                return m;
            },
            setRotation: function (deg) {
                record('Marker.setRotation', arguments);
                return m;
            },
            setRotationAlignment: function () { return m; },
            getElement: function () {
                return (options && options.element) ? options.element : document.createElement('div');
            }
        };
        return m;
    }

    window.maplibregl = {
        Map:    function (options) { return createMap(options); },
        Popup:  function (options) { return createPopup(options); },
        Marker: function (options) { return createMarker(options); }
    };
}());
