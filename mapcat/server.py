
"""
WebSocket and HTTP server for mapcat.
"""
import asyncio
import functools
import os
import subprocess
import websockets
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


@functools.lru_cache(maxsize=1)
def _build_version() -> str:
    """Return version string 'YYYY.MM.DD-shortHash' from the last git commit."""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd %h', '--date=format:%Y.%m.%d'],
            capture_output=True, text=True, check=True,
            cwd=os.path.dirname(__file__),
        )
        parts = result.stdout.strip().split()
        if len(parts) == 2:
            return f"{parts[0]}-{parts[1]}"
    except Exception:
        pass
    return 'unknown'


class StaticHandler(SimpleHTTPRequestHandler):
	def do_GET(self):
		clean_path = self.path.split('?')[0].rstrip('/')
		if clean_path in ('', '/index.html'):
			self._serve_index()
		else:
			super().do_GET()

	def _serve_index(self):
		html_path = os.path.join(STATIC_DIR, 'index.html')
		with open(html_path, 'r', encoding='utf-8') as f:
			content = f.read().replace('__VERSION__', _build_version())
		encoded = content.encode('utf-8')
		self.send_response(200)
		self.send_header('Content-Type', 'text/html; charset=utf-8')
		self.send_header('Content-Length', str(len(encoded)))
		self.end_headers()
		self.wfile.write(encoded)

	def translate_path(self, path):
		# Serve files from static directory
		relpath = path.lstrip('/')
		fullpath = os.path.join(STATIC_DIR, relpath)
		if os.path.isdir(fullpath):
			return os.path.join(fullpath, 'index.html')
		return fullpath if os.path.exists(fullpath) else os.path.join(STATIC_DIR, 'index.html')
	
	def end_headers(self):
		# Disable caching for development
		self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
		self.send_header('Pragma', 'no-cache')
		self.send_header('Expires', '0')
		super().end_headers()


clients = set()
state_getter = None  # Will be set by main.py to get current state

def set_state_getter(getter):
	"""Set the function to get current state."""
	global state_getter
	state_getter = getter

async def broadcast(message):
	"""Broadcast message to all connected WebSocket clients."""
	if clients:
		# Use websockets.broadcast for efficient sending
		websockets.broadcast(clients, message)

async def ws_handler(websocket):
	"""Handle WebSocket connections."""
	clients.add(websocket)
	
	# Send current state to new client
	if state_getter:
		import json
		state = state_getter()
		for feature_id, feature_data in state.features.items():
			message = {
				'action': 'add',
				'id': feature_id,
				'type': feature_data['type'],
				'coords': feature_data['coords'][0] if feature_data['type'] == 'point' else feature_data['coords'],
				'params': feature_data['params']
			}
			await websocket.send(json.dumps(message))
	
	try:
		async for message in websocket:
			# Handle messages from client (e.g., error reports)
			try:
				import json
				import sys
				data = json.loads(message)
				if data.get('type') == 'error':
					# Print error to stderr
					print(f"Browser error: {data.get('message', 'Unknown error')}", file=sys.stderr)
			except Exception as e:
				# Ignore malformed messages
				pass
	finally:
		clients.remove(websocket)

def start_http_server(port):
	httpd = ThreadingHTTPServer(('0.0.0.0', port), StaticHandler)
	thread = threading.Thread(target=httpd.serve_forever, daemon=True)
	thread.start()
	return httpd


async def start_ws_server(port):
	ws_port = port + 1
	return await websockets.serve(ws_handler, '0.0.0.0', ws_port, process_request=None, ping_interval=None)

def start_server(port):
	start_http_server(port)
	asyncio.run(start_ws_server(port))
