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


class ExpenseTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    expense_budget_id: int = Field(default=None, nullable=False, foreign_key='expensebudget.id', ondelete='CASCADE')
    amount: float = Field(default=None, nullable=False)


class IncomeCategory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None)


class IncomeBudget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='incomecategory.id', ondelete="CASCADE")
    amount: float = Field(default=None, nullable=False)


class IncomeTransaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    income_budget_id: int = Field(default=None, nullable=False, foreign_key='incomebudget.id')
    amount: float = Field(default=None, nullable=False)
