from datetime import date
from typing import Optional

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpBudgetBase(SQLModel):
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='expcat.id')
    category_group_id: int = Field(default=None, nullable=False, foreign_key='expcatgroup.id')
    amount: float = Field(default=None, nullable=False)


class ExpBudgetCreate(ExpBudgetBase):
    pass


class ExpBudget(ExpBudgetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ExpBudgetPub(ExpBudgetBase):
    id: int = Field(default=None)
    name: str = Field(default=None)
    category_group: str = Field(default=None)


class MonthlyBudgetRes(SQLModel):
    total: float = Field(default=0)
    category_group_id: int = Field(default=None)
    breakdown: list[ExpBudgetPub] = Field(default=[])


class IncBudgetBase(SQLModel):
    month: date = Field(default=None, nullable=False)
    category_id: int = Field(default=None, nullable=False, foreign_key='inccat.id', ondelete="CASCADE")
    amount: float = Field(default=None, nullable=False)


class IncBudgetCreate(IncBudgetBase):
    pass


class IncBudget(IncBudgetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class IncBudgetPub(IncBudgetBase):
    id: int = Field(default=None)
