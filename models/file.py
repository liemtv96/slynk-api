from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    share_id = Column(String, ForeignKey("shares.id"), nullable=True)
    reverse_share_id = Column(String, ForeignKey("reverse_shares.id"), nullable=True)

    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size = Column(Integer, default=0)
    storage_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    share = relationship("Share", back_populates="files")
    reverse_share = relationship("ReverseShare", back_populates="files")
