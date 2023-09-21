import asyncio
from src.database.service import (
    delete_file,
    reset_models,
    create_user,
    create_file_access,
    create_data,
    create_file,
    get_session,
    async_session,
    get_files,
    delete_file,
    get_data,
)


async def main():
    async with async_session() as session:
        await reset_models()
        user = await create_user(session, "test", "blablabla")
        user2 = await create_user(session, "test2", "blablabla")
        await session.commit()
        file = await create_file(session, "name", user.id, "a,b,c")
        file2 = await create_file(session, "file2", user2.id, "m,n,t")
        await session.commit()
        await create_data(session, file.id, "a", 0, "aaaaaaa")
        await create_data(session, file.id, "b", 0, "")
        await create_data(session, file.id, "c", 0, "cccc")
        await create_data(session, file.id, "a", 1, "cccca")
        await create_data(session, file.id, "b", 1, "ccccb")
        await create_data(session, file.id, "c", 1, "ccccd")
        await create_data(session, file2.id, "m", 0, "aaaaaaa")
        await create_data(session, file2.id, "n", 0, "aaaaaaa")
        await create_data(session, file2.id, "t", 0, "aaaaaaa")
        await create_file_access(session, file.id, user2.id)
        await session.commit()
        print(await get_files(session, user.id))
        # print(await get_files(session, user2.id))
        # print(await delete_file(session, file.id))
        await session.commit()
        data = await get_data(
            session, file.id, {"a": "cccca", "b": "ccccb", 'c': 'a'}
        )
        print("\n".join(map(str, data)))


if __name__ == "__main__":
    asyncio.run(main())
