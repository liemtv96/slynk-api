from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from core.database_sql import Base

class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size = Column(Integer, default=0)
    storage_engine = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    share_id = Column(String, ForeignKey("shares.id"), nullable=True)
    reverse_share_id = Column(String, ForeignKey("reverse_shares.id"), nullable=True)
