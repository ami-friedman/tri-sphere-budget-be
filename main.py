import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status
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
    Transaction,
    TransactionCreate,
    TransactionPublic,
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


@app.get("/transactions", response_model=List[TransactionPublic])
def get_transactions(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    transactions = session.exec(select(Transaction).where(Transaction.user_id == user.id)).all()
    return transactions


# Protected API Endpoints
# ... (other endpoints)

@app.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_summary(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    current_month_start = datetime(date.today().year, date.today().month, 1).date()
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)

    # Fetch all transactions and categories for the user
    transactions = session.exec(
        select(Transaction)
        .where(
            Transaction.user_id == user.id,
            Transaction.transaction_date >= current_month_start,
            Transaction.transaction_date < next_month_start
        )
    ).all()
    categories = session.exec(select(Category).where(Category.user_id == user.id)).all()

    category_map = {c.id: c for c in categories}

    total_income = 0.0
    total_expenses = 0.0

    # Calculate actual spending per category
    actual_spending_by_category = {}

    for transaction in transactions:
        category = category_map.get(transaction.category_id)
        if not category or category.type == 'Transfer':
            continue

        if category.type == 'Income':
            total_income += transaction.amount
        else:
            total_expenses += transaction.amount
            actual_spending_by_category.setdefault(category.id, 0.0)
            actual_spending_by_category[category.id] += transaction.amount

    # Build the monthly expenses list (Budget vs Actual)
    monthly_expenses = []
    monthly_categories = [c for c in categories if c.type == 'Monthly']
    for category in monthly_categories:
        actual_spent = actual_spending_by_category.get(category.id, 0.0)
        monthly_expenses.append({
            "sub_category": category.name,
            "budgeted_amount": category.budgeted_amount,
            "actual_spent": actual_spent,
            "difference": category.budgeted_amount - actual_spent
        })

    # Build the savings balances list
    savings_balances = []
    savings_categories = [c for c in categories if c.type == 'Savings']
    for category in savings_categories:
        balance = actual_spending_by_category.get(category.id, 0.0)
        savings_balances.append({
            "sub_category": category.name,
            "current_balance": balance
        })

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
        "monthly_expenses": monthly_expenses,
        "savings_balances": savings_balances
    }