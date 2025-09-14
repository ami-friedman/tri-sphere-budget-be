import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone, date
from pydantic import BaseModel

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, SQLModel, create_engine, select
import csv
import io
from fastapi import UploadFile, File
from pydantic import BaseModel
from models import PendingTransaction, PendingTransactionPublic, FinalizeTransaction


from models import (
    User, UserCreate, UserPublic, Token, Account, Category, CategoryCreate,
    CategoryPublic, CategoryUpdate, Transaction, TransactionCreate,
    TransactionPublic, TransactionUpdate, CategoryType, MonthlyBudget, AccountType
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_database(DATABASE_URL_STR)
    engine = create_engine(DATABASE_URL_STR, echo=True)
    SQLModel.metadata.create_all(engine)
    app.state.engine = engine
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "https://fluffy-froyo-8db2d2.netlify.app"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-please-change")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)


def get_password_hash(password): return pwd_context.hash(password)


def create_access_token(data, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=365))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_session():
    with Session(app.state.engine) as session: yield session


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = UUID(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = session.get(User, user_id)
    if not user: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.username == user_create.username)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    db_user = User(username=user_create.username, email=user_create.email, hashed_password=get_password_hash(user_create.password))
    session.add(db_user)
    # Create default accounts for the new user
    checking = Account(user_id=db_user.id, name="Checking", type=AccountType.CHECKING)
    savings = Account(user_id=db_user.id, name="Savings", type=AccountType.SAVINGS)
    session.add_all([checking, savings])
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    expires = timedelta(days=365)
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=expires)
    return Token(access_token=token, refresh_token=token, expires_in=int(expires.total_seconds()))


@app.get("/accounts", response_model=List[Account])
def get_accounts(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(Account).where(Account.user_id == user.id)).all()


