from pydantic import UUID4, BaseModel


class User(BaseModel):
    id: UUID4
    username: str
    hashed_password: str
