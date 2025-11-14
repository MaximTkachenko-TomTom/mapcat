
"""
WebSocket and HTTP server for mapcat.
"""
import asyncio
import websockets
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

class StaticHandler(SimpleHTTPRequestHandler):
	def translate_path(self, path):
		# Serve files from static directory
		relpath = path.lstrip('/')
		fullpath = os.path.join(STATIC_DIR, relpath)
		if os.path.isdir(fullpath):
			return os.path.join(fullpath, 'index.html')
		return fullpath if os.path.exists(fullpath) else os.path.join(STATIC_DIR, 'index.html')


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
			# Client sent a message (currently not used, but kept for future)
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