@app.post("/categories", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(cat: CategoryCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_cat = Category.model_validate(cat, update={"user_id": user.id})
    session.add(db_cat)
    session.commit()
    session.refresh(db_cat)
    return db_cat


@app.put("/categories/{cat_id}", response_model=CategoryPublic)
def update_category(cat_id: UUID, cat_up: CategoryUpdate, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_cat = session.get(Category, cat_id)
    if not db_cat or db_cat.user_id != user.id: raise HTTPException(404, "Category not found")
    for k, v in cat_up.model_dump(exclude_unset=True).items(): setattr(db_cat, k, v)
    session.add(db_cat)
    session.commit()
    session.refresh(db_cat)
    return db_cat


@app.delete("/categories/{cat_id}", status_code=204)
def delete_category(cat_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_cat = session.get(Category, cat_id)
    if not db_cat or db_cat.user_id != user.id: raise HTTPException(404, "Category not found")
    if session.exec(select(Transaction).where(Transaction.category_id == cat_id)).first():
        raise HTTPException(409, "Category is in use by transactions.")
    session.delete(db_cat)
    session.commit()


@app.get("/categories", response_model=List[CategoryPublic])
def get_categories(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(Category).where(Category.user_id == user.id)).all()


@app.post("/transactions", response_model=TransactionPublic, status_code=201)
def create_transaction(tx_create: TransactionCreate, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    acc = session.get(Account, tx_create.account_id)
    cat = session.get(Category, tx_create.category_id)
    if not acc or acc.user_id != user.id: raise HTTPException(400, "Account not found")
    if not cat or cat.user_id != user.id: raise HTTPException(400, "Category not found")

    amount = abs(tx_create.amount)

    # Handle the special case for funding savings from a checking account
    if cat.type == CategoryType.SAVINGS and acc.type == AccountType.CHECKING:
        savings_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.SAVINGS)).first()
        if not savings_acc: raise HTTPException(500, "User has no savings account configured")

        # Create a negative transaction for checking (outflow)
        checking_tx = Transaction.model_validate(tx_create, update={"user_id": user.id, "amount": -amount})
        # Create a positive transaction for savings (inflow)
        savings_tx = Transaction(user_id=user.id, account_id=savings_acc.id, category_id=cat.id, amount=amount, transaction_date=tx_create.transaction_date, description=f"Fund from {acc.name}")
        session.add_all([checking_tx, savings_tx])
        session.commit()
        session.refresh(checking_tx)
        return checking_tx
    else:
        # For all other normal transactions, ensure expenses are negative and income is positive
        final_amount = amount if cat.type == CategoryType.INCOME else -amount
        db_tx = Transaction.model_validate(tx_create, update={"user_id": user.id, "amount": final_amount})
        session.add(db_tx)
        session.commit()
        session.refresh(db_tx)
        return db_tx

@app.put("/transactions/{tx_id}", response_model=TransactionPublic)
def update_transaction(tx_id: UUID, tx_up: TransactionUpdate, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    db_tx = session.get(Transaction, tx_id)
    if not db_tx or db_tx.user_id != user.id: raise HTTPException(404, "Transaction not found")
    for k, v in tx_up.model_dump(exclude_unset=True).items(): setattr(db_tx, k, v)
    session.add(db_tx)
    session.commit()
    session.refresh(db_tx)
    return db_tx


@app.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(tx_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_tx = session.get(Transaction, tx_id)
    if not db_tx or db_tx.user_id != user.id: raise HTTPException(404, "Transaction not found")
    session.delete(db_tx)
    session.commit()


@app.get("/transactions", response_model=List[TransactionPublic])
def get_transactions(
        year: int,
        month: int,
        account_id: UUID,
        user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    """
    Fetches transactions for a SPECIFIC account for a given month and year.
    """
    # 1. Validate that the requested account belongs to the user
    account = session.get(Account, account_id)
    if not account or account.user_id != user.id:
        raise HTTPException(status_code=404, detail="Account not found.")

    # 2. Fetch transactions for that specific account for the given period
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    return session.exec(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.account_id == account_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        )
    ).all()


@app.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_summary(year: int, month: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    start, end = date(year, month, 1), (date(year, month, 1) + timedelta(days=32)).replace(day=1)

    checking_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.CHECKING)).first()
    if not checking_acc: return {"total_income": 0, "total_expenses": 0, "net_balance": 0, "monthly_expenses": [], "savings_balances": []}

    txs = session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.account_id == checking_acc.id,
                                                 Transaction.transaction_date >= start, Transaction.transaction_date < end)).all()
    cats = session.exec(select(Category).where(Category.user_id == user.id)).all()
    overrides = session.exec(
        select(MonthlyBudget).where(MonthlyBudget.user_id == user.id, MonthlyBudget.year == year, MonthlyBudget.month == month)).all()

    cat_map = {c.id: c for c in cats}
    budget_map = {mb.category_id: mb.budgeted_amount for mb in overrides}

    income, expenses, spending = 0.0, 0.0, {}
    for tx in txs:
        cat = cat_map.get(tx.category_id)
        if not cat or cat.type == CategoryType.TRANSFER: continue
        if cat.type == CategoryType.INCOME:
            income += tx.amount
        else:
            expenses += abs(tx.amount)
            spending.setdefault(tx.category_id, 0.0)
            spending[tx.category_id] += abs(tx.amount)

    breakdown = []
    for cat in [c for c in cats if c.type in [CategoryType.MONTHLY, CategoryType.CASH, CategoryType.SAVINGS]]:
        budget = budget_map.get(cat.id, cat.budgeted_amount)
        actual = spending.get(cat.id, 0.0)
        breakdown.append({"sub_category": cat.name, "budgeted_amount": budget, "actual_spent": actual, "difference": budget - actual})

    return {"total_income": income, "total_expenses": expenses, "net_balance": income - expenses, "monthly_expenses": breakdown}


@app.get("/savings-ledger", response_model=Dict[str, Any])
def get_savings_ledger(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    savings_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.SAVINGS)).first()
    if not savings_acc: return {"total_balance": 0, "fund_balances": [], "recent_activity": []}

    all_txs = session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.account_id == savings_acc.id)).all()
    savings_cats = session.exec(select(Category).where(Category.user_id == user.id, Category.type == CategoryType.SAVINGS)).all()

    total_balance = sum(tx.amount for tx in all_txs)

    fund_balances = []
    for cat in savings_cats:
        balance = sum(tx.amount for tx in all_txs if tx.category_id == cat.id)
        fund_balances.append({"fund_name": cat.name, "current_balance": balance})

    recent_activity = sorted(all_txs, key=lambda tx: tx.transaction_date, reverse=True)[:20]

    return {"total_balance": total_balance, "fund_balances": fund_balances, "recent_activity": recent_activity}


