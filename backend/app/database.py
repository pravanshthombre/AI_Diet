"""
SQLAlchemy database engine and session management.
Uses SQLite by default; set DATABASE_URL in .env or environment for Supabase / PostgreSQL.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env from backend directory or project root
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nutricalc.db",
).strip()

# Normalize schema prefix (SQLAlchemy 1.4+ requires postgresql:// instead of postgres://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure SSL mode for Supabase / remote PostgreSQL if not already present
if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL and "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

# Connect arguments
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

_is_postgres = "postgresql" in DATABASE_URL

if _is_postgres:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,       # Detect and replace stale connections
        pool_recycle=280,         # Recycle connections before Supabase 5-min timeout
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite: use NullPool to avoid connection exhaustion in single-threaded mode
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        poolclass=StaticPool,
    )

print(f"[DATABASE] Engine configured: {'PostgreSQL (Supabase)' if _is_postgres else 'SQLite (local)'}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


