import json
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True, default="")
    password_hash = Column(String(255), nullable=True, default="")
    password_salt = Column(String(255), nullable=True, default="")
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    picture = Column(String(1024), nullable=True, default="")
    profile_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        profile = {}
        if self.profile_data:
            try:
                profile = json.loads(self.profile_data)
            except Exception:
                profile = {}

        return {
            "id": self.id,
            "email": self.email,
            "name": self.name or (profile.get("fullName") if profile else self.email.split("@")[0]),
            "isVerified": self.is_verified,
            "emailVerified": self.email_verified,
            "picture": self.picture or (profile.get("picture") if profile else ""),
            "profile": profile or {
                "fullName": self.name,
                "emailAddress": self.email,
                "picture": self.picture
            }
        }
