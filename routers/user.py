from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database_sql import get_db
from models.user import User
from models.user_settings import UserSettings
from routers.auth import get_current_user
from schemas.user import Settings, SettingsUpdate

router = APIRouter()

@router.get("/settings", response_model=Settings, summary="Get notification settings")
def get_settings(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current.id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.patch("/settings", summary="Update notification settings")
def update_settings(
    payload: SettingsUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current.id).first()
    if not settings:
        settings = UserSettings(user_id=current.id)
        db.add(settings)

    for field, value in payload.dict(exclude_none=True).items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return {"status": "updated"}


@router.delete("/delete", summary="Delete account")
def delete_account(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current)
    db.commit()
    return {"status": "account_deleted"}
