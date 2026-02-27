import json
import os
from identity.auth import hash_password, verify_password

USER_FILE = "identity/users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {"users": []}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def create_user(username, password):
    data = load_users()

    for u in data["users"]:
        if u["username"] == username:
            return False

    data["users"].append({
        "username": username,
        "password": hash_password(password)
    })

    save_users(data)
    return True

def authenticate_user(username, password):
    data = load_users()

    for u in data["users"]:
        if u["username"] == username:
            if verify_password(password, u["password"]):
                return True

    return False
