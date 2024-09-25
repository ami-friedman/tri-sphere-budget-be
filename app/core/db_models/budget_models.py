from datetime import date

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpBudget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='expcat.id')
    category_group_id: int = Field(default=None, nullable=False, foreign_key='expcatgroup.id')
    amount: float = Field(default=None, nullable=False)


class IncBudget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='inccat.id', ondelete="CASCADE")
    amount: float = Field(default=None, nullable=False)
