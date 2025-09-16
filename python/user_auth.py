import json
import os
import hashlib

AUTH_FILE = os.path.join("..", "data", "users_auth.json")

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def load_users():
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading auth file: {e}")
        return []

def authenticate(username, password):
    hashed = hash_password(password)
    users = load_users()
    for user in users:
        if user.get("username") == username and user.get("password") == hashed:
            return True
    return False

def get_user(username):
    users = load_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None

def add_user(username, password, department="Help Desk"):
    users = load_users()
    if any(u.get("username") == username for u in users):
        return False
    users.append({
        "username": username,
        "password": hash_password(password),
        "department": department
    })
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False
