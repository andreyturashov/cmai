from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret")

_google_request = google_requests.Request()


def get_cors_origins() -> list[str]:
    raw_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def verify_google_credential(credential: str) -> dict[str, str]:
    if not GOOGLE_CLIENT_ID:
        raise RuntimeError("GOOGLE_CLIENT_ID is not configured")

    try:
        payload = id_token.verify_oauth2_token(credential, _google_request, GOOGLE_CLIENT_ID)
    except (GoogleAuthError, ValueError) as exc:
        raise ValueError("Invalid Google credential") from exc

    if payload.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("Invalid Google issuer")

    if not payload.get("email") or not payload.get("sub"):
        raise ValueError("Google profile is missing required claims")

    if payload.get("email_verified") is False:
        raise ValueError("Google email is not verified")

    return {
        "sub": str(payload["sub"]),
        "email": str(payload["email"]),
        "name": str(payload.get("name") or payload["email"]),
        "avatar_url": str(payload.get("picture") or ""),
    }
