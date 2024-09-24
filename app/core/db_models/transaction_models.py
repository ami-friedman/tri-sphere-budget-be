from sqlmodel import Field
from sqlmodel import SQLModel


class ExpenseTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    expense_budget_id: int = Field(default=None, nullable=False, foreign_key='expensebudget.id', ondelete='CASCADE')
    amount: float = Field(default=None, nullable=False)


class IncomeTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    income_budget_id: int = Field(default=None, nullable=False, foreign_key='incomebudget.id')
    amount: float = Field(default=None, nullable=False)
