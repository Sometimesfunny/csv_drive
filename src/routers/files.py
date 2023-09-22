import asyncio
from collections import defaultdict
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, status, HTTPException

from ..database.service import DatabaseService
from .utils import get_current_user
from ..models import User, File
from ..csv_processor import CSVProcessor
from ..database import get_db_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_new_file(file: UploadFile, user: User = Depends(get_current_user), service: DatabaseService = Depends(get_db_service)):
    wrong_file_type = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Wrong file type."
    )
    if file.content_type != "text/csv":
        raise wrong_file_type
    try:
        processor = CSVProcessor(file.file)
        new_file = await service.create_file(file.filename, user.id, ','.join(processor.column_names))
        await service.commit()
        tasks = []
        for row_number, row in enumerate(processor):
            print(row)
            for column_name, value in row.items():
                tasks.append(asyncio.create_task(service.create_data(new_file.id, column_name, row_number, value)))
        await asyncio.gather(*tasks)
        await service.commit()
    finally:
        file.file.close()
    return new_file.id

@router.get("/")
async def get_available_files(user: User = Depends(get_current_user), service: DatabaseService = Depends(get_db_service)):
    db_files = await service.get_files(user.id)
    return list(map(File.model_validate, db_files))

@router.delete("/{file_id}")
async def delete_file(file_id: str, user: User = Depends(get_current_user), service: DatabaseService = Depends(get_db_service)):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found"
        )
    if file.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not the owner of file with id {file_id}"
        )
    res = await service.delete_file(file.id)
    await service.commit()
    if not res:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{file_id}")
async def get_file_data(file_id: str, page_number: int = 0, page_size: int = 100, user: User = Depends(get_current_user), service: DatabaseService = Depends(get_db_service)):
    file = await service.get_file(UUID(file_id))
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found"
        )
    if file.owner_id != user.id:
        has_access = await service.has_access(file.id, user.id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not able to get data from file id {file_id}"
            )
    data_db = await service.get_data(file_id, offset=page_number*page_size, limit=page_size)
    data = defaultdict(list)
    for item in data_db:
        data[item.column_name].append(item.value)
    return data
