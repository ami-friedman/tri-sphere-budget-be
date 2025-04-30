from typing import Optional

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpTransactionBase(SQLModel):
    expense_budget_id: int = Field(default=None, nullable=False, foreign_key='expense_budget.id', ondelete='CASCADE')
    amount: float = Field(default=None, nullable=False)


class ExpTransactionCreate(ExpTransactionBase):
    pass


class ExpTransaction(ExpTransactionBase, table=True):
    __tablename__ = "expense_transaction"
    id: Optional[int] = Field(default=None, primary_key=True)


class ExpTransactionPub(ExpTransactionBase):
    id: int = Field(default=None, primary_key=True)


class IncTransactionBase(SQLModel):
    income_budget_id: int = Field(default=None, nullable=False, foreign_key='income_budget.id')
    amount: float = Field(default=None, nullable=False)


class IncTransactionCreate(IncTransactionBase):
    pass


class IncTransaction(IncTransactionBase, table=True):
    __tablename__ = "income_transaction"
    id: Optional[int] = Field(default=None, primary_key=True)


class IncTransactionPub(IncTransactionBase):
    id: int = Field(default=None, primary_key=True)
