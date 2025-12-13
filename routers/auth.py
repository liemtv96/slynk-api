from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database_sql import get_db
from core.security import hash_password, verify_password, create_access_token, decode_token
from models.user import User
from models.user_settings import UserSettings
from schemas.auth import SignupRequest, TokenResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/signup", response_model=TokenResponse, summary="Sign up")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already in use")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already in use")

    user_id = str(uuid4())
    user = User(
        id=user_id,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    settings = UserSettings(
        user_id=user_id,
        email_updates=True,
        notify_expiration=True,
        notify_reverse_upload=True,
    )
    db.add(settings)
    db.commit()

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, summary="Login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", summary="Get current user")
def get_me(current: User = Depends(get_current_user)):
    return {
        "id": current.id,
        "email": current.email,
        "username": current.username,
        "email_verified": current.email_verified,
        "twofa_enabled": current.twofa_enabled,
    }
