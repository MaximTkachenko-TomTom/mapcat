
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

async def broadcast(message):
	# Broadcast message to all connected clients
	for client in clients:
		if client.open:
			await client.send(message)

async def ws_handler(websocket, path):
	clients.add(websocket)
	try:
		async for message in websocket:
			# Echo received message to all clients (for now)
			for client in clients:
				if client.open:
					await client.send(message)
	finally:
		clients.remove(websocket)

def start_http_server(port):
	httpd = ThreadingHTTPServer(('0.0.0.0', port), StaticHandler)
	thread = threading.Thread(target=httpd.serve_forever, daemon=True)
	thread.start()
	return httpd


async def start_ws_server(port):
	ws_port = port + 1
	async with websockets.serve(ws_handler, '0.0.0.0', ws_port, process_request=None, ping_interval=None):
		await asyncio.Future()  # run forever

def start_server(port):
	start_http_server(port)
	asyncio.run(start_ws_server(port))
