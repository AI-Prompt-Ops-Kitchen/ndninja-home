---
name: realtime-transport
description: Architectural guidance for choosing real-time transport (SSE vs WebSockets)
version: 1.0.0
category: architecture
args: ["[--use-case]", "[--requirements]"]
when_to_use: "User needs to implement real-time features (live updates, streaming, notifications). Use when designing APIs, dashboards, or any system requiring server-to-client push."
tags: [architecture, real-time, sse, websockets, streaming, api-design]
examples:
  - /realtime-transport --use-case "progress updates"
  - /realtime-transport --use-case "chat application"
  - /realtime-transport --requirements "unidirectional,simple,http"
reflection_count: 0
---

# Real-Time Transport Selection

**Purpose:** Guide architectural decisions for real-time communication between server and client. Prevents over-engineering by matching transport mechanism to actual requirements.

## Quick Decision Tree

```
Need bidirectional communication (client ↔ server)?
├─ YES → WebSockets
└─ NO → Server-Sent Events (SSE)

Need complex protocols or binary data?
├─ YES → WebSockets
└─ NO → SSE (text/JSON is fine)

Have strict firewall/proxy requirements?
├─ YES → SSE (works through standard HTTP/HTTPS)
└─ NO → Either works

Want simplest possible implementation?
└─ SSE (built into browsers, no special libraries needed)
```

## Server-Sent Events (SSE)

### When to Use SSE

✅ **Perfect for:**
- Progress updates (builds, deployments, long-running tasks)
- Live dashboards (metrics, logs, monitoring)
- Notifications/alerts (unidirectional push)
- Activity feeds (social updates, news streams)
- Server logs streaming
- Real-time data visualization
- Any scenario where server → client is primary flow

✅ **Advantages:**
- **Simplicity:** Built into browsers via `EventSource` API
- **HTTP-friendly:** Works through firewalls, proxies, load balancers
- **Auto-reconnect:** Browser handles reconnection automatically
- **Text-based:** Easy to debug (can curl and see events)
- **No special libraries:** Just HTTP endpoints
- **Lightweight:** Lower overhead than WebSockets for one-way communication

### SSE Implementation Pattern

**Backend (FastAPI example):**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI()

async def event_generator():
    """Generate SSE events"""
    while True:
        # Your data source here
        data = {"status": "running", "progress": 45}

        # SSE format: "data: {json}\n\n"
        yield f"data: {json.dumps(data)}\n\n"

        await asyncio.sleep(1)

@app.get("/stream")
async def stream_events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Frontend (JavaScript):**
```javascript
const eventSource = new EventSource('/stream');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    // Update UI here
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    // Browser will auto-reconnect
};

// Close when done
eventSource.close();
```

### SSE Limitations

