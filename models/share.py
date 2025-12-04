from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class Share(Base):
    __tablename__ = "shares"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    link = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="shares")
    files = relationship("File", back_populates="share")
