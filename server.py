import os
import time
import json
import uuid
import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from logging.handlers import RotatingFileHandler

import requests

# =====================================================
# BASIC INFO
# =====================================================

APP_NAME = "Shine Companion"
APP_VERSION = "1.4-clean"
PORT = int(os.getenv("PORT", "8060"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# =====================================================
# LOGGING
# =====================================================

logger = logging.getLogger("shine_companion")
logger.setLevel(logging.INFO)

log_path = os.path.join(LOG_DIR, "shine.log")
handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

if not logger.handlers:
    logger.addHandler(handler)

logger.info("Starting %s %s", APP_NAME, APP_VERSION)

# =====================================================
# FASTAPI INIT
# =====================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ROUTES
# =====================================================

@app.get("/status")
async def status():
    return {"ok": True, "name": APP_NAME, "version": APP_VERSION, "port": PORT}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def root():
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    return HTMLResponse("<h3>Shine Companion Running</h3>")

# =====================================================
# OPENAI TEST ENDPOINT
# =====================================================

@app.get("/openai-test")
def openai_test():
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        return {"error": "OPENAI_API_KEY not set"}

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "ping"}
        ],
        "max_tokens": 5
    }

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        return {
            "status": r.status_code,
            "response_preview": r.text[:300]
        }

    except Exception as e:
        return {"error": str(e)}

# =====================================================
# RUNNER
# =====================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)