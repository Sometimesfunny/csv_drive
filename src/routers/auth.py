from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer

from ..errors import TokenExpiredException
from ..auth.jwt import create_access_token, decode_access_token
from ..auth.password import get_password_hash, verify_password
from ..database import get_db_service, DatabaseService
from sqlalchemy.exc import IntegrityError
from ..models import User, Token, Credentials


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


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: DatabaseService = Depends(get_db_service),
) -> User | None:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user_db = await service.get_user(username)

    if user_db:
        return User.model_validate(user_db)
    raise credentials_exception


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
