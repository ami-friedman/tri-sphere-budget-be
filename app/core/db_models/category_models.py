from typing import Optional

from sqlmodel import Field
from sqlmodel import SQLModel


class ExpCatGroupBase(SQLModel):
    name: str = Field(default=None)


class ExpCatGroupCreate(ExpCatGroupBase):
    pass


class ExpCatGroup(ExpCatGroupBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ExpCatGroupPub(ExpCatGroupBase):
    id: int = Field(default=None)


class ExpCatBase(SQLModel):
    name: str = Field(default=None)


class ExpCatCreate(ExpCatBase):
    pass


class ExpCat(ExpCatBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ExpCatPub(ExpCatBase):
    id: int = Field(default=None)


class IncCatBase(SQLModel):
    name: str = Field(default=None)


class IncCatCreate(IncCatBase):
    pass


class IncCat(IncCatBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class IncCatPub(IncCatBase):
    id: int = Field(default=None)
