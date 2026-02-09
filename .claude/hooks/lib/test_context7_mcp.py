"""Tests for Context7 MCP client wrapper."""

import json
import time
import threading
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from context7_mcp import (
    Context7MCPClient, Context7Error, RateLimitError,
    TimeoutError, MCPProtocolError
)


class FakeMCPServer:
    """Simulates a Context7 MCP server for testing.

    Creates a pair of pipes to simulate subprocess stdin/stdout.
    Responds to JSON-RPC requests with canned responses.
    """

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.received = []
        self._request_handlers = {
            'initialize': self._handle_initialize,
            'tools/list': self._handle_tools_list,
            'tools/call': self._handle_tools_call,
        }

    def _handle_initialize(self, params):
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "context7-mcp", "version": "1.0.0"}
        }

    def _handle_tools_list(self, params):
        return {
            "tools": [
                {
                    "name": "resolve-library-id",
                    "description": "Resolve library name to Context7 ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"libraryName": {"type": "string"}},
                        "required": ["libraryName"]
                    }
                },
                {
                    "name": "get-library-docs",
                    "description": "Get documentation for a library",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "context7CompatibleLibraryID": {"type": "string"},
                            "topic": {"type": "string"},
                            "tokens": {"type": "integer"}
                        },
                        "required": ["context7CompatibleLibraryID"]
                    }
                }
            ]
        }

    def _handle_tools_call(self, params):
        tool_name = params.get('name', '')
        arguments = params.get('arguments', {})

        if tool_name == 'resolve-library-id':
            lib_name = arguments.get('libraryName', '')
            return {
                "content": [{
                    "type": "text",
                    "text": f"- `/upstash/{lib_name}` - {lib_name.title()} documentation\n"
                            f"- `/alt/{lib_name}-core` - {lib_name.title()} Core\n"
                }]
            }
        elif tool_name == 'get-library-docs':
            lib_id = arguments.get('context7CompatibleLibraryID', '')
            topic = arguments.get('topic', 'general')
            return {
                "content": [{
                    "type": "text",
                    "text": f"# Documentation for {lib_id}\n\n"
                            f"## Topic: {topic}\n\n"
                            f"This is the documentation content for testing.\n"
                }]
            }
        return {"content": []}

    def process_message(self, message):
        """Process a JSON-RPC message and return response."""
        self.received.append(message)

        method = message.get('method', '')
        params = message.get('params', {})
        req_id = message.get('id')

        # Notifications have no id
        if req_id is None:
            return None

        handler = self._request_handlers.get(method)
        if handler:
            result = handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        else:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }


@pytest.fixture
def fake_server():
    """Create a fake MCP server."""
    return FakeMCPServer()


@pytest.fixture
def mock_client(fake_server):
    """Create a Context7MCPClient with mocked subprocess.

    Instead of spawning npx, we intercept stdin/stdout with our fake server.
    """
    client = Context7MCPClient(timeout=5, max_queries=10)

    import io
    import queue as q

    # Create pipes for communication
    server_responses = q.Queue()
    stdin_buffer = io.StringIO()

    class FakeStdin:
        def write(self, data):
            stdin_buffer.write(data)
            # Parse and respond
            try:
                msg = json.loads(data.strip())
                response = fake_server.process_message(msg)
                if response:
                    server_responses.put(json.dumps(response) + '\n')
            except json.JSONDecodeError:
                pass

        def flush(self):
            pass

        def close(self):
            pass

    class FakeStdout:
        def readline(self):
            try:
                return server_responses.get(timeout=2)
            except q.Empty:
                return ''

    class FakeProcess:
        stdin = FakeStdin()
        stdout = FakeStdout()
        stderr = io.StringIO()
        pid = 12345

        def poll(self):
            return None  # Process is running

        def terminate(self):
            pass

        def wait(self, timeout=None):
            pass

        def kill(self):
            pass

    # Patch subprocess.Popen to return our fake process
    with patch('context7_mcp.subprocess.Popen', return_value=FakeProcess()):
        client.connect()
        yield client

    client.close()


