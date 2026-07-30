from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = "sqlite:///./backend/retail_voice.db"


engine = create_engine(DATABASE_URL)


def enable_sqlite_foreign_keys(target_engine: Engine) -> None:
    """Turn on SQLite foreign-key enforcement for every connection.

    SQLite does not enforce FOREIGN KEY constraints unless
    "PRAGMA foreign_keys=ON" is run per connection, so without this a
    CallRecord or Order could silently reference a non-existent
    customer_id. Applied to both the app engine and any test engine.
    """

    @event.listens_for(target_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


enable_sqlite_foreign_keys(engine)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()