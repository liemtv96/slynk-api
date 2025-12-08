from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from core.database_sql import Base

class Share(Base):
    __tablename__ = "shares"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    link = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
