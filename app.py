from fastapi import Request, Form
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import json
from fastapi import FastAPI
from pydantic import BaseModel
from dateutil import parser
import datetime, os

app = FastAPI()

class Cmd(BaseModel):
    command: str

@app.post("/bridge")
def bridge(cmd: Cmd):
    ts = datetime.datetime.now().isoformat()
    with open(r"C:\ShineAI\bridge.log","a") as f:
        f.write(f"[{ts}] {cmd.command}\n")
    return {"status":"ok","received":cmd.command}


@app.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    with open("users.json") as f:
        users = json.load(f)

    if username in users and users[username] == password:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


# --- Compatibility route for frontend ---
@app.post("/chat")
async def chat_compat(payload: dict):
    try:
        if "ask" in globals():
            return await ask(payload)
        elif "chat" in globals():
            return await chat(payload)
        elif "handle_chat" in globals():
            return await handle_chat(payload)
        else:
            return {"error": "No compatible handler found"}
    except Exception as e:
        return {"error": str(e)}

