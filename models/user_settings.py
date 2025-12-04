from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    email_updates = Column(Boolean, default=True)
    notify_expiration = Column(Boolean, default=True)
    notify_reverse_upload = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")
