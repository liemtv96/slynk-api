import os
import shutil
from uuid import uuid4

from core.config import settings

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
def save_upload_file(file) -> tuple[str, str]:
    file_id = str(uuid4())
    dest_path = os.path.join(settings.UPLOAD_DIR, file_id)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_id, dest_path