@app.get("/budget-summary", response_model=Dict[str, float])
def get_budget_summary(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Calculates the total budgeted amounts for each category type.
    This is used for the summary panel on the Budget page.
    """
    all_categories = session.exec(select(Category).where(Category.user_id == user.id)).all()

    summary = {
        "income": 0.0,
        "monthly": 0.0,
        "cash": 0.0,
        "savings": 0.0,
    }

    for cat in all_categories:
        if cat.type == CategoryType.INCOME:
            summary["income"] += cat.budgeted_amount
        elif cat.type == CategoryType.MONTHLY:
            summary["monthly"] += cat.budgeted_amount
        elif cat.type == CategoryType.CASH:
            summary["cash"] += cat.budgeted_amount
        elif cat.type == CategoryType.SAVINGS:
            summary["savings"] += cat.budgeted_amount

    return summary


class BudgetActual(BaseModel):
    budgeted: float = 0.0
    actual: float = 0.0


class DashboardSummaryResponse(BaseModel):
    income: BudgetActual
    monthly: BudgetActual
    cash: BudgetActual
    savings: BudgetActual
    total_expenses: BudgetActual
    net_cash_flow: BudgetActual


@app.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary_v2(year: int, month: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # 1. Get user's primary checking account
    checking_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.CHECKING)).first()
    if not checking_acc:
        raise HTTPException(status_code=404, detail="Checking account not found for user.")

    # 2. Fetch all necessary data for the given month
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    all_categories = session.exec(select(Category).where(Category.user_id == user.id)).all()
    monthly_overrides = session.exec(
        select(MonthlyBudget).where(MonthlyBudget.user_id == user.id, MonthlyBudget.year == year, MonthlyBudget.month == month)).all()
    transactions = session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.account_id == checking_acc.id,
                                                          Transaction.transaction_date >= start_date,
                                                          Transaction.transaction_date < end_date)).all()

    # 3. Process data into useful lookups
    budget_map = {mb.category_id: mb.budgeted_amount for mb in monthly_overrides}
    category_map = {c.id: c for c in all_categories}

    # 4. Calculate Budgeted and Actual totals for each category type
    summary = DashboardSummaryResponse(
        income=BudgetActual(),
        monthly=BudgetActual(),
        cash=BudgetActual(),
        savings=BudgetActual(),
        total_expenses=BudgetActual(),
        net_cash_flow=BudgetActual()
    )

    # Calculate budgeted amounts
    for cat in all_categories:
        budgeted_amount = budget_map.get(cat.id, cat.budgeted_amount)
        if cat.type == CategoryType.INCOME:
            summary.income.budgeted += budgeted_amount
        elif cat.type == CategoryType.MONTHLY:
            summary.monthly.budgeted += budgeted_amount
        elif cat.type == CategoryType.CASH:
            summary.cash.budgeted += budgeted_amount
        elif cat.type == CategoryType.SAVINGS:
            summary.savings.budgeted += budgeted_amount

    # Calculate actual amounts from transactions
    for tx in transactions:
        cat = category_map.get(tx.category_id)
        if not cat or cat.type == CategoryType.TRANSFER:
            continue

        amount = abs(tx.amount)
        if cat.type == CategoryType.INCOME:
            summary.income.actual += amount
        elif cat.type == CategoryType.MONTHLY:
            summary.monthly.actual += amount
        elif cat.type == CategoryType.CASH:
            summary.cash.actual += amount
        elif cat.type == CategoryType.SAVINGS:
            summary.savings.actual += amount

    # 5. Calculate final totals
    summary.total_expenses.budgeted = summary.monthly.budgeted + summary.cash.budgeted + summary.savings.budgeted
    summary.total_expenses.actual = summary.monthly.actual + summary.cash.actual + summary.savings.actual

    summary.net_cash_flow.budgeted = summary.income.budgeted - summary.total_expenses.budgeted
    summary.net_cash_flow.actual = summary.income.actual - summary.total_expenses.actual

    return summary


class FundSavingsRequest(BaseModel):
    year: int
    month: int


@app.post("/transactions/fund-savings", status_code=201)
def fund_savings_from_budget(req: FundSavingsRequest, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Creates funding transactions for all savings categories that have a budget
    but have not yet been funded for the given month.
    """
    year, month = req.year, req.month
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    # 1. Get user's accounts
    checking_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.CHECKING)).first()
    savings_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.SAVINGS)).first()
    if not checking_acc or not savings_acc:
        raise HTTPException(status_code=404, detail="User accounts not configured correctly.")

    # 2. Find all savings categories with a budget > 0
    savings_categories = session.exec(
        select(Category).where(
            Category.user_id == user.id,
            Category.type == CategoryType.SAVINGS,
            Category.budgeted_amount > 0
        )
    ).all()
    if not savings_categories:
        return {"message": "No savings categories with a budget to fund."}

    # 3. Check for existing funding transactions this month to avoid duplicates
    existing_funding_txs = session.exec(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.account_id == checking_acc.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date,
            Transaction.category_id.in_([c.id for c in savings_categories])
        )
    ).all()
    funded_category_ids = {tx.category_id for tx in existing_funding_txs}

    # 4. Create transactions for unfunded categories
    new_transactions_created = 0
    for cat in savings_categories:
        if cat.id not in funded_category_ids:
            amount = cat.budgeted_amount

            checking_tx = Transaction(user_id=user.id, account_id=checking_acc.id, category_id=cat.id, amount=-amount,
                                      transaction_date=start_date, description="Budgeted Savings Funding")
            savings_tx = Transaction(user_id=user.id, account_id=savings_acc.id, category_id=cat.id, amount=amount,
                                     transaction_date=start_date, description=f"Funding from {checking_acc.name}")
            session.add_all([checking_tx, savings_tx])
            new_transactions_created += 1

    if new_transactions_created == 0:
        return {"message": "All savings categories have already been funded for this month."}

    session.commit()
    return {"message": f"Successfully created {new_transactions_created} funding transaction(s)."}