class TestContext7MCPClient:
    """Tests for Context7MCPClient."""

    def test_connect(self, mock_client):
        """Client connects and initializes successfully."""
        assert mock_client.connected

    def test_discover_tools(self, mock_client):
        """Client discovers available tools."""
        tools = mock_client.discover_tools()
        assert 'resolve-library-id' in tools
        assert 'get-library-docs' in tools
        assert len(tools) == 2

    def test_resolve_library_id(self, mock_client):
        """Library name resolves to a Context7 ID."""
        lib_id = mock_client.resolve_library_id("fastapi")
        assert lib_id is not None
        assert '/' in lib_id
        assert 'fastapi' in lib_id.lower()

    def test_query_docs(self, mock_client):
        """Documentation is returned for a library ID."""
        docs = mock_client.query_docs("/upstash/fastapi", topic="routing")
        assert docs is not None
        assert 'content' in docs
        assert 'text' in docs['content']
        assert len(docs['content']['text']) > 0

    def test_rate_limiting(self, mock_client):
        """Rate limit enforced after max_queries."""
        # Use up all queries
        for i in range(10):
            mock_client.resolve_library_id(f"lib-{i}")

        # Next query should raise
        with pytest.raises(RateLimitError):
            mock_client.resolve_library_id("one-too-many")

    def test_queries_remaining(self, mock_client):
        """queries_remaining tracks usage."""
        assert mock_client.queries_remaining == 10
        mock_client.resolve_library_id("fastapi")
        assert mock_client.queries_remaining == 9

    def test_context_manager(self, fake_server):
        """Client works as context manager."""
        with patch('context7_mcp.subprocess.Popen') as mock_popen:
            import io
            import queue as q

            server_responses = q.Queue()

            class FakeStdin:
                def write(self, data):
                    try:
                        msg = json.loads(data.strip())
                        response = fake_server.process_message(msg)
                        if response:
                            server_responses.put(json.dumps(response) + '\n')
                    except json.JSONDecodeError:
                        pass
                def flush(self): pass
                def close(self): pass

            class FakeStdout:
                def readline(self):
                    try:
                        return server_responses.get(timeout=2)
                    except q.Empty:
                        return ''

            class FakeProcess:
                stdin = FakeStdin()
                stdout = FakeStdout()
                stderr = io.StringIO()
                pid = 12345
                def poll(self): return None
                def terminate(self): pass
                def wait(self, timeout=None): pass
                def kill(self): pass

            mock_popen.return_value = FakeProcess()

            with Context7MCPClient(timeout=5) as client:
                assert client.connected
                lib_id = client.resolve_library_id("react")
                assert lib_id is not None


class TestParseLibraryId:
    """Tests for _parse_library_id static method."""

    def test_parse_standard_format(self):
        text = "- `/upstash/fastapi` - FastAPI documentation\n- `/alt/fastapi-core` - Core"
        result = Context7MCPClient._parse_library_id(text, "fastapi")
        assert result == "/upstash/fastapi"

    def test_parse_no_match(self):
        text = "No libraries found matching your query."
        result = Context7MCPClient._parse_library_id(text, "nonexistent")
        assert result is None

    def test_parse_multiple_results(self):
        text = ("- `/facebook/react` - React documentation\n"
                "- `/facebook/react-native` - React Native\n")
        result = Context7MCPClient._parse_library_id(text, "react")
        assert result == "/facebook/react"

    def test_parse_with_backticks(self):
        text = "`/tiangolo/fastapi` FastAPI framework"
        result = Context7MCPClient._parse_library_id(text, "fastapi")
        assert result == "/tiangolo/fastapi"


class TestFetchAndCache:
    """Tests for fetch_and_cache integration."""

    def test_fetch_and_cache_success(self, mock_client):
        """fetch_and_cache resolves, queries, and caches."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True

        result = mock_client.fetch_and_cache(
            library="fastapi",
            version="0",
            intent="general",
            cache_manager=mock_cache
        )

        assert result['success'] is True
        assert result['source'] == 'api'
        assert result['library_id'] is not None
        assert result['time_ms'] >= 0
        mock_cache.set.assert_called_once()

    def test_fetch_and_cache_resolve_failure(self, mock_client, fake_server):
        """fetch_and_cache handles resolution failure."""
        # Override the handler in the dispatch dict directly
        original = fake_server._request_handlers['tools/call']
        def fail_resolve(params):
            tool_name = params.get('name', '')
            arguments = params.get('arguments', {})
            if tool_name == 'resolve-library-id':
                return {"content": [{"type": "text", "text": "No results found."}]}
            return fake_server._handle_tools_call(params)
        fake_server._request_handlers['tools/call'] = fail_resolve

        mock_cache = MagicMock()
        result = mock_client.fetch_and_cache(
            library="nonexistent-lib-xyz",
            version="1",
            intent="general",
            cache_manager=mock_cache
        )

        assert result['success'] is False
        assert result['source'] == 'resolve_failed'
        mock_cache.set.assert_not_called()

        # Restore original handler
        fake_server._request_handlers['tools/call'] = original
