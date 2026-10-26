import secrets

from app.core.config import get_auth_settings
from app.core.security import create_access_token, verify_password, verify_password_for_timing
from app.services.exceptions import AuthenticationError


def login(username: str, password: str) -> str:
    settings = get_auth_settings()
    username_matches = secrets.compare_digest(username, settings.username)
    if username_matches:
        password_matches = verify_password(password, settings.password_hash)
    else:
        verify_password_for_timing(password)
        password_matches = False
    if not username_matches or not password_matches:
        raise AuthenticationError("Invalid username or password")
    return create_access_token(settings.username)