class FundBalance(BaseModel):
    fund_name: str
    current_balance: float


class SavingsSummary(BaseModel):
    total_balance: float
    fund_balances: List[FundBalance]


class V2DashboardResponse(BaseModel):
    checking_summary: Dict[str, BudgetActual]
    savings_summary: SavingsSummary


# ** NEW ENDPOINT **
@app.get("/dashboard/v2", response_model=V2DashboardResponse)
def get_full_dashboard(year: int, month: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # --- Part 1: Checking Account Summary (similar to old summary endpoint) ---
    checking_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.CHECKING)).first()
    if not checking_acc:
        raise HTTPException(status_code=404, detail="Checking account not found.")

    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)

    all_categories = session.exec(select(Category).where(Category.user_id == user.id)).all()
    monthly_overrides = session.exec(
        select(MonthlyBudget).where(MonthlyBudget.user_id == user.id, MonthlyBudget.year == year, MonthlyBudget.month == month)).all()
    transactions = session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.account_id == checking_acc.id,
                                                          Transaction.transaction_date >= start_date,
                                                          Transaction.transaction_date < end_date)).all()

    budget_map = {mb.category_id: mb.budgeted_amount for mb in monthly_overrides}
    category_map = {c.id: c for c in all_categories}

    summary = {"income": BudgetActual(), "monthly": BudgetActual(), "cash": BudgetActual(), "savings": BudgetActual()}
    for cat in all_categories:
        budgeted_amount = budget_map.get(cat.id, cat.budgeted_amount)
        if cat.type == CategoryType.INCOME:
            summary["income"].budgeted += budgeted_amount
        elif cat.type == CategoryType.MONTHLY:
            summary["monthly"].budgeted += budgeted_amount
        elif cat.type == CategoryType.CASH:
            summary["cash"].budgeted += budgeted_amount
        elif cat.type == CategoryType.SAVINGS:
            summary["savings"].budgeted += budgeted_amount

    for tx in transactions:
        cat = category_map.get(tx.category_id)
        if not cat or cat.type == CategoryType.TRANSFER: continue
        amount = abs(tx.amount)
        if cat.type == CategoryType.INCOME:
            summary["income"].actual += amount
        elif cat.type == CategoryType.MONTHLY:
            summary["monthly"].actual += amount
        elif cat.type == CategoryType.CASH:
            summary["cash"].actual += amount
        elif cat.type == CategoryType.SAVINGS:
            summary["savings"].actual += amount

    total_exp_b = summary["monthly"].budgeted + summary["cash"].budgeted + summary["savings"].budgeted
    total_exp_a = summary["monthly"].actual + summary["cash"].actual + summary["savings"].actual

    checking_summary = {
        "income": summary["income"], "monthly": summary["monthly"], "cash": summary["cash"], "savings": summary["savings"],
        "total_expenses": BudgetActual(budgeted=total_exp_b, actual=total_exp_a),
        "net_cash_flow": BudgetActual(budgeted=summary["income"].budgeted - total_exp_b, actual=summary["income"].actual - total_exp_a)
    }

    # --- Part 2: Savings Account Summary (from savings ledger endpoint) ---
    savings_acc = session.exec(select(Account).where(Account.user_id == user.id, Account.type == AccountType.SAVINGS)).first()
    if not savings_acc:
        savings_summary = SavingsSummary(total_balance=0, fund_balances=[])
    else:
        all_savings_txs = session.exec(
            select(Transaction).where(Transaction.user_id == user.id, Transaction.account_id == savings_acc.id)).all()
        savings_cats = [c for c in all_categories if c.type == CategoryType.SAVINGS]

        total_balance = sum(tx.amount for tx in all_savings_txs)

        fund_balances = []
        for cat in savings_cats:
            balance = sum(tx.amount for tx in all_savings_txs if tx.category_id == cat.id)
            fund_balances.append(FundBalance(fund_name=cat.name, current_balance=balance))

        savings_summary = SavingsSummary(total_balance=total_balance, fund_balances=fund_balances)

    return V2DashboardResponse(checking_summary=checking_summary, savings_summary=savings_summary)


