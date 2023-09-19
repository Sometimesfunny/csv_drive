from pydantic import UUID4
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from .models import FileAccess, User, File, Data, Base
from dotenv import load_dotenv
import os


load_dotenv()


DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_IP')}/{os.getenv('DB_NAME')}"


engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def reset_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def create_user(
    session: AsyncSession, username: str, hashed_password: str
) -> User:
    db_user = User(username=username, hashed_password=hashed_password)
    session.add(db_user)
    return db_user


async def create_file(
    session: AsyncSession, name: str, owner_id: UUID4, column_order: str
) -> File:
    db_file = File(name=name, owner_id=owner_id, column_order=column_order)
    session.add(db_file)
    return db_file


async def create_data(
    session: AsyncSession, file_id: UUID4, column_name: str, row_number: int, data: str
) -> Data:
    db_data = Data(
        file_id=file_id, column_name=column_name, row_number=row_number, data=data
    )
    session.add(db_data)
    return db_data


async def create_file_access(
    session: AsyncSession, file_id: UUID4, user_id: UUID4
) -> FileAccess:
    db_file_access = FileAccess(file_id=file_id, user_id=user_id)
    session.add(db_file_access)
    return db_file_access
