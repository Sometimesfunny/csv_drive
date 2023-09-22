from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from ..auth.jwt import create_access_token, decode_access_token
from ..auth.password import get_password_hash, verify_password
from ..auth.models import Token
from ..database import get_db_service, DatabaseService
from ..errors import UserAlreadyExists
from ..models import User


router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.post("/register/", response_model=Token)
async def register(
    username: str,
    password: str,
    response: Response,
    service: DatabaseService = Depends(get_db_service),
):
    hashed_password = get_password_hash(password)
    await service.create_user(username, hashed_password)
    try:
        await service.commit()
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    access_token = create_access_token(data={"sub": username})
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return Token(access_token=access_token, token_type="Bearer")


@router.post("/token/", response_model=Token)
async def login_for_access_token(
    username: str, password: str, response: Response, service: DatabaseService = Depends(get_db_service)
):
    user = await service.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": username})
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception as e:
        print(type(e), e)
        raise credentials_exception

    user_db = await service.get_user(username)

    if user_db:
        return User.model_validate(user_db)


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
