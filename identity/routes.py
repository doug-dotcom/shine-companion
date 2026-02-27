from fastapi import APIRouter
from pydantic import BaseModel
from identity.users import create_user, authenticate_user
from identity.auth import create_access_token

router = APIRouter()

class UserRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: UserRequest):
    success = create_user(user.username, user.password)

    if not success:
        return {"status":"error","message":"User already exists"}

    return {"status":"ok","message":"User created"}

@router.post("/login")
def login(user: UserRequest):

    if not authenticate_user(user.username, user.password):
        return {"status":"error","message":"Invalid credentials"}

    token = create_access_token({"sub": user.username})

    return {
        "status":"ok",
        "token": token
    }
