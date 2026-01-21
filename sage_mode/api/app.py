from fastapi import FastAPI
from sage_mode.api.decision_journal_routes import router as decision_router

app = FastAPI(title="Sage Mode API")

app.include_router(decision_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Sage Mode API"}
