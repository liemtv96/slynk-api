from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class CreateShareRequest(BaseModel):
    file_ids: List[str]
    expires_at: Optional[datetime] = None


class ShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    link: str
    file_ids: list[str]
    expires_at: Optional[datetime]
    views: int
