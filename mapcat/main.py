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
import os

async def stdin_broadcast_loop(is_tty):
	"""
	Read stdin and broadcast lines.
	If is_tty, run in REPL mode with prompts.
	Otherwise, process piped input and exit when done.
	"""
	loop = asyncio.get_event_loop()
	
	try:
		while True:
			# Show prompt in REPL mode
			if is_tty:
				await loop.run_in_executor(None, lambda: sys.stdout.write("> "))
				await loop.run_in_executor(None, sys.stdout.flush)
			
			# Read line
			line = await loop.run_in_executor(None, sys.stdin.readline)
			
			# EOF or closed pipe
			if not line:
				if is_tty:
					print("\nExit")
				break
			
			line = line.strip()
			
			# Skip empty lines
			if not line:
				continue
			
			# Broadcast command
			await server.broadcast(line)
			
			# Echo response in REPL mode
			if is_tty:
				print(f"< OK {line}")
	except KeyboardInterrupt:
		if is_tty:
			print("\nExit")
		sys.exit(0)

def main():
	args = parse_args()
	port = args.port
	no_open = args.no_open
	
	# Detect if stdin is a TTY (interactive) or piped
	is_tty = sys.stdin.isatty()

	print(f"Starting Mapcat server on port {port}...")
	
	if is_tty:
		print("Running in REPL mode. Type commands or press Ctrl+C to exit.")
	else:
		print("Reading commands from stdin...")

	# Start HTTP server in background
	server.start_http_server(port)

	if not no_open:
		url = f"http://localhost:{port}/"
		print(f"Opening browser at {url}")
		webbrowser.open(url)



	# Start WebSocket server and stdin loop
	async def runner():
		ws_server = await server.start_ws_server(port)
		async with ws_server:
			await stdin_broadcast_loop(is_tty)

	asyncio.run(runner())

if __name__ == "__main__":
	main()
