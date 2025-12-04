from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.share import Share
from models.file import File as FileModel
from routers.auth import get_current_user
from schemas.share import CreateShareRequest, ShareResponse

router = APIRouter()

@router.post("/", response_model=ShareResponse, summary="Create share")
def create_share(
    payload: CreateShareRequest,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    share_id = str(uuid4())
    link = share_id[:8]

    share = Share(
        id=share_id,
        owner_id=current.id,
        link=link,
        expires_at=payload.expires_at,
    )
    db.add(share)

    if payload.file_ids:
        db.query(FileModel).filter(FileModel.id.in_(payload.file_ids)).update(
            {"share_id": share_id},
            synchronize_session=False,
        )

    db.commit()
    db.refresh(share)
    return ShareResponse(
        id=share.id,
        link=share.link,
        file_ids=payload.file_ids,
        expires_at=share.expires_at,
        views=share.views,
    )


@router.get("/", summary="List my shares")
def list_shares(db: Session = Depends(get_db), current=Depends(get_current_user)):
    shares = db.query(Share).filter(Share.owner_id == current.id).all()
    result: list[ShareResponse] = []
    for s in shares:
        file_ids = [f.id for f in s.files]
        result.append(
            ShareResponse(
                id=s.id,
                link=s.link,
                file_ids=file_ids,
                expires_at=s.expires_at,
                views=s.views,
            )
        )
    return result


@router.delete("/{share_id}", summary="Delete share")
def delete_share(share_id: str, db: Session = Depends(get_db), current=Depends(get_current_user)):
    s = db.query(Share).filter(Share.id == share_id, Share.owner_id == current.id).first()
    if not s:
        return {"status": "not_found"}
    db.delete(s)
    db.commit()
    return {"status": "deleted"}
