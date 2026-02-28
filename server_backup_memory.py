from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from jose import jwt
import sqlite3
import os

app = FastAPI()

SECRET = os.getenv("JWT_SECRET","shine_secret")

security = HTTPBearer()

def verify_token(credentials=Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.get("/")
def root():
    return {"status":"Shine Companion Online"}

@app.post("/memory/save")
def save_memory(data:dict, user=Depends(verify_token)):
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO user_memory (user_id,key,value) VALUES (?,?,?)",
        (user["id"], data["key"], data["value"])
    )

    conn.commit()
    conn.close()

    return {"status":"saved"}

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

    return {"memory":data}
# ==============================
# SHINE COMPANION CHAT ENDPOINT
# ==============================

from fastapi import Request
from openai import OpenAI
import sqlite3
import os

client = OpenAI()

@app.post("/chat")
async def chat(request: Request, user=Depends(verify_token)):

    data = await request.json()
    message = data.get("message")

    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT key,value FROM user_memory WHERE user_id=?",
        (user["id"],)
    )

    memories = cursor.fetchall()

    memory_context = ""
    for m in memories:
        memory_context += f"{m[0]}: {m[1]}\n"

    prompt = f"""
User memory:
{memory_context}

User message:
{message}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Shine Companion."},
            {"role": "user", "content": prompt}
        ]
    )

    reply = response.choices[0].message.content

    conn.close()

    return {"reply": reply}