@app.post("/transactions/upload", status_code=201)
def upload_transactions(account_type: AccountType, file: UploadFile = File(...), user: User = Depends(get_current_user),
                        session: Session = Depends(get_session)):
    try:
        contents = file.file.read().decode("utf-8")
        csv_reader = csv.reader(io.StringIO(contents))
        header = next(csv_reader)

        if "Description" not in header or "Date" not in header or "Amount" not in header:
            raise HTTPException(status_code=400, detail="CSV must contain 'Description', 'Date', and 'Amount' columns.")

        pending_txs = []
        for row in csv_reader:
            row_dict = dict(zip(header, row))
            description = row_dict["Description"].lower()
            amount = abs(float(row_dict["Amount"]))

            # Intelligent amount handling: default to expense (negative), but flip to income (positive) for refunds/payments.
            if "payment" in description or "refund" in description:
                final_amount = amount
            else:
                final_amount = -amount

            pending_txs.append(
                PendingTransaction(
                    user_id=user.id,
                    statement_description=row_dict["Description"],
                    transaction_date=datetime.strptime(row_dict["Date"], "%Y-%m-%d").date(),
                    amount=final_amount,
                    target_account_type=account_type
                )
            )
        session.add_all(pending_txs)
        session.commit()
        return {"message": f"Successfully imported {len(pending_txs)} transactions for review."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


# ** UPDATED ENDPOINT 2: GET PENDING **
@app.get("/transactions/pending", response_model=List[PendingTransactionPublic])
def get_pending_transactions(
        account_type: AccountType,  # Now requires an account type to filter by
        user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    # This now only returns transactions for the specified account type
    return session.exec(
        select(PendingTransaction).where(
            PendingTransaction.user_id == user.id,
            PendingTransaction.target_account_type == account_type
        )
    ).all()


# ** NEW ENDPOINT 3: IGNORE **
@app.post("/transactions/pending/ignore", status_code=200)
def ignore_pending_transactions(pending_ids: List[UUID], user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    txs_to_delete = session.exec(
        select(PendingTransaction).where(PendingTransaction.user_id == user.id, PendingTransaction.id.in_(pending_ids))).all()
    if not txs_to_delete:
        raise HTTPException(status_code=404, detail="No matching transactions found to ignore.")
    for tx in txs_to_delete:
        session.delete(tx)
    session.commit()
    return {"message": "Selected transactions have been ignored."}


# ** NEW ENDPOINT 4: FINALIZE **
@app.post("/transactions/finalize", status_code=201)
def finalize_transactions(finalized_txs: List[FinalizeTransaction], user: User = Depends(get_current_user),
                          session: Session = Depends(get_session)):
    newly_created_count = 0
    for f_tx in finalized_txs:
        pending_tx = session.get(PendingTransaction, f_tx.pending_transaction_id)
        if pending_tx and pending_tx.user_id == user.id:
            # Create the final transaction record
            final_tx = Transaction(
                user_id=user.id,
                account_id=f_tx.account_id,
                category_id=f_tx.category_id,
                amount=pending_tx.amount,
                description=pending_tx.statement_description,
                transaction_date=pending_tx.transaction_date
            )
            session.add(final_tx)
            # Remove the pending transaction
            session.delete(pending_tx)
            newly_created_count += 1
    session.commit()
    return {"message": f"Successfully finalized {newly_created_count} transactions."}
