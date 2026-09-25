from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.dependencies import CurrentUser, SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    """
    OAuth2 password flow login.
    Validates credentials and returns {access_token, token_type}.
    token_type:"bearer".
    HTTP_401_UNAUTHORIZED is raised if credentials are invalid.
    body: form data with email and password.
    response: JSON with access_token and token_type.
    """
    user = session.exec(
        select(User).where(User.email == form.username)
    ).first()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user.email,user.is_superuser),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, session: SessionDep):
    """
    Register a new user.
    email 'admin' automatically gets admin privileges
    Validates unique email and returns created user info. If email is taken, HTTP_409_CONFLICT is raised.    
    Body: UserCreate schema.
    Response: UserOut schema with status code 201.
    """
    existing = session.exec(
        select(User).where(User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="email already taken",
        )
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        is_superuser=(data.email == settings.FIRST_SUPERUSER),
    )

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to register user") from e


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    """Requires authentication. If not authenticated, HTTP_401_UNAUTHORIZED is raised.
    Return the current authenticated user's info.
    Response: UserOut schema with status code 200."""
    return user


