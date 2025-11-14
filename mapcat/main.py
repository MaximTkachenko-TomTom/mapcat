"""
Entry point for mapcat CLI.
"""

import argparse
import sys
import webbrowser
from mapcat import server

def parse_args():
	parser = argparse.ArgumentParser(description="Mapcat CLI")
	parser.add_argument("--port", type=int, default=8080, help="Port for HTTP/WebSocket server (default: 8080)")
	parser.add_argument("--no-open", action="store_true", help="Do not auto-open browser")
	return parser.parse_args()


import asyncio

async def stdin_broadcast_loop():
	while True:
		line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
		if not line:
			break
		line = line.strip()
		if line:
			await server.broadcast(line)

def main():
	args = parse_args()
	port = args.port
	no_open = args.no_open

	print(f"Starting Mapcat server on port {port}...")

	# Start HTTP server in background
	server.start_http_server(port)

	if not no_open:
		url = f"http://localhost:{port}/"
		print(f"Opening browser at {url}")
		webbrowser.open(url)

	# Start WebSocket server and stdin loop
	async def runner():
		ws_task = asyncio.create_task(server.start_ws_server(port))
		stdin_task = asyncio.create_task(stdin_broadcast_loop())
		await asyncio.gather(ws_task, stdin_task)

	asyncio.run(runner())

if __name__ == "__main__":
	main()
