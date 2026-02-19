#!/usr/bin/env python3
"""
Local URL shortener server
Redirects short codes to full URLs — handles private/Tailscale IPs
that public shorteners can't touch.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

SHORTCUTS_FILE = os.path.expanduser("~/.url-shortcuts.json")
PORT = 8999
HOST = "0.0.0.0"  # Bind to all interfaces so Tailscale can reach it


def load_shortcuts():
    if not os.path.exists(SHORTCUTS_FILE):
        return {}
    with open(SHORTCUTS_FILE) as f:
        return json.load(f)


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = self.path.lstrip("/")

        if not code:
            shortcuts = load_shortcuts()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"NDN URL Shortener — {len(shortcuts)} active shortcuts\n".encode())
            return

        shortcuts = load_shortcuts()

        if code in shortcuts:
            target = shortcuts[code]
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Unknown code: {code}\n".encode())

    def log_message(self, format, *args):
        pass  # Keep output clean


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), RedirectHandler)
    print(f"NDN URL Shortener running on port {PORT}", flush=True)
    server.serve_forever()
