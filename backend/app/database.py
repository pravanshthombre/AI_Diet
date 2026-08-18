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
engine = None

if _is_postgres:
    try:
        temp_engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=280,
            pool_size=5,
            max_overflow=10,
        )
        # Test connection with 5-second timeout
        with temp_engine.connect() as conn:
            pass
        engine = temp_engine
        print("[DATABASE] Successfully connected to PostgreSQL (Supabase)!")
    except Exception as pg_err:
        print(f"[DATABASE WARNING] Could not connect to PostgreSQL ({pg_err}).")
        print("[DATABASE] Falling back to SQLite to keep service online.")
        _is_postgres = False

if not engine:
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///./nutricalc.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    print("[DATABASE] Running on local SQLite engine.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


