from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class FileResponse(BaseModel):
    id: str
    filename: str
    size: int
    content_type: Optional[str]
    storage_engine: str
    created_at: datetime