"""
Shared fixtures for frontend (Playwright) tests.
"""
import socket
import threading
from pathlib import Path

import pytest
from playwright.sync_api import Page

from mapcat.server import StaticHandler
from http.server import ThreadingHTTPServer


_MOCK_JS = (Path(__file__).parent / 'maplibre_mock.js').read_text()


def _free_port() -> int:
    """Return a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='session')
def http_server():
    """Start the mapcat static HTTP server on a free port for the test session."""
    port = _free_port()
    httpd = ThreadingHTTPServer(('127.0.0.1', port), StaticHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{port}'
    httpd.shutdown()


@pytest.fixture
def mock_page(page: Page, http_server: str) -> Page:
    """
    Load index.html with the MapLibre GL CDN request intercepted by the spy mock.

    The fixture also:
    - Aborts the MapLibre CSS request (unnecessary for logic tests).
    - Resets window.__mapCalls to [] before each test so calls don't bleed across tests.
    - Waits until window.map is initialised before yielding.
    """
    mock_js = _MOCK_JS

    # Replace the MapLibre GL JS bundle with our lightweight spy mock.
    page.route(
        '**/maplibre-gl*.js',
        lambda route: route.fulfill(body=mock_js, content_type='application/javascript'),
    )
    # Suppress the MapLibre CSS (not needed for behaviour tests).
    page.route(
        '**/maplibre-gl*.css',
        lambda route: route.fulfill(body='', content_type='text/css'),
    )

    page.goto(http_server)

    # Wait until the mock map object is available (set synchronously by the page script).
    page.wait_for_function('typeof window.map !== "undefined"')

    # Clear any calls recorded during page initialisation.
    page.evaluate('window.__mapCalls = []')

    yield page
