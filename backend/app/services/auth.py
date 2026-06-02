import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.services.database import get_connection


security = HTTPBearer()


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    expected = hash_password(password, salt)
    return hmac.compare_digest(expected, stored_hash)


def create_user(username: str, password: str):
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists.")
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        return {"id": cursor.lastrowid, "username": username}


def authenticate_user(username: str, password: str):
    with get_connection() as conn:
        row = conn.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"id": row["id"], "username": row["username"]}


def create_access_token(user_id: int, username: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(time.time()) + settings.token_expire_hours * 3600,
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(body)
    return f"{body}.{signature}"


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_access_token(credentials.credentials)
    with get_connection() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE id = ?", (payload["sub"],)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return {"id": row["id"], "username": row["username"]}


def verify_access_token(token: str):
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token.") from exc
    if not hmac.compare_digest(_sign(body), signature):
        raise HTTPException(status_code=401, detail="Invalid token signature.")
    try:
        payload = json.loads(_unb64(body).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token payload.") from exc
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired.")
    return payload


def _sign(body: str) -> str:
    secret = get_settings().auth_secret.encode("utf-8")
    return _b64(hmac.new(secret, body.encode("utf-8"), hashlib.sha256).digest())


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
