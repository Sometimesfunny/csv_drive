from uuid import UUID
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class Credentials(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: UUID
    username: str

    class Config:
        from_attributes = True

class File(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    column_order: str

    class Config:
        from_attributes = True


class FileAccess(BaseModel):
    file_id: UUID
    user_id: UUID
    username: UUID
