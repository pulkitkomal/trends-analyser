from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(topic)").fetchall()}
            if "user_id" not in cols:
                conn.exec_driver_sql("ALTER TABLE topic ADD COLUMN user_id INTEGER")
                conn.commit()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
