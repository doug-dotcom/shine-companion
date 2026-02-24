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

# Your existing provider manager (kept)
from provider_manager import ProviderManager

# =========================================================
# BASIC APP INFO
# =========================================================

APP_NAME = "Shine Companion"
APP_VERSION = "1.4-login-full-users"
PORT = int(os.getenv("SHINE_PORT", "8060"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOG_DIR = os.path.join(BASE_DIR, "logs")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

INDEX_FILE = os.path.join(BASE_DIR, "index.html")  # your existing UI file

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger("shine_companion")
logger.setLevel(logging.INFO)

_log_path = os.path.join(LOG_DIR, "shine_companion.log")
handler = RotatingFileHandler(_log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(fmt)

if not logger.handlers:
    logger.addHandler(handler)

logger.info("Starting %s %s", APP_NAME, APP_VERSION)

# =========================================================
# FASTAPI INIT
# =========================================================

app = FastAPI()

SESSION_SECRET = os.getenv("SHINE_SESSION_SECRET", "shine_alpha_secret_change_me")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

allow_origins_env = os.getenv("SHINE_CORS_ORIGINS", "").strip()
if allow_origins_env:
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
else:
    allow_origins = [
        "http://localhost:8060",
        "http://127.0.0.1:8060",
        "http://localhost",
        "http://127.0.0.1",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# =========================================================
# PROVIDER MANAGER (preserved)
# =========================================================

def _init_provider_manager() -> ProviderManager:
    try:
        return ProviderManager(base_dir=BASE_DIR)
    except TypeError:
        try:
            return ProviderManager(BASE_DIR)
        except TypeError:
            return ProviderManager()

provider = _init_provider_manager()

# =========================================================
# SIMPLE RATE LIMITING
# =========================================================

RATE_LIMIT_WINDOW = int(os.getenv("SHINE_RATE_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.getenv("SHINE_RATE_MAX", "60"))
ip_hits: Dict[str, List[float]] = {}

def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    hits = ip_hits.get(ip, [])
    hits = [t for t in hits if now - t < RATE_LIMIT_WINDOW]
    if len(hits) >= RATE_LIMIT_MAX:
        ip_hits[ip] = hits
        return True
    hits.append(now)
    ip_hits[ip] = hits
    return False

# =========================================================
# USERS / AUTH
# =========================================================

def ensure_users_file() -> None:
    if not os.path.exists(USERS_FILE):
        # Alpha default users (plaintext for now)
        starter = {
            "Doug": "admin123",
            "Lyndal": "admin123",
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(starter, f, indent=2)
        logger.warning("Created users.json with alpha defaults (Doug/Lyndal). Change passwords later.")

def load_users() -> Dict[str, str]:
    ensure_users_file()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        logger.error("Failed reading users.json: %s", e)
    return {}

def get_user(request: Request) -> str:
    try:
        u = request.session.get("user")
        return str(u) if u else ""
    except Exception:
        return ""

def is_logged_in(request: Request) -> bool:
    return bool(get_user(request))

def require_login(request: Request) -> Optional[RedirectResponse]:
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    return None

def user_mode(request: Request, mode: str) -> str:
    """
    Namespaces memory by user without touching ProviderManager internals.
    Example: Doug:companion, Lyndal:companion
    """
    u = get_user(request) or "anon"
    mode = (mode or "companion").strip()
    return f"{u}:{mode}"

# =========================================================
# ROUTES
# =========================================================

@app.get("/status")
async def status():
    return {"ok": True, "name": APP_NAME, "version": APP_VERSION, "port": PORT}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if is_logged_in(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    users = load_users()
    if username in users and users[username] == password:
        request.session["user"] = username
        logger.info("Login success user=%s ip=%s", username, _client_ip(request))
        return RedirectResponse(url="/", status_code=302)

    logger.warning("Login failed user=%s ip=%s", username, _client_ip(request))
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=401,
    )

@app.get("/logout")
async def logout(request: Request):
    try:
        u = get_user(request)
        request.session.clear()
        logger.info("Logout user=%s ip=%s", u, _client_ip(request))
    except Exception:
        pass
    return RedirectResponse(url="/login", status_code=302)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    redir = require_login(request)
    if redir:
        return redir

    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)

    return HTMLResponse(
        "<h3>Shine Companion is running.</h3><p>Missing index.html in app folder.</p>",
        status_code=200
    )

@app.get("/index.html", response_class=HTMLResponse)
async def index_html(request: Request):
    redir = require_login(request)
    if redir:
        return redir
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    return RedirectResponse(url="/", status_code=302)

# =========================================================
# MEMORY ENDPOINTS (namespaced by user)
# =========================================================

@app.get("/memory/status")
async def memory_status(request: Request):
    redir = require_login(request)
    if redir:
        return redir

    fn = getattr(provider, "memory_status", None)
    if callable(fn):
        return fn()
    return {"ok": True, "note": "provider has no memory_status()"}

@app.get("/memory/peek")
async def memory_peek(request: Request, n: int = 10, mode: str = "companion"):
    redir = require_login(request)
    if redir:
        return redir

    fn = getattr(provider, "memory_peek", None)
    if callable(fn):
        try:
            n = max(1, min(int(n), 50))
        except Exception:
            n = 10
        return fn(mode=user_mode(request, mode), n=n)
    return {"ok": True, "messages": [], "note": "provider has no memory_peek()"}

@app.post("/memory/clear")
async def memory_clear(request: Request, mode: str = Form("companion")):
    redir = require_login(request)
    if redir:
        return redir

    fn = getattr(provider, "memory_clear", None)
    if callable(fn):
        return fn(mode=user_mode(request, mode))
    return {"ok": True, "cleared": False, "note": "provider has no memory_clear()"}

# =========================================================
# CHAT ENDPOINT (namespaced by user)
# =========================================================

@app.post("/chat")
async def chat(request: Request):
    if not is_logged_in(request):
        return JSONResponse({"ok": False, "error": "not_logged_in", "login": "/login"}, status_code=401)

    ip = _client_ip(request)
    if is_rate_limited(ip):
        return JSONResponse({"ok": False, "error": "rate_limited"}, status_code=429)

    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "invalid_json"}, status_code=400)

    message = (data.get("message") or "").strip()
    raw_mode = (data.get("mode") or request.query_params.get("mode") or "companion").strip()
    mode = user_mode(request, raw_mode)

    if not message:
        return JSONResponse({"ok": False, "error": "empty_message"}, status_code=400)
    if len(message) > 4000:
        return JSONResponse({"ok": False, "error": "message_too_long"}, status_code=413)

    req_id = uuid.uuid4().hex[:8]
    logger.info("REQ %s user=%s ip=%s mode=%s len=%s", req_id, get_user(request), ip, mode, len(message))

    try:
        reply = None
        fn = getattr(provider, "chat", None)

        if callable(fn):
            try:
                reply = fn(message, mode=mode)
            except TypeError:
                try:
                    reply = fn(message, mode)
                except TypeError:
                    reply = fn({"message": message, "mode": mode})
        else:
            return JSONResponse({"ok": False, "error": "provider_missing_chat()"}, status_code=500)

        if isinstance(reply, dict):
            return JSONResponse(reply)

        return JSONResponse({"ok": True, "reply": str(reply), "mode": mode})

    except Exception as e:
        logger.exception("REQ %s provider error: %s", req_id, e)
        return JSONResponse({"ok": False, "error": "provider_error", "detail": str(e)}, status_code=502)

# =========================================================
# RUNNER
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=PORT, reload=False, log_level="warning")