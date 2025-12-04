from fastapi import APIRouter, UploadFile, File as UploadFileType, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.file import File as FileModel
from models.reverse_share import ReverseShare
from routers.auth import get_current_user
from schemas.file import FileResponse
from storage.local import save_upload_file

router = APIRouter()

@router.post("/upload", response_model=list[FileResponse], summary="Upload files")
async def upload_files(
    files: list[UploadFile] = UploadFileType(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    results: list[FileModel] = []
    for f in files:
        file_id, storage_path = save_upload_file(f)
        m = FileModel(
            id=file_id,
            owner_id=current.id,
            filename=f.filename,
            content_type=f.content_type,
            size=0,
            storage_path=storage_path,
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
        file_id, storage_path = save_upload_file(f)
        m = FileModel(
            id=file_id,
            owner_id=rev.owner_id,
            filename=f.filename,
            content_type=f.content_type,
            size=0,
            storage_path=storage_path,
            reverse_share_id=reverse_id,
        )
        db.add(m)
        rev.received_files += 1
    db.commit()
    return {"status": "uploaded", "reverse_id": reverse_id}
