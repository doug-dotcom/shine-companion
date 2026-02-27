from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

# OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Request schema
class ChatRequest(BaseModel):
    message: str


# Root check
@app.get("/")
def read_root():
    return {"status": "Shine Companion running"}


# Chat endpoint
@app.post("/chat")
def chat(req: ChatRequest):

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[

            {
                "role": "system",
                "content": """
You are Shine Companion.

Shine Companion is calm, supportive, emotionally intelligent and grounded.

Your purpose is to help people talk freely without judgement.

Your tone:
- calm
- kind
- thoughtful
- grounded
- human

You encourage reflection and growth.

Never sound robotic.
Never sound corporate.
Always respond like a wise supportive companion.

You represent the Shine philosophy:

Speak your truth.
No judgement.
Growth through reflection.
"""
            },

            {
                "role": "user",
                "content": req.message
            }

        ],
        temperature=0.7
    )

    return {
        "reply": completion.choices[0].message.content
    }