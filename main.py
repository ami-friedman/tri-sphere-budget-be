import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone, date
from jose import JWTError, jwt
from dotenv import load_dotenv
from uuid import UUID

from models import (
    User,
    UserCreate,
    UserPublic,
    Token,
    Account,
    Category,
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
    Transaction,
    TransactionCreate,
    TransactionPublic,
    TransactionUpdate,
    TransferCreate,
    TransferPublic,
    CategoryType
)

# Load environment variables
load_dotenv()

# We define the URL string here. The engine will be created dynamically.
# Note: The '@' in 'P@ssw0rd' is URL-encoded as '%40'
DATABASE_URL_STR = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:P%40ssw0rd@localhost/trisphere_budget")


def create_database(url_str: str):
    """
    Creates the database if it doesn't exist by connecting to a default
    database first.
    """
    db_url = make_url(url_str)
    db_name = db_url.database

    # Create a temporary URL with a known database to connect to the server
    temp_url = db_url.set(database='information_schema')
    temp_engine = create_engine(temp_url, echo=False)

    with temp_engine.connect() as connection:
        # Check if the database exists
        result = connection.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'"))
        if not result.scalar():
            print(f"Database '{db_name}' not found. Creating it now...")
            connection.execute(text(f"CREATE DATABASE {db_name}"))
            connection.commit()
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")


def create_db_and_tables(engine):
    """Creates all tables in the database using a provided engine."""
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Dynamic database and engine creation
    create_database(DATABASE_URL_STR)
    engine = create_engine(DATABASE_URL_STR, echo=True)
    create_db_and_tables(engine)

    # We attach the engine to the app state so it can be used by dependencies
    app.state.engine = engine
    yield


app = FastAPI(lifespan=lifespan)

# CORS Middleware
origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT & Password Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-please-change")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Set a long expiration time for convenience during development
        expire = datetime.now(timezone.utc) + timedelta(days=365)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Dependency to get database session
def get_session():
    # Use the engine from the app state
    engine = app.state.engine
    with Session(engine) as session:
        yield session


# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        # Convert string to UUID object
        user_id = UUID(user_id_str)
    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# API Endpoints
@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user_create.username)).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    db_user = session.exec(select(User).where(User.email == user_create.email)).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(days=365)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    refresh_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(days=365))

    return Token(access_token=access_token, expires_in=int(access_token_expires.total_seconds()), refresh_token=refresh_token)


# Protected API Endpoints
@app.post("/categories", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(category_create: CategoryCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Check for an existing category with the same name and type for this user
    existing_category = session.exec(
        select(Category).where(
            Category.user_id == user.id,
            Category.name == category_create.name,
            Category.type == category_create.type
        )
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category named '{category_create.name}' with type '{category_create.type}' already exists."
        )

    db_category = Category(
        user_id=user.id,
        name=category_create.name,
        type=category_create.type,
        budgeted_amount=category_create.budgeted_amount
    )
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@app.put("/categories/{category_id}", response_model=CategoryPublic)
def update_category(category_id: UUID, category_update: CategoryUpdate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    db_category = session.exec(select(Category).where(Category.id == category_id, Category.user_id == user.id)).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or does not belong to the user."
        )

    # Apply updates
    for key, value in category_update.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)

    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@app.get("/categories", response_model=List[CategoryPublic])
def get_categories(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    categories = session.exec(select(Category).where(Category.user_id == user.id)).all()
    return categories


@app.post("/transactions", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction_create: TransactionCreate, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    # Validate category exists and belongs to the user
    try:
        category_id = UUID(str(transaction_create.category_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID format"
        )

    category = session.exec(select(Category).where(Category.id == category_id, Category.user_id == user.id)).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or does not belong to the user"
        )

    db_transaction = Transaction(
        user_id=user.id,
        category_id=category_id,
        amount=transaction_create.amount,
        description=transaction_create.description,
        transaction_date=transaction_create.transaction_date,
    )
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


@app.put("/transactions/{transaction_id}", response_model=TransactionPublic)
def update_transaction(transaction_id: UUID, transaction_update: TransactionUpdate, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id)).first()
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or does not belong to the user."
        )

    # Validate category exists and belongs to the user if provided
    if transaction_update.category_id:
        category = session.exec(select(Category).where(Category.id == transaction_update.category_id, Category.user_id == user.id)).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or does not belong to the user"
            )

    # Apply updates
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or does not belong to the user."
        )

    session.delete(db_transaction)
    session.commit()
    return


@app.get("/transactions", response_model=List[TransactionPublic])
def get_transactions(
        user: User = Depends(get_current_user),
        session: Session = Depends(get_session),
        year: Optional[int] = None,
        month: Optional[int] = None
):
    current_year = year if year else date.today().year
    current_month = month if month else date.today().month

    start_date = date(current_year, current_month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    transactions = session.exec(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        )
    ).all()
    return transactions


