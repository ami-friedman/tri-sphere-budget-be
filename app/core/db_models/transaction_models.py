from sqlmodel import Field
from sqlmodel import SQLModel


class ExpTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    expense_budget_id: int = Field(default=None, nullable=False, foreign_key='expbudget.id', ondelete='CASCADE')
    amount: float = Field(default=None, nullable=False)


class IncTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    income_budget_id: int = Field(default=None, nullable=False, foreign_key='incbudget.id')
    amount: float = Field(default=None, nullable=False)
