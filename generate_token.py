from jose import jwt

SECRET = "shine_secret"

payload = {
    "id": "demo_user"
}

token = jwt.encode(payload, SECRET, algorithm="HS256")

print("")
print("YOUR TOKEN:")
print("")
print(token)
print("")
