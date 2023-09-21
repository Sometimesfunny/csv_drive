from uuid import UUID
from sqlalchemy import and_, asc, delete, desc, exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import FileAccess, User, File, Data


class DatabaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, hashed_password: str) -> User:
        db_user = User(username=username, hashed_password=hashed_password)
        self.session.add(db_user)
        return db_user
    
    async def delete_user(self, user_id: UUID):
        # query_files = delete(File).where(File.owner_id == user_id)
        # await self.session.execute(query_files)
        query_user = delete(User).where(User.id == user_id)
        result = await self.session.execute(query_user)
        return result.rowcount > 0

    async def create_file(self, name: str, owner_id: UUID, column_order: str) -> File:
        db_file = File(name=name, owner_id=owner_id, column_order=column_order)
        self.session.add(db_file)
        return db_file

    async def create_data(
        self,
        file_id: UUID,
        column_name: str,
        row_number: int,
        value: str,
    ) -> Data:
        db_data = Data(
            file_id=file_id, column_name=column_name, row_number=row_number, value=value
        )
        self.session.add(db_data)
        return db_data

    async def get_data(
        self,
        file_id: UUID,
        filters: dict[str, str] = None,
        sort: dict[str, str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Data]:
        query = (
            select(Data)
            .where(
                Data.file_id == file_id,
                Data.row_number >= offset,
                Data.row_number < offset + limit,
            )
            .offset(offset)
            .limit(limit)
        )

        if filters:
            filter_conditions = []
            for column_name, value in filters.items():
                try:
                    filter_conditions.append(
                        and_(Data.column_name == column_name, Data.value == value)
                    )
                except AttributeError:
                    print(f"Attribute not found {column_name}")
            if filter_conditions:
                subquery = (
                    select(Data.row_number)
                    .where(Data.file_id == file_id, or_(*filter_conditions))
                    .group_by(Data.row_number)
                    .having(func.count() == len(filter_conditions))
                ).alias("sq")
                query = query.where(
                    exists().where(and_(Data.row_number == subquery.c.row_number))
                )

        if sort:
            sort_conditions = []
            for column_name, sort_order in sort.items():
                sort_func = asc if sort_order == "asc" else desc
                try:
                    sort_conditions.append(sort_func(getattr(Data, column_name)))
                except AttributeError:
                    print(f"Attribute not found {column_name}")
            if sort_conditions:
                query = query.order_by(*sort_conditions)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_files(self, user_id: UUID) -> list[File]:
        query = (
            select(File)
            .outerjoin(FileAccess, File.id == FileAccess.file_id)
            .where(or_(FileAccess.user_id == user_id, File.owner_id == user_id))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_file(self, file_id: UUID) -> bool:
        query_file_access = delete(FileAccess).where(FileAccess.file_id == file_id)
        query_data = delete(Data).where(Data.file_id == file_id)
        query_file = delete(File).where(File.id == file_id)
        await self.session.execute(query_file_access)
        await self.session.execute(query_data)
        result = await self.session.execute(query_file)
        return result.rowcount > 0

    async def create_file_access(self, file_id: UUID, user_id: UUID) -> FileAccess:
        db_file_access = FileAccess(file_id=file_id, user_id=user_id)
        self.session.add(db_file_access)
        return db_file_access

    async def commit(self):
        await self.session.commit()
    
    async def rollback(self):
        await self.session.rollback()
