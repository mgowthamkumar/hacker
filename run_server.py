"""
AutoHire AI - Python FastAPI Server Launcher
Runs the FastAPI Web & Authentication Backend on Port 8800.
"""

import sys
import uvicorn
from pathlib import Path

# Configure utf-8 encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings

if __name__ == "__main__":
    print(f"Starting AutoHire AI FastAPI Server on {settings.HOST}:{settings.PORT}...")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False
    )
