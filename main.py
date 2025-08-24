import os
from contextlib import asynccontextmanager
from operator import or_
from typing import AsyncGenerator, List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone, date

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, SQLModel, create_engine, select

from models import (
    User, UserCreate, UserPublic, Token, Account, Category, CategoryCreate,
    CategoryPublic, CategoryUpdate, Transaction, TransactionCreate,
    TransactionPublic, TransactionUpdate, CategoryType, MonthlyBudget
)

load_dotenv()

DATABASE_URL_STR = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:P%40ssw0rd@localhost/trisphere_budget")


def create_database(url_str: str):
    db_url = make_url(url_str)
    db_name = db_url.database
    temp_url = db_url.set(database='information_schema')
    temp_engine = create_engine(temp_url, echo=False)
    with temp_engine.connect() as connection:
        result = connection.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'"))
        if not result.scalar():
            connection.execute(text(f"CREATE DATABASE {db_name}"))
            connection.commit()


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_database(DATABASE_URL_STR)
    engine = create_engine(DATABASE_URL_STR, echo=True)
    create_db_and_tables(engine)
    app.state.engine = engine
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-please-change")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=365))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_session():
    engine = app.state.engine
    with Session(engine) as session:
        yield session


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.username == user_create.username)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    if session.exec(select(User).where(User.email == user_create.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed_password = get_password_hash(user_create.password)
    db_user = User(username=user_create.username, email=user_create.email, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


# ** THIS FUNCTION IS FIXED **
@app.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token_expires = timedelta(days=365)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Using the same token for refresh for simplicity, with its own long expiry
    refresh_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(days=365))

    return Token(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        refresh_token=refresh_token
    )


@app.post("/categories", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(category_create: CategoryCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(select(Category).where(Category.user_id == user.id, Category.name == category_create.name,
                                                   Category.type == category_create.type)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"A category named '{category_create.name}' with type '{category_create.type}' already exists.")

    db_category = Category.model_validate(category_create, update={"user_id": user.id})
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@app.put("/categories/{category_id}", response_model=CategoryPublic)
def update_category(category_id: UUID, category_update: CategoryUpdate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    db_category = session.exec(select(Category).where(Category.id == category_id, Category.user_id == user.id)).first()
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for key, value in category_update.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_category = session.exec(select(Category).where(Category.id == category_id, Category.user_id == user.id)).first()
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    if session.exec(select(Transaction).where(Transaction.category_id == category_id)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Cannot delete category. It is currently in use by one or more transactions.")

    session.delete(db_category)
    session.commit()


@app.get("/categories", response_model=List[CategoryPublic])
def get_categories(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(Category).where(Category.user_id == user.id)).all()


@app.post("/transactions", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction_create: TransactionCreate, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    category = session.get(Category, transaction_create.category_id)
    if not category or category.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or does not belong to the user")

    db_transaction = Transaction.model_validate(transaction_create, update={"user_id": user.id})
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


@app.put("/transactions/{transaction_id}", response_model=TransactionPublic)
def update_transaction(transaction_id: UUID, transaction_update: TransactionUpdate, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id)).first()
    if not db_transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    for key, value in transaction_update.model_dump(exclude_unset=True).items():
        setattr(db_transaction, key, value)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id)).first()
    if not db_transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    session.delete(db_transaction)
    session.commit()


@app.get("/transactions", response_model=List[TransactionPublic])
def get_transactions(year: int, month: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)
    return session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.transaction_date >= start_date,
                                                  Transaction.transaction_date < end_date)).all()


@app.get("/transfers", response_model=List[TransactionPublic])
def get_transfers(year: int, month: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Fetches transactions that are categorized as 'Savings' or 'Transfer'.
    """
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    statement = (
        select(Transaction)
        .join(Category)
        .where(
            Transaction.user_id == user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date,
            or_(Category.type == CategoryType.SAVINGS, Category.type == CategoryType.TRANSFER)
        )
    )
    return session.exec(statement).all()



@app.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_summary(year: int, month: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    transactions = session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.transaction_date >= start_date,
                                                          Transaction.transaction_date < end_date)).all()
    all_user_categories = session.exec(select(Category).where(Category.user_id == user.id)).all()
    monthly_overrides = session.exec(
        select(MonthlyBudget).where(MonthlyBudget.user_id == user.id, MonthlyBudget.year == year, MonthlyBudget.month == month)).all()

    category_map = {c.id: c for c in all_user_categories}
    monthly_budget_map = {mb.category_id: mb.budgeted_amount for mb in monthly_overrides}

    total_income = 0.0
    total_expenses = 0.0
    actual_spending_by_category = {}
    savings_balances = {}

    for t in transactions:
        category = category_map.get(t.category_id)
        if not category or category.type == CategoryType.TRANSFER:
            continue

        if category.type == CategoryType.INCOME:
            total_income += t.amount
        else:
            total_expenses += t.amount
            if category.type in [CategoryType.CASH, CategoryType.MONTHLY]:
                actual_spending_by_category.setdefault(t.category_id, 0.0)
                actual_spending_by_category[t.category_id] += t.amount
            elif category.type == CategoryType.SAVINGS:
                savings_balances.setdefault(t.category_id, 0.0)
                savings_balances[t.category_id] += t.amount

    expense_breakdown = []
    budgeted_expense_categories = [c for c in all_user_categories if c.type in [CategoryType.MONTHLY, CategoryType.CASH]]

    for category in budgeted_expense_categories:
        budgeted_amount = monthly_budget_map.get(category.id, category.budgeted_amount)
        actual_spent = actual_spending_by_category.get(category.id, 0.0)
        expense_breakdown.append({
            "sub_category": category.name, "budgeted_amount": budgeted_amount,
            "actual_spent": actual_spent, "difference": budgeted_amount - actual_spent
        })

    final_savings_balances = []
    savings_categories = [c for c in all_user_categories if c.type == CategoryType.SAVINGS]
    for category in savings_categories:
        final_savings_balances.append({
            "sub_category": category.name,
            "current_balance": savings_balances.get(category.id, 0.0)
        })

    return {
        "total_income": total_income, "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
        "monthly_expenses": expense_breakdown,
        "savings_balances": final_savings_balances
    }