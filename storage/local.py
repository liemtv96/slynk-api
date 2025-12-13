import os
import uuid
from fastapi import UploadFile
from core.config import settings

def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
    file_id = str(uuid.uuid4())
    storage_key = f"{file_id}/{file.filename}"
    full_path = os.path.join(settings.UPLOAD_DIR, storage_key)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    size = 0
    with open(full_path, "wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            size += len(chunk)
            buffer.write(chunk)

    return file_id, storage_key, size
