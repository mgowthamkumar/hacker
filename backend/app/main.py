import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import httpx

from backend.app.config import settings, BASE_DIR
from backend.app.database import init_db
from backend.app.routes.auth import router as auth_router
from backend.app.routes.profile import router as profile_router
from backend.app.routes.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and import users.json records
    init_db()
    print("==================================================")
    print("[AUTOHIRE AI] Python FastAPI Backend Initialized")
    print(f"Serving Web & Auth on: http://{settings.HOST}:{settings.PORT}")
    print("==================================================")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AutoHire AI FastAPI Backend",
        "version": settings.VERSION
    }

# Include Core Authentication, Profile, and Opportunities Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(jobs_router)

# Optional Proxy to App1 (Port 5503) for Resume Analyzer if called on Port 8800
@app.api_route("/api/rag/analyze", methods=["GET", "POST"])
@app.api_route("/analyzer", methods=["GET", "POST"])
@app.api_route("/api/analyzer", methods=["GET", "POST"])
async def proxy_to_analyzer(request: Request):
    target_url = f"http://127.0.0.1:5503{request.url.path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = dict(request.headers)
            headers.pop("host", None)
            content = await request.body()
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=content
            )
            return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception:
        # If app1.py is not running on 5503, return clean message
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "Resume analyzer process (app1.py) is starting or not reached."}
        )

# Optional Proxy to Main (Port 8000) for Chatbot if called on Port 8800
@app.api_route("/api/chat", methods=["POST"])
async def proxy_to_chat(request: Request):
    target_url = "http://127.0.0.1:8000/api/chat"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            content = await request.body()
            resp = await client.post(target_url, content=content, headers={"Content-Type": "application/json"})
            return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception:
        return JSONResponse(
            status_code=200,
            content={
                "answer": "AutoHire AI Assistant is online. Ready to help you prepare for technical interviews and opportunities."
            }
        )

# Root route serves index.html or sign-in.html
@app.get("/")
def serve_index():
    index_file = BASE_DIR / "sign-in.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "AutoHire AI Backend Running"}

# Mount static files to serve the entire AutoHire AI frontend (HTML, JS, CSS, assets)
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
