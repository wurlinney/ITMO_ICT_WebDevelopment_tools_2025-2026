import os
from sqlmodel import SQLModel, Session, create_engine

# Prefer external DB config if provided; fallback keeps local startup working.
db_url = os.getenv("DATABASE_URL", "sqlite:///./warriors.db")
engine = create_engine(db_url, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
