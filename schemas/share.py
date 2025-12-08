from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class CreateShareRequest(BaseModel):
    file_ids: List[str]
    expires_at: Optional[datetime] = None


class ShareResponse(BaseModel):
    id: str
    link: str
    file_ids: list[str]
    expires_at: Optional[datetime]
    views: int
