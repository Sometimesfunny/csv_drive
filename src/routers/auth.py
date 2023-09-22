from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..auth.jwt import create_access_token
from ..auth.password import get_password_hash, verify_password
from ..database import get_db_service, DatabaseService
from sqlalchemy.exc import IntegrityError
from ..models import Token, Credentials


router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.post("/register", response_model=Token)
async def register(
    credentials: Credentials,
    service: DatabaseService = Depends(get_db_service),
):
    hashed_password = get_password_hash(credentials.password)
    await service.create_user(credentials.username, hashed_password)
    try:
        await service.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    access_token = create_access_token(data={"sub": credentials.username})
    return Token(access_token=access_token, token_type="Bearer")


@router.post("/token", response_model=Token)
async def login_for_access_token(
    credentials: Credentials, service: DatabaseService = Depends(get_db_service)
):
    user = await service.get_user(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": credentials.username})
    return Token(access_token=access_token, token_type="Bearer")
