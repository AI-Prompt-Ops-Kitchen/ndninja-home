from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sage_mode.routes.auth_routes import router as auth_router
from sage_mode.routes.team_routes import router as team_router
from sage_mode.routes.session_routes import router as session_router
from sage_mode.routes.dashboard_routes import router as dashboard_router
from sage_mode.routes.websocket_routes import router as websocket_router

app = FastAPI(title="Sage Mode", description="Development Team Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(team_router)
app.include_router(session_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "3.0"}
