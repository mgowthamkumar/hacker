import json
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings, BASE_DIR

logger = logging.getLogger("autohire.database")

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes database schema and imports existing users from users.json."""
    from backend.app.models.user import User
    from backend.app.models.otp import OTPRecord

    Base.metadata.create_all(bind=engine)

    users_json_path = BASE_DIR / "users.json"
    if users_json_path.exists():
        db = SessionLocal()
        try:
            with open(users_json_path, "r", encoding="utf-8") as f:
                users_data = json.load(f)

            for item in users_data:
                email = str(item.get("email") or "").strip().lower()
                if not email:
                    continue

                existing = db.query(User).filter(User.email == email).first()
                if not existing:
                    profile = item.get("profile") or {}
                    user = User(
                        id=str(item.get("id") or ""),
                        email=email,
                        name=item.get("name") or profile.get("fullName") or email.split("@")[0],
                        password_hash=item.get("passwordHash") or "",
                        password_salt=item.get("passwordSalt") or "",
                        is_verified=bool(item.get("isVerified", False)),
                        email_verified=bool(item.get("emailVerified", False)),
                        picture=profile.get("picture") or item.get("picture") or "",
                        profile_data=json.dumps(profile) if profile else None
                    )
                    db.add(user)
            db.commit()
            logger.info("Database initialized and users.json records verified.")
        except Exception as e:
            db.rollback()
            logger.warning(f"Notice importing users.json to database: {e}")
        finally:
            db.close()
