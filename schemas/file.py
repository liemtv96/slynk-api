from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    size: int
    content_type: Optional[str]
    storage_engine: str
    created_at: datetime