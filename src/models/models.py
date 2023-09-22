from uuid import UUID
from pydantic import BaseModel

class User(BaseModel):
    id: UUID
    username: str
    hashed_password: str

    class Config:
        orm_mode = True
