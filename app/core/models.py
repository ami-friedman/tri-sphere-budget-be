from datetime import date

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpenseCategoryGroup(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None)


class ExpenseCategory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None)


class ExpenseBudget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='expensecategory.id')
    category_group_id: int = Field(default=None, nullable=False, foreign_key='expensecategorygroup.id')
    amount: float = Field(default=None, nullable=False)

    class Config:
        arbitrary_types_allowed = True


class ExpenseTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    expense_budget_id: int = Field(default=None, nullable=False, foreign_key='expensebudget.id')
    amount: float = Field(default=None, nullable=False)
