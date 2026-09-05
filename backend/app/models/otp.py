import time
from sqlalchemy import Column, Integer, String, Boolean, Float
from backend.app.database import Base


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), index=True, nullable=False)
    temp_token = Column(String(128), unique=True, index=True, nullable=False)
    hashed_otp = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    expires_at = Column(Float, nullable=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    resend_count = Column(Integer, default=0)
    last_resend_at = Column(Float, nullable=False, default=time.time)
    is_used = Column(Boolean, default=False)
    created_at = Column(Float, nullable=False, default=time.time)

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def has_exceeded_attempts(self) -> bool:
        return self.attempts >= self.max_attempts