@app.post("/transfers", response_model=TransferPublic, status_code=status.HTTP_201_CREATED)
def create_transfer(transfer_create: TransferCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Validate the transfer category is of type 'Savings' and belongs to the user
    try:
        category_id = UUID(str(transfer_create.category_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID format"
        )

    category = session.exec(select(Category).where(Category.id == category_id, Category.user_id == user.id)).first()
    if not category or category.type != 'Savings':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category: transfers must be to a 'Savings' category."
        )

    db_transaction = Transaction(
        user_id=user.id,
        category_id=category_id,
        amount=-transfer_create.amount,  # Transfers out of main account are negative
        description=transfer_create.description,
        transaction_date=transfer_create.transaction_date,
    )
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


@app.get("/transfers", response_model=List[TransferPublic])
def get_transfers(
        user: User = Depends(get_current_user),
        session: Session = Depends(get_session),
        year: Optional[int] = None,
        month: Optional[int] = None
):
    current_year = year if year else date.today().year
    current_month = month if month else date.today().month

    start_date = date(current_year, current_month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    transfer_category_type = 'Savings'

    transactions = session.exec(
        select(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user.id,
            Category.type == transfer_category_type,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        )
    ).all()
    return transactions


@app.put("/transfers/{transfer_id}", response_model=TransferPublic)
def update_transfer(transfer_id: UUID, transfer_update: TransactionUpdate, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transfer_id, Transaction.user_id == user.id)).first()
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or does not belong to the user."
        )

    # Validate the transfer category is of type 'Savings' and belongs to the user
    if transfer_update.category_id:
        category = session.exec(select(Category).where(Category.id == transfer_update.category_id, Category.user_id == user.id)).first()
        if not category or category.type != 'Savings':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category: transfers must be to a 'Savings' category."
            )

    # Apply updates
    for key, value in transfer_update.model_dump(exclude_unset=True).items():
        setattr(db_transaction, key, value)

    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


@app.delete("/transfers/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer(transfer_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transfer_id, Transaction.user_id == user.id)).first()
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or does not belong to the user."
        )

    session.delete(db_transaction)
    session.commit()
    return


@app.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_summary(
        user: User = Depends(get_current_user),
        session: Session = Depends(get_session),
        year: Optional[int] = None,
        month: Optional[int] = None
):
    current_year = year if year else date.today().year
    current_month = month if month else date.today().month

    start_date = date(current_year, current_month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    # Fetch all transactions and categories for the user
    transactions = session.exec(
        select(Transaction)
        .where(
            Transaction.user_id == user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        )
    ).all()
    all_user_categories = session.exec(select(Category).where(Category.user_id == user.id)).all()

    category_map = {c.id: c for c in all_user_categories}

    total_income = 0.0
    total_expenses = 0.0
    actual_spending_by_category = {}
    savings_movements = {}

    for transaction in transactions:
        category = category_map.get(transaction.category_id)
        if not category or category.type == CategoryType.TRANSFER:
            continue

        if category.type == CategoryType.INCOME:
            total_income += transaction.amount
        else:
            # This correctly includes Cash, Monthly, and Savings in total expenses
            total_expenses += transaction.amount

            # Populate actual spending for expense categories
            if category.type in [CategoryType.CASH, CategoryType.MONTHLY]:
                actual_spending_by_category.setdefault(category.id, 0.0)
                actual_spending_by_category[category.id] += transaction.amount

            # Track savings movements separately for savings balance calculation
            if category.type == CategoryType.SAVINGS:
                savings_movements.setdefault(category.id, 0.0)
                savings_movements[category.id] += transaction.amount

    # Build the expense breakdown table (Budget vs Actual)
    expense_breakdown = []
    # **THIS IS THE FIX**: Include both 'Monthly' and 'Cash' types in the table.
    budgeted_expense_categories = [
        c for c in all_user_categories if c.type in [CategoryType.MONTHLY, CategoryType.CASH]
    ]

    for category in budgeted_expense_categories:
        actual_spent = actual_spending_by_category.get(category.id, 0.0)
        expense_breakdown.append({
            "sub_category": category.name,
            "budgeted_amount": category.budgeted_amount,
            "actual_spent": actual_spent,
            "difference": category.budgeted_amount - actual_spent
        })

    # Build the savings balances list
    savings_balances = []
    savings_categories = [c for c in all_user_categories if c.type == CategoryType.SAVINGS]
    for category in savings_categories:
        # NOTE: Savings balance is just the sum of transactions to that category.
        balance = savings_movements.get(category.id, 0.0)
        savings_balances.append({
            "sub_category": category.name,
            "current_balance": balance
        })

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
        "monthly_expenses": expense_breakdown,  # Renamed for clarity, but key is the same for FE
        "savings_balances": savings_balances
    }


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # First, find the category to ensure it exists and belongs to the user
    db_category = session.exec(select(Category).where(Category.id == category_id, Category.user_id == user.id)).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    # Business Logic: Check if any transactions are using this category
    transaction_check = session.exec(select(Transaction).where(Transaction.category_id == category_id)).first()
    if transaction_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category. It is currently in use by one or more transactions."
        )

    # If no transactions are using it, proceed with deletion
    session.delete(db_category)
    session.commit()
    return
