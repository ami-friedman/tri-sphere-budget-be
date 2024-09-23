from datetime import datetime
from typing import Generator

import pytest
from sqlmodel import Session

from app.core.db import engine
from app.core.db import init_db
from app.core.models import ExpenseBudget
from app.core.models import ExpenseCategory
from app.core.models import ExpenseCategoryGroup
from app.core.models import IncomeBudget
from app.core.models import IncomeCategory
from app.services import budget_service
from app.services import category_service
from app.tests.utils import faker


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db()
        yield session


@pytest.fixture(scope="session", autouse=True)
def expense_category(db: Session) -> ExpenseCategory:
    return category_service.create_expense_category(session=db, name=faker.random_expense_category())


@pytest.fixture(scope="session", autouse=True)
def expense_category_group(db: Session) -> ExpenseCategoryGroup:
    return category_service.create_expense_category_group(session=db, name=faker.random_expense_category_group())


@pytest.fixture(scope="session", autouse=True)
def expense_budget_item(db: Session, expense_category: ExpenseCategory, expense_category_group: ExpenseCategoryGroup) -> ExpenseBudget:
    return budget_service.create_expense_budget_entry(
        session=db,
        month=datetime.today(),
        category_id=expense_category.id,
        group_id=expense_category_group.id,
        amount=faker.random_expense_amount(),
    )


@pytest.fixture(scope="session", autouse=True)
def income_category(db: Session) -> IncomeCategory:
    return category_service.create_income_category(session=db, name=faker.random_income_category())


@pytest.fixture(scope="session", autouse=True)
def income_budget_item(db: Session, income_category: IncomeCategory) -> IncomeBudget:
    return budget_service.create_income_budget_entry(
        session=db,
        month=datetime.today(),
        category_id=income_category.id,
        amount=faker.random_expense_amount(),
    )
