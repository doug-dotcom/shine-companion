import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

# OAuth2 "password" flow endpoint (login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Storage (simple JSON for now; later swap to SQLite)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def _load_users() -> Dict[str, Any]:
    if not os.path.exists(USERS_FILE):
        return {"users": {}}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_users(data: Dict[str, Any]) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[Dict[str, Any]]:
    db = _load_users()
    return db["users"].get(username)

def create_user(username: str, password: str) -> None:
    db = _load_users()
    if username in db["users"]:
        raise HTTPException(status_code=400, detail="User already exists")
    db["users"][username] = {
        "username": username,
        "password_hash": get_password_hash(password),
        "created_utc": datetime.utcnow().isoformat() + "Z"
    }
    _save_users(db)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

def _secret_key() -> str:
    key = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or ""
    if not key:
        # Fail hard: JWT must not run without a secret in prod.
        raise RuntimeError("Missing SECRET_KEY (or JWT_SECRET) environment variable")
    return key

def _algo() -> str:
    return os.getenv("JWT_ALGORITHM") or "HS256"

def _ttl_minutes() -> int:
    try:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "720")  # 12 hours
    except Exception:
        return 720

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=_ttl_minutes()))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _secret_key(), algorithm=_algo())

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[_algo()])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return {"username": user["username"]}
