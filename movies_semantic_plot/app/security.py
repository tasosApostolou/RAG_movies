"""
Security — Password Hashing & JWT Token Helpers

Provides:
  - hash_password(raw) → hashed string
  - verify_password(raw, hashed) → bool
  - create_access_token(subject) → JWT string
"""

from datetime import datetime, timedelta, timezone
from app.core.config import settings
from jose import jwt
from passlib.context import CryptContext
secret_key = settings.SECRET_KEY
algorithm = settings.ALGORITHM
access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# ----------- JWT -----------
jwt_cofig = {
    "secret_key": "secret-key-n&^R%^!VB766n7nzzb",
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
}
# --- Password Hashing ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(raw, hashed)


# --- JWT Tokens ---

def create_access_token(sub: str,is_superuser: bool,) -> str:
    """Create a signed JWT with a subject and expiry."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=access_token_expire_minutes,
    )
    payload = {"sub": sub, "is_superuser":is_superuser, "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=algorithm)
