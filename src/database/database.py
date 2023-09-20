from uuid import UUID
from sqlalchemy import delete, or_, select
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
    session: AsyncSession, name: str, owner_id: UUID, column_order: str
) -> File:
    db_file = File(name=name, owner_id=owner_id, column_order=column_order)
    session.add(db_file)
    return db_file


async def create_data(
    session: AsyncSession, file_id: UUID, column_name: str, row_number: int, data: str
) -> Data:
    db_data = Data(
        file_id=file_id, column_name=column_name, row_number=row_number, data=data
    )
    session.add(db_data)
    return db_data


async def get_data(
    session: AsyncSession, file_id: UUID, offset: int = 0, limit: int = 100
) -> list[Data]:
    query = select(Data).where(Data.file_id == file_id).offset(offset).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_files(session: AsyncSession, user_id: UUID) -> list[File]:
    query = (
        select(File)
        .outerjoin(FileAccess, File.id == FileAccess.file_id)
        .where(or_(FileAccess.user_id == user_id, File.owner_id == user_id))
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def delete_file(session: AsyncSession, file_id: UUID):
    query_file_access = delete(FileAccess).where(FileAccess.file_id == file_id)
    query_data = delete(Data).where(Data.file_id == file_id)
    query_file = delete(File).where(File.id == file_id)
    await session.execute(query_file_access)
    await session.execute(query_data)
    result = await session.execute(query_file)


async def create_file_access(
    session: AsyncSession, file_id: UUID, user_id: UUID
) -> FileAccess:
    db_file_access = FileAccess(file_id=file_id, user_id=user_id)
    session.add(db_file_access)
    return db_file_access
