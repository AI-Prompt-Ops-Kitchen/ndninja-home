# .claude/hooks/lib/context7_mcp.py
"""
Context7 MCP client wrapper.

Communicates with the @upstash/context7-mcp server via JSON-RPC 2.0 over stdio.
Provides library resolution, documentation fetching, rate limiting, and timeout protection.
"""

import subprocess
import json
import logging
import time
import threading
import queue
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class Context7Error(Exception):
    """Base exception for Context7 MCP errors."""
    pass


class RateLimitError(Context7Error):
    """Raised when query limit is exceeded."""
    pass


class TimeoutError(Context7Error):
    """Raised when MCP operation times out."""
    pass


class MCPProtocolError(Context7Error):
    """Raised when MCP protocol communication fails."""
    pass


class Context7MCPClient:
    """Client for the Context7 MCP server (@upstash/context7-mcp).

    Spawns the MCP server as a subprocess and communicates via JSON-RPC 2.0
    over stdio. Provides rate limiting and timeout protection.

    Usage:
        client = Context7MCPClient(timeout=30, max_queries=10)
        client.connect()
        lib_id = client.resolve_library_id("fastapi")
        docs = client.query_docs(lib_id, topic="routing")
        client.close()
    """

    def __init__(self, timeout: int = 30, max_queries: int = 10):
        self._timeout = timeout
        self._max_queries = max_queries
        self._query_count = 0
        self._request_id = 0
        self._process = None
        self._tools: Dict[str, dict] = {}
        self._reader_thread = None
        self._response_queue: queue.Queue = queue.Queue()
        self._running = False

    @property
    def query_count(self) -> int:
        return self._query_count

    @property
    def queries_remaining(self) -> int:
        return max(0, self._max_queries - self._query_count)

    @property
    def connected(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def connect(self) -> bool:
        """Spawn MCP server and perform initialize handshake.

        Returns True if connection succeeded.
        """
        try:
            self._process = subprocess.Popen(
                ['npx', '-y', '@upstash/context7-mcp'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Start reader thread for stdout
            self._running = True
            self._reader_thread = threading.Thread(
                target=self._reader_loop, daemon=True
            )
            self._reader_thread.start()

            # MCP initialize handshake
            response = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "context7-preloader",
                    "version": "1.0.0"
                }
            })

            if response is None:
                raise MCPProtocolError("No response to initialize request")

            if 'error' in response:
                raise MCPProtocolError(f"Initialize error: {response['error']}")

            # Send initialized notification (no response expected)
            self._send_notification("notifications/initialized")

            logger.info("Context7 MCP server connected")
            return True

        except FileNotFoundError:
            logger.error("npx not found — is Node.js installed?")
            self.close()
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Context7 MCP: {e}")
            self.close()
            return False

    def discover_tools(self) -> Dict[str, dict]:
        """List available tools from the MCP server.

        Returns dict of {tool_name: tool_schema}.
        """
        response = self._send_request("tools/list", {})
        if response and 'result' in response:
            tools = response['result'].get('tools', [])
            self._tools = {t['name']: t for t in tools}
            logger.info(f"Discovered {len(self._tools)} tools: {list(self._tools.keys())}")
        return self._tools

    def resolve_library_id(self, library_name: str) -> Optional[str]:
        """Resolve a library name to a Context7 library ID.

        Args:
            library_name: Human-readable library name (e.g. "fastapi", "react")

        Returns:
            Context7 library ID string, or None if resolution failed.
        """
        self._check_rate_limit()

        response = self._send_request("tools/call", {
            "name": "resolve-library-id",
            "arguments": {"libraryName": library_name}
        })

        if response is None:
            logger.warning(f"No response for resolve-library-id({library_name})")
            return None

        if 'error' in response:
            logger.warning(f"resolve-library-id error: {response['error']}")
            return None

        result = response.get('result', {})
        content = result.get('content', [])

        # Extract library ID from response content
        for item in content:
            if item.get('type') == 'text':
                text = item.get('text', '')
                # Parse the text response to find the library ID
                # Context7 returns a formatted list; extract the first match
                library_id = self._parse_library_id(text, library_name)
                if library_id:
                    return library_id

        logger.warning(f"Could not resolve library ID for: {library_name}")
        return None

    def query_docs(self, library_id: str, topic: str = '',
                   tokens: int = 5000) -> Optional[Dict[str, Any]]:
        """Query documentation for a resolved library.

        Args:
            library_id: Context7 library ID (from resolve_library_id)
            topic: Optional topic filter (e.g. "routing", "authentication")
            tokens: Max tokens to return (default 5000)

        Returns:
            Dict with 'content' and 'citations' keys, or None on failure.
        """
        self._check_rate_limit()

        args = {
            "context7CompatibleLibraryID": library_id,
            "tokens": tokens,
        }
        if topic:
            args["topic"] = topic

        response = self._send_request("tools/call", {
            "name": "get-library-docs",
            "arguments": args
        })

        if response is None:
            logger.warning(f"No response for query-docs({library_id})")
            return None

        if 'error' in response:
            logger.warning(f"query-docs error: {response['error']}")
            return None

        result = response.get('result', {})
        content = result.get('content', [])

        # Build structured response
        doc_text = ''
        citations = []
        for item in content:
            if item.get('type') == 'text':
                doc_text += item.get('text', '')

        if not doc_text:
            logger.warning(f"Empty documentation for {library_id}")
            return None

        return {
            'content': {'text': doc_text, 'tokens': tokens},
            'citations': citations if citations else None
        }

    def fetch_and_cache(self, library: str, version: str,
                        intent: str, cache_manager) -> Dict[str, Any]:
        """Resolve library, fetch docs, and store in cache.

        This is the main integration point used by the preloader and /load-docs.

        Args:
            library: Library name (e.g. "fastapi")
            version: Major version string (e.g. "0", "latest")
            intent: Query intent (e.g. "general", "routing")
            cache_manager: CacheManager instance

        Returns:
            Dict with 'success', 'source', 'time_ms', 'library_id' keys.
        """
        from context7_fingerprint import generate_fingerprint

        start = time.monotonic()
        fingerprint = generate_fingerprint(library, version, intent)

        result = {
            'library': library,
            'version': version,
            'intent': intent,
            'source': 'miss',
            'success': False,
            'time_ms': 0,
            'library_id': None,
        }

        # Step 1: Resolve library ID
        library_id = self.resolve_library_id(library)
        if not library_id:
            result['time_ms'] = int((time.monotonic() - start) * 1000)
            result['source'] = 'resolve_failed'
            return result

        result['library_id'] = library_id

        # Step 2: Query docs
        docs = self.query_docs(library_id, topic=intent)
        if not docs:
            result['time_ms'] = int((time.monotonic() - start) * 1000)
            result['source'] = 'query_failed'
            return result

        # Step 3: Store in cache
        cache_manager.set(
            fingerprint=fingerprint,
            library_id=library_id,
            library_version=version,
            query_intent=intent,
            content=docs['content'],
            citations=docs.get('citations')
        )

        result['source'] = 'api'
        result['success'] = True
        result['time_ms'] = int((time.monotonic() - start) * 1000)

        logger.info(f"Fetched and cached {library}-{version}:{intent} "
                     f"({result['time_ms']}ms)")
        return result

    def close(self):
        """Shutdown the MCP server process."""
        self._running = False
        if self._process:
            try:
                self._process.stdin.close()
            except Exception:
                pass
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
            logger.info("Context7 MCP server disconnected")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # --- Internal methods ---

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _send_request(self, method: str, params: dict) -> Optional[dict]:
        """Send JSON-RPC request and wait for response."""
        if not self.connected:
            raise MCPProtocolError("Not connected")

        req_id = self._next_id()
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }

        try:
            self._process.stdin.write(json.dumps(message) + '\n')
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise MCPProtocolError(f"Failed to send request: {e}")

        # Wait for matching response
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            try:
                remaining = max(0.1, deadline - time.monotonic())
                response = self._response_queue.get(timeout=remaining)
                if response.get('id') == req_id:
                    return response
                # Put back non-matching responses (shouldn't happen in practice)
                self._response_queue.put(response)
            except queue.Empty:
                break

        raise TimeoutError(f"Timeout waiting for response to {method} (id={req_id})")

    def _send_notification(self, method: str, params: Optional[dict] = None):
        """Send JSON-RPC notification (no response expected)."""
        if not self.connected:
            return

        message = {"jsonrpc": "2.0", "method": method}
        if params:
            message["params"] = params

        try:
            self._process.stdin.write(json.dumps(message) + '\n')
            self._process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def _reader_loop(self):
        """Background thread: read JSON-RPC responses from stdout."""
        while self._running and self._process and self._process.poll() is None:
            try:
                line = self._process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line or not line.startswith('{'):
                    continue  # Skip non-JSON lines (npx output, etc.)
                msg = json.loads(line)
                if 'id' in msg:
                    self._response_queue.put(msg)
                # Notifications (no id) are silently discarded
            except json.JSONDecodeError:
                continue
            except Exception:
                break

    def _check_rate_limit(self):
        """Enforce per-session query limit."""
        if self._query_count >= self._max_queries:
            raise RateLimitError(
                f"Query limit reached ({self._max_queries}). "
                f"Create a new client to reset."
            )
        self._query_count += 1

    @staticmethod
    def _parse_library_id(text: str, library_name: str) -> Optional[str]:
        """Extract best-matching library ID from resolve-library-id response.

        The response is typically a formatted list of library IDs.
        We pick the first one that looks like a valid Context7 library path.
        """
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            # Context7 library IDs look like: /org/repo or similar paths
            if '/' in line and library_name.lower() in line.lower():
                # Extract the ID portion (usually starts with /)
                parts = line.split()
                for part in parts:
                    part = part.strip('`').strip('*').strip('-').strip()
                    if part.startswith('/') and len(part) > 2:
                        return part
        # Fallback: just use the first line that has a /
        for line in lines:
            line = line.strip()
            parts = line.split()
            for part in parts:
                part = part.strip('`').strip('*').strip('-').strip()
                if part.startswith('/') and len(part) > 2:
                    return part
        return None
