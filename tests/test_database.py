from collections import defaultdict
import pprint
import pytest
import pytest_asyncio
from src.database import reset_models, test_db_service
from contextlib import nullcontext

from sqlalchemy.exc import IntegrityError, DBAPIError
from uuid import uuid4


@pytest_asyncio.fixture(scope="session", autouse=True)
async def reset_db():
    await reset_models()


@pytest_asyncio.fixture
async def user():
    async with test_db_service() as service:
        user = await service.create_user(f"user_{uuid4()}", "password")
        await service.commit()
        yield user
        res = await service.delete_user(user.id)
        await service.commit()


@pytest_asyncio.fixture
async def file():
    async with test_db_service() as service:
        user = await service.create_user("user", "password")
        file = await service.create_file("file1", user.id, "a,b,c")
        await service.commit()
        yield file
        await service.delete_user(user.id)
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
        async with test_db_service() as service:
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
        async with test_db_service() as service:
            with context:
                file = await service.create_file(filename, user.id, columns_order)
                await service.commit()
                assert file.owner_id == user.id
                await service.delete_file(file.id)
                await service.commit()

    @pytest.mark.asyncio
    async def test_create_file_nouser(self):
        async with test_db_service() as service:
            with pytest.raises(IntegrityError):
                file = await service.create_file("file1", uuid4(), "a,b,c")
                await service.commit()

    @pytest.mark.asyncio
    async def test_data(self, file):
        async with test_db_service() as service:
            table_data = {
                "a": ["x", "a", "dd", "x", "3", "3"],
                "b": ["y", "b", "ee", "f", "2", "1"],
                "c": ["z", "c", "ff", "h", "1", "2"],
            }
            for key, value in table_data.items():
                for i, val in enumerate(value):
                    await service.create_data(file.id, key, i, val)
            await service.commit()
            data = await service.get_data(file.id)
            got_data = defaultdict(list)
            for item in data:
                assert item.file_id == file.id
                got_data[item.column_name].append(item.value)
            assert table_data == got_data
            data = await service.get_data(file.id, {"a": "x"})
            got_data = defaultdict(list)
            for item in data:
                got_data[item.column_name].append(item.value)
            assert got_data == {"a": ["x", "x"], "b": ["y", "f"], "c": ["z", "h"]}
            data = await service.get_data(file.id, {})
            got_data = defaultdict(list)
            for item in data:
                got_data[item.column_name].append(item.value)
            assert table_data == got_data
            assert await service.delete_file(file.id) is True
            await service.commit()
            assert await service.get_files(file.owner_id) == []

    @pytest.mark.asyncio
    async def test_access(self, file, user):
        async with test_db_service() as service:
            file_access = await service.create_file_access(file.id, user.id)
            await service.commit()
            assert file_access.file_id == file.id
            assert file_access.user_id == user.id
            files = await service.get_files(user.id)
            assert files[0].id == file.id
            has_access = await service.has_access(file.id, user.id)
            assert has_access is True
