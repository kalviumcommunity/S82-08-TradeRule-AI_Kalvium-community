"""
Database models, engine configuration, and session management for TradeRule AI.
Supports SQLite (local development) and PostgreSQL (production).
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from sqlalchemy import Boolean, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ============================================================
# DATABASE URL RESOLUTION
# ============================================================

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent.parent

DEFAULT_SQLITE_PATH = PROJECT_ROOT / "data" / "traderule.db"
DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

raw_db_url = os.getenv("DATABASE_URL")

if raw_db_url:
    # Render and some providers provide postgres:// which SQLAlchemy 1.4+ expects as postgresql://
    if raw_db_url.startswith("postgres://"):
        DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = raw_db_url
else:
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

is_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, default="")
    role = Column(String(50), nullable=False, default="user")  # "user" or "admin"
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# USER REPOSITORY HELPERS
# ============================================================

def get_user_by_email(db: Session, email: str) -> User | None:
    norm_email = email.strip().lower()
    return db.query(User).filter(User.email == norm_email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password_hash: str,
    full_name: str = "",
    role: str = "user",
) -> User:
    norm_email = email.strip().lower()
    user = User(
        email=norm_email,
        password_hash=password_hash,
        full_name=full_name.strip(),
        role=role if role in {"user", "admin"} else "user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
