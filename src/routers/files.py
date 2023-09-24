from ast import Str
import asyncio
from collections import defaultdict
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    UploadFile,
    status,
    HTTPException,
)

from ..errors import CSVValidationError

from ..database.service import DatabaseService
from .utils import get_current_user, sort_table
from ..models import User, File, FileAccess
from ..csv_processor import CSVProcessor
from ..database import get_db_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_new_file(
    file: UploadFile,
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    wrong_file_type = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Wrong file type."
    )
    if file.content_type != "text/csv":
        raise wrong_file_type
    try:
        processor = CSVProcessor(file.file)
        new_file = await service.create_file(
            file.filename, user.id, ",".join(processor.column_names)
        )
        await service.commit()
        tasks = []
        for row_number, row in enumerate(processor):
            for column_name, value in row.items():
                tasks.append(
                    asyncio.create_task(
                        service.create_data(new_file.id, column_name, row_number, value)
                    )
                )
        await asyncio.gather(*tasks)
        await service.commit()
    except CSVValidationError:
        raise wrong_file_type
    finally:
        file.file.close()
    return new_file.id


@router.get("/")
async def get_available_files(
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    db_files = await service.get_files(user.id)
    return list(map(File.model_validate, db_files))


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found",
        )
    if file.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not the owner of file with id {file_id}",
        )
    res = await service.delete_file(file.id)
    await service.commit()
    if not res:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response("Success")


@router.get("/{file_id}")
async def get_file_data(
    file_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found",
        )
    if file.owner_id != user.id:
        has_access = await service.has_access(file.id, user.id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not able to get data from file id {file_id}",
            )
    column_names = file.column_order.split(",")
    filters: dict[str, str] = {}
    sort: dict[str, str] = {}
    for key, value in request.query_params.items():
        if key not in column_names:
            continue
        splitted_value = value.split(",")
        filter_q = splitted_value[0]
        sort_q = None
        if len(splitted_value) > 1:
            sort_q = splitted_value[1]
        if filter_q:
            filters[key] = filter_q
        if sort_q and sort_q in ("asc", "desc"):
            sort[key] = sort_q
    data_db = await service.get_data(file_id, filters=filters)
    data = defaultdict(list)
    for item in data_db:
        data[item.column_name].append(item.value)
    if sort:
        data = sort_table(data, sort)
    return data


@router.put("/{file_id}/{username}")
async def grant_file_access(
    file_id: str,
    username: str,
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with UUID {file_id} not found",
        )
    if file.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not able to edit permissions for file id {file_id}",
        )
    access_user = await service.get_user(username)
    if not access_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found",
        )
    await service.create_file_access(file.id, access_user.id)
    await service.commit()
    return Response("Success")


@router.delete("/{file_id}/{username}")
async def grant_file_access(
    file_id: str,
    username: str,
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with UUID {file_id} not found",
        )
    if file.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not able to edit permissions for file id {file_id}",
        )
    access_user = await service.get_user(username)
    if not access_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found",
        )
    result = await service.delete_file_access(file.id, access_user.id)
    if result:
        return Response("Success")
    return Response("Nothing changed", status_code=status.HTTP_304_NOT_MODIFIED)


@router.get("/{file_id}/access")
async def get_file_access(
    file_id: str,
    user: User = Depends(get_current_user),
    service: DatabaseService = Depends(get_db_service),
):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with UUID {file_id} not found",
        )
    if file.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not able to get data from file id {file_id}",
        )
    file_access_db:list[UUID, UUID, str] = await service.get_file_access(file.id)
    file_access = []
    for access in file_access_db:
        file_access.append(FileAccess(file_id=access[0], user_id=access[1], username=access[2]))
    return file_access
