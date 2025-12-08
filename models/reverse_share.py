from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from core.database_sql import Base

class ReverseShare(Base):
    __tablename__ = "reverse_shares"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    link = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    max_files = Column(Integer, default=0)
    received_files = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
