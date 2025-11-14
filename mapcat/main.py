"""
Entry point for mapcat CLI.
"""

import argparse
import sys
import webbrowser
import asyncio
import json
from mapcat import server, parser
from mapcat.state import State
from mapcat.commands import COMMAND_HANDLERS

def parse_args():
	parser_arg = argparse.ArgumentParser(description="Mapcat CLI")
	parser_arg.add_argument("--port", type=int, default=8080, help="Port for HTTP/WebSocket server (default: 8080)")
	parser_arg.add_argument("--no-open", action="store_true", help="Do not auto-open browser")
	return parser_arg.parse_args()


async def stdin_broadcast_loop(is_tty, state):
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
			
			# Parse command
			parsed = parser.parse_command(line)
			if not parsed:
				if is_tty:
					print("< ERROR: Invalid command")
				continue  # Parser already logged error
			
			# Get handler
			handler = COMMAND_HANDLERS.get(parsed['cmd'])
			if not handler:
				_log_error(f"Unknown command: {parsed['cmd']}")
				if is_tty:
					print(f"< ERROR: Unknown command '{parsed['cmd']}'")
				continue
			
			# Execute handler
			message = handler(state, parsed)
			if message:
				# Broadcast to WebSocket clients
				await server.broadcast(json.dumps(message))
				
				# Echo response in REPL mode
				if is_tty:
					print(f"< OK {parsed['cmd']} id={message.get('id', 'N/A')}")
			else:
				if is_tty:
					print(f"< ERROR: Command failed")
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
	
	# Initialize state
	state = State()

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
			await stdin_broadcast_loop(is_tty, state)

	asyncio.run(runner())


def _log_error(message: str):
	"""Log error to stderr."""
	print(f"Main error: {message}", file=sys.stderr)


if __name__ == "__main__":
	main()
