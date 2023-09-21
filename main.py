import asyncio
from src.database import get_db_service, reset_models


async def main():
    async with get_db_service() as service:
        await reset_models()
        user = await service.create_user("test", "blablabla")
        user2 = await service.create_user("test2", "blablabla")
        await service.commit()
        file = await service.create_file("name", user.id, "a,b,c")
        file2 = await service.create_file("file2", user2.id, "m,n,t")
        await service.commit()
        await service.create_data(file.id, "a", 0, "aaaaaaa")
        await service.create_data(file.id, "b", 0, "")
        await service.create_data(file.id, "c", 0, "cccc")
        await service.create_data(file.id, "a", 1, "cccca")
        await service.create_data(file.id, "b", 1, "ccccb")
        await service.create_data(file.id, "c", 1, "ccccd")
        await service.create_data(file2.id, "m", 0, "aaaaaaa")
        await service.create_data(file2.id, "n", 0, "aaaaaaa")
        await service.create_data(file2.id, "t", 0, "aaaaaaa")
        table_data = {
            'a': ['x', 'a', 'dd'],
            'b': ['y', 'b', 'ee'],
            'c': ['z', 'c', 'ff']
        }
        for key, value in table_data.items():
            for val in value:
                await service.create_data(file.id, key, 0, val)
        await service.commit()
        await service.create_file_access(file.id, user2.id)
        await service.commit()
        print(await service.get_files(user.id))
        # print(await get_files(session, user2.id))
        # print(await service.delete_file(file.id))
        await service.commit()
        data = await service.get_data(
            file.id, {"a": "x"}
        )
        print("\n".join(map(str, data)))


if __name__ == "__main__":
    asyncio.run(main())
