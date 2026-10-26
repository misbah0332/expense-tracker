from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_auth_settings

_HASHER = PasswordHash.recommended()
_DUMMY_HASH = _HASHER.hash("timing-only-not-a-credential")
_ALGORITHM = "HS256"


class TokenError(Exception):
    pass


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _HASHER.verify(password, password_hash)
    except Exception:
        return False


def verify_password_for_timing(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_auth_settings()
    lifetime = (
        settings.jwt_expire_minutes if expires_minutes is None else expires_minutes
    )
    expires_at = datetime.now(UTC) + timedelta(minutes=lifetime)
    token = jwt.encode(
        {"sub": subject, "exp": expires_at},
        settings.jwt_secret,
        algorithm=_ALGORITHM,
    )
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def decode_access_token(token: str) -> str:
    settings = get_auth_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired token") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenError("Invalid or expired token")
    if subject != settings.username:
        raise TokenError("Invalid or expired token")
    return subject
