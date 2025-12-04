from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.reverse_share import ReverseShare
from routers.auth import get_current_user
from schemas.reverse_share import CreateReverseRequest, ReverseResponse

router = APIRouter()

@router.post("/", response_model=ReverseResponse, summary="Create reverse share")
def create_reverse(
    payload: CreateReverseRequest,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    rid = str(uuid4())
    link = rid[:8]

    rev = ReverseShare(
        id=rid,
        owner_id=current.id,
        name=payload.name,
        link=link,
        expires_at=payload.expires_at,
        max_files=payload.max_files,
        received_files=0,
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return rev


@router.get("/", response_model=list[ReverseResponse], summary="List reverse shares")
def list_reverse(db: Session = Depends(get_db), current=Depends(get_current_user)):
    revs = db.query(ReverseShare).filter(ReverseShare.owner_id == current.id).all()
    return revs
