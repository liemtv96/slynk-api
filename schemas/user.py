from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    id: str
    email: EmailStr
    username: str
    email_verified: bool
    twofa_enabled: bool

    class Config:
        orm_mode = True


class Settings(BaseModel):
    email_updates: bool
    notify_expiration: bool
    notify_reverse_upload: bool

    class Config:
        orm_mode = True


class SettingsUpdate(BaseModel):
    email_updates: Optional[bool] = None
    notify_expiration: Optional[bool] = None
    notify_reverse_upload: Optional[bool] = None
