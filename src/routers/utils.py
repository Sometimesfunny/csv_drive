from fastapi import Depends, HTTPException, status
from src.auth.jwt import decode_access_token
from src.database import get_db_service

from ..database.service import DatabaseService
from ..errors import TokenExpiredException
from ..models import User
from .auth import oauth2_scheme


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: DatabaseService = Depends(get_db_service),
) -> User:
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


def sort_table(table: dict[str, list], sort_order: dict[str, str]) -> dict[str, list]:
    rows = [dict(zip(table, row)) for row in zip(*table.values())]

    def sort_key(row):
        return tuple(
            row[column] if order == "asc" else -row[column]
            for column, order in sort_order.items()
        )

    sorted_rows = sorted(rows, key=sort_key)
    sorted_table = {column: [] for column in table.keys()}
    for row in sorted_rows:
        for column, value in row.items():
            sorted_table[column].append(value)
    return sorted_table
