import sys
from pathlib import Path

# Ensure backend root directory is in sys.path for cloud host deployments
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.responses import JSONResponse
from app.api.phase1 import Phase1APIError, router as phase1_router
from app.api.phase2 import router as phase2_router
from app.api.synthetic import router as synthetic_router
from app.config import DETECTION_PROCESSED_DIR, STATIC_DIR, UPLOAD_DIR

app = FastAPI(
    title="CROWD-SHIELD API",
    description="Context-Aware Predictive Crowd Safety & Intervention System",
    version="1.1.0"
)

logger = logging.getLogger(__name__)

# Health check endpoint
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "crowd-shield-backend",
        "phase": "phase-1"
    }

# CORS Configuration - explicit local development origins
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routes always boot without later-phase optional dependencies.
app.include_router(phase1_router)
app.include_router(phase2_router)
app.include_router(synthetic_router)

try:
    from app.api.endpoints import api_router
except Exception as exc:
    logger.warning("Later-phase API routes disabled because an optional dependency or model issue was encountered: %s", exc)
else:
    app.include_router(api_router)


@app.exception_handler(Phase1APIError)
async def phase1_api_error_handler(_request, exc: Phase1APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

# Mount static files and uploads
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount(
    "/processed",
    StaticFiles(directory=str(DETECTION_PROCESSED_DIR)),
    name="processed",
)

@app.get("/")
def read_root():
    return {
        "system": "CROWD-SHIELD API Backend",
        "full_name": "Context-Aware Predictive Crowd Safety & Intervention System",
        "status": "ONLINE",
        "health": "/api/health",
        "swagger_docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
