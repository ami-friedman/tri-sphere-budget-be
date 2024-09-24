from datetime import date

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpenseBudget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='expensecategory.id')
    category_group_id: int = Field(default=None, nullable=False, foreign_key='expensecategorygroup.id')
    amount: float = Field(default=None, nullable=False)


class IncomeBudget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='incomecategory.id', ondelete="CASCADE")
    amount: float = Field(default=None, nullable=False)
