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

def main():
	args = parse_args()
	port = args.port
	no_open = args.no_open

	# Start the server (placeholder, actual implementation in server.py)
	print(f"Starting Mapcat server on port {port}...")
	# This should start the server asynchronously, but for now, just a placeholder
	# server.start_server(port)

	if not no_open:
		url = f"http://localhost:{port}/"
		print(f"Opening browser at {url}")
		webbrowser.open(url)

if __name__ == "__main__":
	main()
