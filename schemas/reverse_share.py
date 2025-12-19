from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class CreateReverseRequest(BaseModel):
    name: str
    max_files: int = 0
    expires_at: Optional[datetime] = None


class ReverseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    link: str
    expires_at: Optional[datetime]
    max_files: int
    received_files: int
