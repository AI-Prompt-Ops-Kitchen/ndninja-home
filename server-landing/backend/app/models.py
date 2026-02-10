from pydantic import BaseModel
from typing import Literal

class HealthStatus(BaseModel):
    status: Literal['healthy', 'degraded', 'unhealthy']
    uptime: float
    timestamp: str

class ServiceInfo(BaseModel):
    name: str
    url: str
    port: int
    description: str
    icon: str
    status: Literal['online', 'offline', 'unknown'] = 'unknown'
    response_time: float | None = None

class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    container_count: int
    uptime_seconds: float
