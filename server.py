from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
import sqlite3
import os
from openai import OpenAI

app = FastAPI()

# =========================
# CONFIG
# =========================

SECRET = os.getenv("JWT_SECRET", "shine_secret")
ALGORITHM = "HS256"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

security = HTTPBearer()

# =========================
# DATABASE INIT
# =========================

def init_db():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_memory(
        user_id TEXT,
        key TEXT,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# TOKEN VERIFY
# =========================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=403, detail="Invalid token")

# =========================
# LOGIN ENDPOINT
# =========================

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    username = form_data.username
    password = form_data.password

    # simple demo auth
    if username != "doug" or password != "shine":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "id": username,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {"status": "Shine Companion Online"}

# =========================
# SAVE MEMORY
# =========================

@app.post("/memory/save")
def save_memory(data: dict, user=Depends(verify_token)):

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO user_memory (user_id,key,value) VALUES (?,?,?)",
        (user["id"], data["key"], data["value"])
    )

    conn.commit()
    conn.close()

    return {"status": "saved"}

# =========================
# GET MEMORY
# =========================

@app.get("/memory/get")
def get_memory(user=Depends(verify_token)):

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute(
        "SELECT key,value FROM user_memory WHERE user_id=?",
        (user["id"],)
    )

    data = c.fetchall()

    conn.close()

    return {"memory": data}

# =========================
# CHAT
# =========================

@app.post("/chat")
async def chat(request: Request, user=Depends(verify_token)):

    body = await request.json()
    message = body.get("message")

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute(
        "SELECT key,value FROM user_memory WHERE user_id=?",
        (user["id"],)
    )

    memories = c.fetchall()

    memory_context = ""
    for m in memories:
        memory_context += f"{m[0]}: {m[1]}\n"

    prompt = f"""
MEMORY:
{memory_context}

USER MESSAGE:
{message}
"""

    response = client.chat.completions.create(
        model=os.getenv("SHINE_MODEL","gpt-4o-mini"),
        messages=[
            {"role":"system","content":"You are Shine Companion."},
            {"role":"user","content":prompt}
        ]
    )

    reply = response.choices[0].message.content

    conn.close()

    return {"reply": reply}