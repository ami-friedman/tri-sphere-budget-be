from typing import Optional

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpenseCategoryGroupBase(SQLModel):
    name: str = Field(default=None)


class ExpenseCategoryGroupCreate(ExpenseCategoryGroupBase):
    pass


class ExpenseCategoryGroup(ExpenseCategoryGroupBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ExpenseCategoryGroupPublic(ExpenseCategoryGroupBase):
    id: int = Field(default=None)


class ExpenseCategoryBase(SQLModel):
    name: str = Field(default=None)


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategory(ExpenseCategoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ExpenseCategoryPublic(ExpenseCategoryBase):
    id: int = Field(default=None)


class IncomeCategoryBase(SQLModel):
    name: str = Field(default=None)


class IncomeCategoryCreate(IncomeCategoryBase):
    pass


class IncomeCategory(IncomeCategoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class IncomeCategoryPublic(IncomeCategoryBase):
    id: int = Field(default=None)
