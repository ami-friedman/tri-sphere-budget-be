import enum
from uuid import UUID, uuid4
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, ForeignKey, text, Enum as SAEnum
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.types import TypeDecorator, CHAR
from datetime import datetime, date

class UUIDBinary(TypeDecorator):
    impl = CHAR(32)
    cache_ok = True
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(BINARY(16))
    def process_bind_param(self, value: UUID, dialect):
        return value.bytes if value else None
    def process_result_value(self, value, dialect):
        return UUID(bytes=value) if value else None

class CategoryType(str, enum.Enum):
    CASH = "Cash"
    MONTHLY = "Monthly"
    SAVINGS = "Savings"
    TRANSFER = "Transfer"
    INCOME = "Income"

class AccountType(str, enum.Enum):
    CHECKING = "Checking"
    SAVINGS = "Savings"

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, sa_column=Column(UUIDBinary, primary_key=True))
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": text("CURRENT_TIMESTAMP"), "server_default": text("CURRENT_TIMESTAMP")})
    accounts: List["Account"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    monthly_budgets: List["MonthlyBudget"] = Relationship(back_populates="user")
    pending_transactions: List["PendingTransaction"] = Relationship(back_populates="user")

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
    id: UUID = Field(default_factory=uuid4, sa_column=Column(UUIDBinary, primary_key=True))
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    name: str
    type: AccountType = Field(sa_column=Column(SAEnum(AccountType)))
    initial_balance: float = Field(default=0.00)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})
    user: User = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(back_populates="account")

class CategoryBase(SQLModel):
    name: str
    type: CategoryType = Field(sa_column=Column(SAEnum(CategoryType, values_callable=lambda obj: [e.value for e in obj])))
    budgeted_amount: float = Field(default=0.00)

class Category(CategoryBase, table=True):
    __tablename__ = "categories"
    id: UUID = Field(default_factory=uuid4, sa_column=Column(UUIDBinary, primary_key=True))
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})
    user: "User" = Relationship(back_populates="categories")
    transactions: List["Transaction"] = Relationship(back_populates="category")
    monthly_budgets: List["MonthlyBudget"] = Relationship(back_populates="category")

class CategoryCreate(CategoryBase): pass
class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    type: Optional[CategoryType] = None
    budgeted_amount: Optional[float] = None
class CategoryPublic(CategoryBase):
    id: UUID
    created_at: datetime

class MonthlyBudget(SQLModel, table=True):
    __tablename__ = "monthly_budgets"
    id: UUID = Field(default_factory=uuid4, sa_column=Column(UUIDBinary, primary_key=True))
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    category_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("categories.id")))
    year: int
    month: int
    budgeted_amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": text("CURRENT_TIMESTAMP"), "server_default": text("CURRENT_TIMESTAMP")})
    user: User = Relationship(back_populates="monthly_budgets")
    category: Category = Relationship(back_populates="monthly_budgets")

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: UUID = Field(default_factory=uuid4, sa_column=Column(UUIDBinary, primary_key=True))
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    account_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("accounts.id")))
    category_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("categories.id")))
    amount: float
    description: Optional[str] = None
    transaction_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})
    user: User = Relationship(back_populates="transactions")
    account: Account = Relationship(back_populates="transactions")
    category: Category = Relationship(back_populates="transactions")

class TransactionCreate(SQLModel):
    account_id: UUID
    category_id: UUID
    amount: float
    description: Optional[str] = None
    transaction_date: date

class TransactionUpdate(SQLModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None

class TransactionPublic(TransactionCreate):
    id: UUID
    created_at: datetime


class PendingTransaction(SQLModel, table=True):
    __tablename__ = "pending_transactions"
    id: UUID = Field(default_factory=uuid4, sa_column=Column(UUIDBinary, primary_key=True))
    user_id: UUID = Field(sa_column=Column(UUIDBinary, ForeignKey("users.id")))
    statement_description: str
    transaction_date: date
    amount: float
    # NEW: Field to store the target account type
    target_account_type: AccountType = Field(sa_column=Column(SAEnum(AccountType)))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})

    user: User = Relationship(back_populates="pending_transactions")


class PendingTransactionPublic(SQLModel):
    id: UUID
    statement_description: str
    transaction_date: date
    amount: float


class FinalizeTransaction(SQLModel):
    pending_transaction_id: UUID
    account_id: UUID
    category_id: UUID

