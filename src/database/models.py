import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, hashed_password={self.hashed_password})"


class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    column_order = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f"File(id={self.id}, name={self.name}, owner_id={self.owner_id}, column_order={self.column_order})"


class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"))
    column_name = Column(String, nullable=False)
    row_number = Column(Integer, nullable=False)
    value = Column(String, nullable=False, default="")

    def __repr__(self) -> str:
        return f"Data(id={self.id}, file_id={self.file_id}, column_name={self.column_name}, row_number={self.row_number}, value={self.value})"


class FileAccess(Base):
    __tablename__ = "file_access"

    id = Column(Integer, primary_key=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    def __repr__(self) -> str:
        return (
            f"FileAccess(id={self.id}, file_id={self.file_id}, user_id={self.user_id})"
        )
