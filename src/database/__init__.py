from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from .service import DatabaseService
from ..errors import NoCredentialsException
from dotenv import load_dotenv
import os


load_dotenv()

if not (os.getenv('DB_USER') and os.getenv('DB_PASS') and os.getenv('DB_IP') and os.getenv('DB_NAME')):
    raise NoCredentialsException

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_IP')}/{os.getenv('DB_NAME')}"


engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def reset_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_db_service() -> AsyncIterator[DatabaseService]:
    async with async_session() as session:
        yield DatabaseService(session)
