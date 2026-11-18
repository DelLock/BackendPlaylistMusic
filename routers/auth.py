from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import authenticate_user, client_ip, get_current_user
from models import DBUser, LoginRequest, ROLE_USER, Token, User, UserCreate
from security import JWT_EXPIRE_MINUTES, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])

USERNAME_TAKEN = "User with this username already exists"


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    # Роль всегда обычная: из тела запроса её не берём, админом через регистрацию не стать
    taken = db.query(DBUser.id).filter(func.lower(DBUser.username) == data.username.lower()).first()
    if taken:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=USERNAME_TAKEN)

    user = DBUser(username=data.username, password_hash=hash_password(data.password), role=ROLE_USER)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # два одинаковых запроса одновременно
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=USERNAME_TAKEN)
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password, client_ip(request))
    return Token(access_token=create_access_token(user.id), expires_in=JWT_EXPIRE_MINUTES * 60)


@router.get("/me", response_model=User)
def me(user: DBUser = Depends(get_current_user)):
    return user
