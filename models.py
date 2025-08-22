from uuid import UUID, uuid4
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine
from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.types import TypeDecorator, CHAR
from datetime import datetime, date

# Custom UUID Type for MySQL
class UUIDBinary(TypeDecorator):
    impl = CHAR(32)

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(BINARY(16))

    def process_bind_param(self, value: UUID, dialect):
        if value is None:
            return value
        return value.bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return UUID(bytes=value)


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(UUIDBinary, primary_key=True, default=uuid4)
    )
    hashed_password: str
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": "NOW()", "server_default": text("CURRENT_TIMESTAMP")}
    )

    accounts: List["Account"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class UserPublic(UserBase):
    id: UUID
    created_at: datetime

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str

class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(UUIDBinary, primary_key=True, default=uuid4)
    )
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    name: str
    initial_balance: float = Field(default=0.00)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

    user: User = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(back_populates="account")

class Category(SQLModel, table=True):
    __tablename__ = "categories"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(UUIDBinary, primary_key=True, default=uuid4)
    )
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    name: str
    type: str
    budgeted_amount: float = Field(default=0.00)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

    user: User = Relationship(back_populates="categories")
    transactions: List["Transaction"] = Relationship(back_populates="category")

# Pydantic schema for Category creation
class CategoryCreate(SQLModel):
    name: str
    type: str
    budgeted_amount: float = 0.00

# Pydantic schema for Category update - all fields are optional
class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    type: Optional[str] = None
    budgeted_amount: Optional[float] = None

# Pydantic schema for returning Category data
class CategoryPublic(CategoryCreate):
    id: UUID
    created_at: datetime

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(UUIDBinary, primary_key=True, default=uuid4)
    )
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    account_id: Optional[UUID] = Field(sa_column=Column(UUIDBinary, ForeignKey("accounts.id"), nullable=True))
    category_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("categories.id")))
    amount: float
    description: Optional[str]
    transaction_date: date
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

    user: User = Relationship(back_populates="transactions")
    account: Optional[Account] = Relationship(back_populates="transactions")
    category: Category = Relationship(back_populates="transactions")

# Pydantic schema for Transaction creation
class TransactionCreate(SQLModel):
    category_id: UUID
    amount: float
    description: Optional[str]
    transaction_date: date

# Pydantic schema for Transaction update - all fields are optional
class TransactionUpdate(SQLModel):
    category_id: Optional[UUID] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None

# Pydantic schema for returning Transaction data
class TransactionPublic(TransactionCreate):
    id: UUID
    created_at: datetime

# Pydantic schema for Transfer creation
class TransferCreate(SQLModel):
    category_id: UUID
    amount: float
    description: Optional[str] = None
    transaction_date: date

# Pydantic schema for returning Transfer data
class TransferPublic(TransferCreate):
    id: UUID
    created_at: datetime