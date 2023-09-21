import pytest
import pytest_asyncio
from src.database import reset_models, get_db_service
from contextlib import nullcontext

from sqlalchemy.exc import IntegrityError, DBAPIError
from uuid import uuid4


@pytest_asyncio.fixture(scope="session", autouse=True)
async def reset_db():
    await reset_models()

@pytest_asyncio.fixture
async def user():
    async with get_db_service() as service:
        user = await service.create_user("user", "password")
        await service.commit()
        yield user
        res = await service.delete_user(user.id)
        await service.commit()


class TestDatabaseService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "username,hashed_password,context",
        [
            ("username1", "hashed_password1", nullcontext()),
            ("1", "hashed_password2", nullcontext()),
            ("username3", "1", nullcontext()),
            ("2", "2", nullcontext()),
            ("", "", nullcontext()),
            ("username1", "hashed_password3", pytest.raises(IntegrityError)),
            (1, 1, pytest.raises(DBAPIError)),
        ],
    )
    async def test_create_user(self, username, hashed_password, context):
        async with get_db_service() as service:
            with context:
                user = await service.create_user(username, hashed_password)
                assert user.username == username
                assert user.hashed_password == hashed_password
                await service.commit()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "filename, columns_order, context",
        [
            ("file1", "a,b,c", nullcontext()),
            (1, "a,b,c", pytest.raises(DBAPIError)),
            ("file1", 1, pytest.raises(DBAPIError)),
        ],
    )
    async def test_create_file_user(self, filename, columns_order, context, user):
        async with get_db_service() as service:
            with context:
                file = await service.create_file(filename, user.id, columns_order)
                await service.commit()
                assert file.owner_id == user.id

    @pytest.mark.asyncio
    async def test_create_file_nouser(self):
        async with get_db_service() as service:
            with pytest.raises(IntegrityError):
                file = await service.create_file("file1", uuid4(), "a,b,c")
                await service.commit()
