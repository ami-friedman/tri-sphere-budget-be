from sqlmodel import create_engine

from .db_models import *  # noqa: F403, F401
from app.core.config import settings


engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)


def init_db() -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    SQLModel.metadata.create_all(engine)
