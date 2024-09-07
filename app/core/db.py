from sqlmodel import create_engine

from app.core.config import settings
from app.core.models import ExpenseBudget  # noqa: F401
from app.core.models import ExpenseCategory  # noqa: F401
from app.core.models import ExpenseCategoryGroup  # noqa: F401
from app.core.models import ExpenseTransaction  # noqa: F401


engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)


def init_db() -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    SQLModel.metadata.create_all(engine)
