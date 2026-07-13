from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import DATABASE_URL

_is_sqlite = "sqlite" in DATABASE_URL

_engine_kwargs: dict = {
    "connect_args": {"check_same_thread": False} if _is_sqlite else {},
    "echo": False,
}
if not _is_sqlite:
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 40

engine = create_engine(DATABASE_URL, **_engine_kwargs)

if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.database.models import Job, Comment, Cluster  # noqa
    Base.metadata.create_all(bind=engine)
