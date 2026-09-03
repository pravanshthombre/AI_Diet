"""
SQLAlchemy database engine and session management.

Resolution order:
  1. If DATABASE_URL is set, use it (PostgreSQL on Supabase in production).
     The `postgres://` scheme is normalized to `postgresql://`, and SSL is
     auto-enabled for remote hosts (non-localhost / non-127.0.0.1).
  2. Otherwise, fall back to a local SQLite file at backend/nutricalc.db
     so the test suite and local development work out of the box.

The engine is created lazily on first import so misconfiguration never
prevents the module from being imported (e.g., during pytest collection).
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env from backend directory or project root
load_dotenv()


def _build_engine() -> Engine:
    """Construct the SQLAlchemy engine using DATABASE_URL or a SQLite fallback."""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        database_url = database_url.strip()

        # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        # Ensure SSL for remote Postgres (Supabase) unless explicitly disabled
        if (
            "postgresql" in database_url
            and "sslmode" not in database_url
            and "localhost" not in database_url
            and "127.0.0.1" not in database_url
        ):
            sep = "&" if "?" in database_url else "?"
            database_url = f"{database_url}{sep}sslmode=require"

        return create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=280,
            pool_size=5,
            max_overflow=10,
        )

    # Fallback: local SQLite file in the backend directory.
    sqlite_path = Path(__file__).resolve().parent.parent / "nutricalc.db"
    return create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


def ensure_schema_columns(target_engine: Engine):
    """Auto-migrate missing columns for existing tables (Supabase PostgreSQL / SQLite)."""
    try:
        from sqlalchemy import text
        with target_engine.connect() as conn:
            # Check dialect
            dialect_name = target_engine.dialect.name
            if dialect_name == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS supabase_uid VARCHAR;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_supabase_uid ON users (supabase_uid);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);"))
                conn.commit()
            elif dialect_name == "sqlite":
                # Check existing columns in users table if table exists
                cols_res = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                existing_cols = {col[1] for col in cols_res}
                if existing_cols:
                    if "supabase_uid" not in existing_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN supabase_uid TEXT;"))
                    if "email" not in existing_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN email TEXT;"))
                conn.commit()
    except Exception as e:
        print(f"[SCHEMA NOTICE] Auto-migration check: {e}")


engine: Engine = _build_engine()
ensure_schema_columns(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

