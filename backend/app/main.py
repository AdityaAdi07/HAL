from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import master, workforce, tracking, capacity

app = FastAPI(title="HAL Manufacturing Digital Twin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master.router, prefix="/api")
app.include_router(workforce.router, prefix="/api/workforce")
app.include_router(tracking.router, prefix="/api/tracking")
app.include_router(capacity.router, prefix="/api/capacity")

@app.get("/health")
def health_check():
    return {"status": "ok"}
