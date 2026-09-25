from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.db import get_session
from app.models.user import User
from app.security import jwt_cofig


# --- Database Session ---

SessionDep = Annotated[Session, Depends(get_session)]

# --- Authentication ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Authenticated user 
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> User:
    """Decode the JWT, look up the user, or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not token:
            raise credentials_exception
        payload = jwt.decode(
            token, jwt_cofig["secret_key"], algorithms=[jwt_cofig["algorithm"]],
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.email == username)).first()
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_admin(user: CurrentUser) -> User:
    """Verify the user is an admin, or raise 403."""
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
    return user

CurrentAdmin = Annotated[User, Depends(get_current_admin)]

