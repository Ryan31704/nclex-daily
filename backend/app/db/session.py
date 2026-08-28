from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()
engine_options: dict[str, object] = {"pool_pre_ping": True}
if settings.database_serverless:
    # Vercel instances are transient, so Supabase's transaction pooler owns the
    # reusable connections. Supavisor transaction mode also requires prepared
    # statements to be disabled for psycopg.
    engine_options.update(
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
