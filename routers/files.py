import os
from datetime import datetime

from fastapi import APIRouter, UploadFile, File as UploadFileType, Depends, HTTPException
from fastapi.responses import FileResponse as StreamingFileResponse
from sqlalchemy.orm import Session

from core.config import settings
from core.database_sql import get_db
from models.file import File as FileModel
from models.reverse_share import ReverseShare
from models.share import Share
from routers.auth import get_current_user
from schemas.file import FileResponse
from storage import delete_file, generate_download_url, save_upload_file

router = APIRouter()

@router.post("/upload", response_model=list[FileResponse], summary="Upload files")
async def upload_files(
    files: list[UploadFile] = UploadFileType(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    results: list[FileModel] = []
    for f in files:
        file_id, storage_key, size = save_upload_file(f)
        m = FileModel(
            id=file_id,
            owner_id=current.id,
            filename=f.filename,
            content_type=f.content_type,
            size=size,
            storage_engine=settings.STORAGE_ENGINE,
            storage_key=storage_key,
        )
        db.add(m)
        results.append(m)
    db.commit()
    return results


@router.post("/upload/reverse/{reverse_id}", summary="Upload to reverse share")
async def upload_reverse(
    reverse_id: str,
    files: list[UploadFile] = UploadFileType(...),
    db: Session = Depends(get_db),
):
    rev = db.query(ReverseShare).filter(ReverseShare.id == reverse_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Reverse share not found")
    for f in files:
        file_id, storage_key, size = save_upload_file(f)
        m = FileModel(
            id=file_id,
            owner_id=rev.owner_id,
            filename=f.filename,
            content_type=f.content_type,
            size=size,
            storage_engine=settings.STORAGE_ENGINE,
            storage_key=storage_key,
            reverse_share_id=reverse_id,
        )
        db.add(m)
        rev.received_files += 1
    db.commit()
    return {"status": "uploaded", "reverse_id": reverse_id}


@router.get("", response_model=list[FileResponse], summary="List my files")
def list_files(
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    return (
        db.query(FileModel)
        .filter(FileModel.owner_id == current.id)
        .order_by(FileModel.created_at.desc())
        .all()
    )

@router.get("/{file_id}", response_model=FileResponse, summary="Get file info")
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    file = (
        db.query(FileModel)
        .filter(
            FileModel.id == file_id,
            FileModel.owner_id == current.id,
        )
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.get("/{file_id}/url", summary="Get file download URL")
def get_file_url(
    file_id: str,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    file = (
        db.query(FileModel)
        .filter(
            FileModel.id == file_id,
            FileModel.owner_id == current.id,
        )
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    url = generate_download_url(
        storage_key=file.storage_key,
        expires_at=None,
    )
    return {"url": url}


@router.get("/share/{share_token}/{file_id}", summary="Download via share")
def get_file_via_share(
    share_token: str,
    file_id: str,
    db: Session = Depends(get_db),
):
    share = (
        db.query(Share)
        .filter(Share.link == share_token)
        .first()
    )

    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    if share.expires_at and share.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="Share expired")
    file = (
        db.query(FileModel)
        .filter(
            FileModel.id == file_id,
            FileModel.owner_id == share.owner_id,
        )
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    share.views += 1
    db.commit()
    url = generate_download_url(
        storage_key=file.storage_key,
        expires_at=share.expires_at,
    )
    return {"url": url}


@router.delete("/{file_id}", summary="Delete file")
def delete_file_endpoint(
    file_id: str,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    file = (
        db.query(FileModel)
        .filter(
            FileModel.id == file_id,
            FileModel.owner_id == current.id,
        )
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    delete_file(file.storage_key)
    db.delete(file)
    db.commit()
    return {"status": "deleted", "file_id": file_id}

@router.get("/download/{storage_key:path}", summary="Download stored file (local storage)")
def download_file(storage_key: str):
    if settings.STORAGE_ENGINE != "local":
        raise HTTPException(status_code=404, detail="Download route only valid for local storage")

    base_dir = os.path.abspath(settings.UPLOAD_DIR)
    full_path = os.path.abspath(os.path.join(base_dir, storage_key))
    if not full_path.startswith(base_dir + os.sep) and full_path != base_dir:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    filename = os.path.basename(full_path)
    return StreamingFileResponse(full_path, filename=filename)