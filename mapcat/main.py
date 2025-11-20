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

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

# Import readline for better REPL experience (arrow keys, history)
try:
	import readline
except ImportError:
	readline = None

def parse_args():
	parser_arg = argparse.ArgumentParser(description="Mapcat CLI")
	parser_arg.add_argument("--port", type=int, default=8080, help="Port for HTTP/WebSocket server (default: 8080)")
	parser_arg.add_argument("--no-open", action="store_true", help="Do not auto-open browser")
	parser_arg.add_argument("--verbose", action="store_true", help="Print OK messages for successful commands")
	return parser_arg.parse_args()


async def stdin_broadcast_loop(is_tty, state, verbose):
	"""
	Read stdin and broadcast lines.
	If is_tty, run in REPL mode with prompts.
	Otherwise, process piped input and exit when done.
	
	Args:
		is_tty: True if running in interactive TTY mode
		state: State instance
		verbose: True if OK messages should be printed
	"""
	loop = asyncio.get_event_loop()
	
	try:
		while True:
			# Read line
			if is_tty:
				# Use input() for interactive mode (supports readline)
				try:
					line = await loop.run_in_executor(None, input, "> ")
				except EOFError:
					print("\nExit")
					break
			else:
				# Use stdin.readline() for piped mode
				line = await loop.run_in_executor(None, sys.stdin.readline)
				if not line:
					break
			
			line = line.strip()
			
			# Skip empty lines
			if not line:
				continue
			
			# Parse command
			parsed = parser.parse_command(line)
			if not parsed:
				_log_error("parse", "Invalid command", line)
				if is_tty:
					print("< ERROR: Invalid command")
				continue  # Parser already logged error
			
			# Add original line to parsed command for error reporting
			parsed['_original_line'] = line
			
			# Get handler
			handler = COMMAND_HANDLERS.get(parsed['cmd'])
			if not handler:
				_log_error(parsed['cmd'], f"Unknown command", line)
				if is_tty:
					print(f"< ERROR: Unknown command '{parsed['cmd']}'")
				continue
			
			# Execute handler
			message = handler(state, parsed)
			if message:
				# Broadcast to WebSocket clients
				await server.broadcast(json.dumps(message))
				
				# Log success to stdout (if verbose)
				if verbose:
					_log_success(parsed['cmd'], line)
				
				# Echo response in REPL mode
				if is_tty:
					print(f"< OK {parsed['cmd']} id={message.get('id', 'N/A')}")
			elif parsed['cmd'] != 'help':
				# Handler returned None (failed) - error already logged by handler
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
	verbose = args.verbose
	
	# Detect if stdin is a TTY (interactive) or piped
	is_tty = sys.stdin.isatty()
	
	# Initialize state
	state = State()
	
	# Register state getter for new WebSocket connections
	server.set_state_getter(lambda: state)

	print(f"Starting Mapcat server on port {port}...")
	
	if is_tty:
		print("Running in REPL mode. Type commands or press Ctrl+C to exit.")
	else:
		print("Reading commands from stdin...")

	# Start HTTP server in background
	server.start_http_server(port)

	# Start WebSocket server and stdin loop
	async def runner():
		ws_server = await server.start_ws_server(port)
		async with ws_server:
			# In piped mode, delay browser opening to ensure server is ready
			if not is_tty and not no_open:
				await asyncio.sleep(0.5)
				url = f"http://localhost:{port}/"
				print(f"Opening browser at {url}")
				webbrowser.open(url)
			
			await stdin_broadcast_loop(is_tty, state, verbose)
			
			# Keep server running after stdin closes (for piped mode)
			if not is_tty:
				print("Commands processed. Server running. Press Ctrl+C to exit.")
				try:
					await asyncio.Future()  # Run forever
				except asyncio.CancelledError:
					pass

	# Open browser immediately in interactive mode
	if is_tty and not no_open:
		url = f"http://localhost:{port}/"
		print(f"Opening browser at {url}")
		webbrowser.open(url)

	asyncio.run(runner())


def _log_success(cmd: str, line: str):
    """
    Log success to stdout in green.
    
    Args:
        cmd: The command that succeeded
        line: Original command line
    """
    # Extract parameters (everything after command name)
    parts = line.split(None, 1)  # Split on first whitespace
    params = parts[1] if len(parts) > 1 else ""
    
    # Format: first 48 chars ... last 16 chars
    if len(params) > 64:
        params_preview = params[:48] + "..." + params[-16:]
    else:
        params_preview = params
    
    print(f"{GREEN}OK: {cmd} {params_preview}{RESET}")


def _log_error(cmd: str, message: str, line: str = ""):
    """
    Log error to stderr in red with formatted output.
    
    Args:
        cmd: The command that failed
        message: The error message
        line: Optional original command line
    """
    if line:
        # Extract parameters (everything after command name)
        parts = line.split(None, 1)  # Split on first whitespace
        params = parts[1] if len(parts) > 1 else ""
        
        # Format: first 48 chars ... last 16 chars
        if len(params) > 64:
            params_preview = params[:48] + "..." + params[-16:]
        else:
            params_preview = params
        
        print(f"{RED}FAIL: {cmd} {params_preview}{RESET}", file=sys.stderr)
    else:
        print(f"{RED}FAIL: {cmd}{RESET}", file=sys.stderr)
    print(f"{RED}FAIL: {message}{RESET}", file=sys.stderr)


if __name__ == "__main__":
	main()