❌ **Not suitable for:**
- Bidirectional communication (client needs to send messages to server)
- Binary data (SSE is text-only)
- Very high frequency updates (>100 messages/sec per client)
- Complex protocols (game state synchronization, etc.)
- Internet Explorer support (IE doesn't support EventSource)

## WebSockets

### When to Use WebSockets

✅ **Perfect for:**
- Chat applications (bidirectional messaging)
- Multiplayer games (low-latency state sync)
- Collaborative editing (Google Docs-style)
- Trading platforms (high-frequency updates + commands)
- Remote control interfaces (IoT, robotics)
- Video conferencing signaling
- Any scenario requiring client ↔ server communication

✅ **Advantages:**
- **Bidirectional:** Full duplex communication
- **Low latency:** Direct TCP connection (no HTTP overhead after handshake)
- **Binary support:** Can send binary data efficiently
- **Custom protocols:** Build any protocol on top of WebSocket frames
- **High frequency:** Handles thousands of messages/second

### WebSocket Implementation Pattern

**Backend (FastAPI example):**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive from client
            data = await websocket.receive_text()

            # Process and respond
            response = {"echo": data}
            await websocket.send_json(response)

    except WebSocketDisconnect:
        print("Client disconnected")
```

**Frontend (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected');
    ws.send(JSON.stringify({message: 'Hello'}));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected');
    // Need to implement reconnection manually
};
```

### WebSocket Limitations

❌ **Challenges:**
- **More complex:** Requires WebSocket libraries/frameworks
- **Reconnection:** Must implement reconnection logic manually
- **Proxy issues:** Some proxies/firewalls block WebSocket connections
- **Resource intensive:** Maintains persistent TCP connections
- **Debugging harder:** Binary protocol, can't just curl it

## Real-World Examples

### Example 1: Build Progress (SSE)

**Use case:** Show real-time build progress for CI/CD pipeline

**Why SSE:**
- Unidirectional (server → client only)
- Simple JSON messages
- Auto-reconnect if network hiccups
- Works through corporate firewalls

**Implementation:**
```python
# From Kage Bunshin no Jutsu project
async def stream_task_updates(task_id: str):
    async for update in task_manager.watch(task_id):
        yield f"data: {json.dumps({
            'task_id': task_id,
            'status': update.status,
            'output': update.output,
            'timestamp': update.timestamp.isoformat()
        })}\n\n"
```

### Example 2: Chat Application (WebSockets)

**Use case:** Real-time chat with typing indicators

**Why WebSockets:**
- Bidirectional (users send and receive messages)
- Low latency for instant feel
- Typing indicators need client → server events
- Presence tracking (who's online)

**Not suitable for SSE because:** Client needs to send frequent updates (typing status, read receipts) without separate HTTP requests.

### Example 3: Live Dashboard (SSE)

**Use case:** System monitoring dashboard with metrics

**Why SSE:**
- Server pushes metrics every second
- Client just displays data (no interaction needed)
- Simple to implement and maintain
- Easy to add authentication (just HTTP headers)

**Implementation:**
```python
@app.get("/metrics/stream")
async def stream_metrics():
    async def generate():
        while True:
            metrics = await get_system_metrics()
            yield f"data: {json.dumps(metrics)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Decision Matrix

| Requirement | SSE | WebSockets |
|------------|-----|------------|
| Server → Client only | ✅ Perfect | ⚠️ Overkill |
| Client → Server frequent | ❌ No | ✅ Yes |
| Simple implementation | ✅ Very | ⚠️ Moderate |
| Works through proxies | ✅ Always | ⚠️ Sometimes |
| Auto-reconnect | ✅ Built-in | ❌ Manual |
| Binary data | ❌ No | ✅ Yes |
| Low latency | ✅ Good | ✅ Excellent |
| Browser support | ✅ Modern | ✅ All |
| Debugging | ✅ Easy | ⚠️ Harder |
| Resource usage | ✅ Low | ⚠️ Higher |

## Architecture Patterns

### Pattern 1: SSE for Updates + REST for Commands

**Best of both worlds:**
- SSE for real-time updates (server → client)
- Regular HTTP POST/PUT for commands (client → server)

**Example:**
```javascript
// Listen for updates via SSE
const updates = new EventSource('/api/tasks/stream');
updates.onmessage = (event) => {
    updateUI(JSON.parse(event.data));
};

// Send commands via REST
async function startTask(taskData) {
    await fetch('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(taskData)
    });
}
```

**When to use:**
- Most real-time dashboards
- Progress tracking UIs
- Notification systems
- Any system where commands are infrequent vs. updates

### Pattern 2: WebSockets for Full Duplex

**Use when:**
- Commands and updates are equally frequent
- Need instant bidirectional communication
- Building interactive experiences (games, collaboration)

### Pattern 3: Hybrid Approach

**Example:** Video conferencing
- WebSockets for signaling (connection setup, control)
- WebRTC for actual media (audio/video)
- SSE for presence updates (who joined/left)

## Performance Considerations

### SSE Scaling

**Connection limits:**
- Browsers limit to 6 SSE connections per domain
- Use single connection with multiplexed events

**Example of event multiplexing:**
```javascript
// Server sends events with IDs
yield f"event: task_update\ndata: {json.dumps(data)}\n\n"
yield f"event: notification\ndata: {json.dumps(notif)}\n\n"

// Client handles by event type
eventSource.addEventListener('task_update', (e) => {...});
eventSource.addEventListener('notification', (e) => {...});
```

### WebSocket Scaling

**Connection overhead:**
- Each WebSocket = persistent TCP connection
- 10,000 clients = 10,000 open connections
- Need proper load balancing and scaling strategy

**Scaling solutions:**
- Redis pub/sub for multi-server coordination
- Dedicated WebSocket servers (separate from API)
- Connection pooling and limits

## AuDHD-Friendly Features

**Reduces Decision Paralysis:**
- Clear decision tree at the top
- Binary choices (not infinite options)
- Real-world examples show concrete applications

**Executive Function Support:**
- Decision matrix provides structure
- Patterns are pre-validated (don't need to research)
- Copy-paste ready code examples

**Hyperfocus Accommodation:**
- Can deep-dive into either technology
- Comparison table prevents "which is better?" rabbit holes
- Limitations section prevents over-engineering

## Common Mistakes to Avoid

### ❌ Mistake 1: Using WebSockets for One-Way Data
```javascript
// DON'T: WebSocket just for server → client
ws.onmessage = (event) => {
    updateDashboard(event.data);
};
// Never send anything to server

// DO: Use SSE instead
const es = new EventSource('/dashboard/stream');
es.onmessage = (event) => {
    updateDashboard(event.data);
};
```

### ❌ Mistake 2: Using SSE for Bidirectional Chat
```javascript
// DON'T: SSE + polling for fake bidirectional
const updates = new EventSource('/chat/stream');
setInterval(() => {
    fetch('/chat/send', {method: 'POST', body: message});
}, 100); // Polling is wasteful

// DO: Use WebSockets for true bidirectional
const ws = new WebSocket('ws://localhost/chat');
```

### ❌ Mistake 3: Not Handling Reconnection
```javascript
// DON'T: Assume connection never drops
const ws = new WebSocket('ws://localhost/stream');
// No reconnection logic

// DO: Implement reconnection for WebSockets
function connectWebSocket() {
    const ws = new WebSocket('ws://localhost/stream');
    ws.onclose = () => {
        setTimeout(connectWebSocket, 1000);
    };
    return ws;
}

// Or just use SSE which reconnects automatically
```

## Integration with Other Skills

**Works well with:**
- `/api-design` - Choose transport as part of API architecture
- `/debug-zombies` - Debug hanging connections
- `/db-health-check` - Stream database metrics

## Success Criteria

A good transport choice should:
1. ✅ Match actual requirements (not over-engineered)
2. ✅ Work reliably through network infrastructure
3. ✅ Be maintainable by team (simpler is better)
4. ✅ Scale appropriately for expected load
5. ✅ Debug easily when issues occur

## Version History

- v1.0.0 (2026-01-05): Initial release from Kage Bunshin reflection
  - Captured SSE preference pattern from Week 3 implementation
  - Decision tree and comparison matrix
  - Real-world examples from production code

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-05 - Pattern
**Signal:** "Used SSE instead of WebSockets for simpler real-time updates"
**What Changed:** Preference for Server-Sent Events over WebSockets when simplicity and unidirectional flow are prioritized
**Confidence:** Medium
**Source:** kage-bunshin-week3-implementation-2026-01-04
**Rationale:** This represents an architectural decision pattern that should be reused in future real-time implementations to avoid over-engineering
