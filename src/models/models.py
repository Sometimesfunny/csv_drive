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
