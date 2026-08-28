from collections.abc import Generator

from sqlalchemy import Enum, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def str_enum(enum_cls):
    """SQLAlchemy's Enum column type persists a Python enum member's NAME
    by default (WorkflowStage.SURVEY -> "SURVEY"), not its value -- easy to
    miss for a `class X(str, Enum)` whose members already equal their
    lowercase value everywhere else in Python. On SQLite (no CHECK
    constraint by default in SQLAlchemy 2.0) this goes unnoticed; against a
    real Postgres native enum type -- whose labels are the lowercase
    values, per every migration in alembic/versions/ -- inserting the
    default-cased name fails outright. values_callable makes the stored
    representation match what the migrations actually declared.
    """
    return Enum(enum_cls, values_callable=lambda cls: [member.value for member in cls])


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
