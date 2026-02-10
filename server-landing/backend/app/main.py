from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import asyncio
import json
import sys
from typing import List
from .models import HealthStatus, SystemMetrics
from .services import get_all_services_status, load_services_config
from .system import get_system_metrics
from .validators import LocalhostDetectionError

app = FastAPI(
    title="Server Landing Backend API",
    description="Backend API for server landing page monitoring",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def validate_configuration():
    """Validate configuration on startup to ensure no localhost URLs."""
    try:
        services = load_services_config()
        print(f"✓ Configuration validated: {len(services)} services loaded")
    except LocalhostDetectionError as e:
        print("\n" + "="*80)
        print(str(e))
        print("="*80 + "\n")
        print("Application startup ABORTED due to configuration error.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during configuration validation: {e}")
        sys.exit(1)

# Store app start time
_app_start_time = time.time()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Server Landing Backend API",
        "version": "1.0.0",
        "endpoints": ["/health", "/services", "/system"]
    }

@app.get("/health", response_model=HealthStatus)
async def get_health():
    """Get health check status."""
    uptime = time.time() - _app_start_time

    # Simple health check - could be enhanced with actual service checks
    status = 'healthy'

    return HealthStatus(
        status=status,
        uptime=round(uptime, 2),
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/services")
async def get_services():
    """Get status of all configured services."""
    services = await get_all_services_status()
    return services

@app.get("/system", response_model=SystemMetrics)
async def get_system():
    """Get system metrics (CPU, memory, disk, containers)."""
    metrics = get_system_metrics()
    return metrics

@app.websocket("/ws/services")
async def websocket_services(websocket: WebSocket):
    """
    WebSocket endpoint for real-time service status updates.
    Sends service status updates every 5 seconds.
    """
    await manager.connect(websocket)

    try:
        # Send initial status immediately
        print("WebSocket: Fetching service status...")
        services = await get_all_services_status()
        print(f"WebSocket: Got {len(services)} services")
        metrics = get_system_metrics()
        print(f"WebSocket: Got metrics")

        message_data = {
            "type": "update",
            "services": [service.model_dump() for service in services],
            "metrics": metrics.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"WebSocket: Sending initial message...")
        await websocket.send_json(message_data)
        print("WebSocket: Initial message sent successfully")

        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for 5 seconds
                await asyncio.sleep(5)

                # Get fresh data
                services = await get_all_services_status()
                metrics = get_system_metrics()

                # Send update
                await websocket.send_json({
                    "type": "update",
                    "services": [service.model_dump() for service in services],
                    "metrics": metrics.model_dump(),
                    "timestamp": datetime.utcnow().isoformat()
                })

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error in WebSocket loop: {e}")
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
