import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

_MIN_JWT_SECRET_LENGTH = 32


@dataclass(frozen=True)
class AuthSettings:
    username: str
    password_hash: str
    jwt_secret: str
    jwt_expire_minutes: int


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to the gitignored .env file."
        )
    return database_url


@lru_cache
def get_auth_settings() -> AuthSettings:
    username = os.environ.get("APP_USERNAME", "").strip()
    password_hash = os.environ.get("APP_PASSWORD_HASH", "").strip()
    jwt_secret = os.environ.get("JWT_SECRET", "")
    expire_raw = os.environ.get("JWT_EXPIRE_MINUTES", "60").strip()

    if not username:
        raise RuntimeError("APP_USERNAME is not set. Add it to the gitignored .env file.")
    if not password_hash.startswith("$argon2"):
        raise RuntimeError(
            "APP_PASSWORD_HASH must be an Argon2 hash in the gitignored .env file."
        )
    if len(jwt_secret) < _MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            "JWT_SECRET must be at least 32 characters in the gitignored .env file."
        )
    try:
        jwt_expire_minutes = int(expire_raw)
    except ValueError:
        jwt_expire_minutes = 0
    if jwt_expire_minutes <= 0:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be a positive integer.")

    return AuthSettings(
        username=username,
        password_hash=password_hash,
        jwt_secret=jwt_secret,
        jwt_expire_minutes=jwt_expire_minutes,
    )
