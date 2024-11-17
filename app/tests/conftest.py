import random
from datetime import datetime
from typing import Generator

import pytest
from sqlmodel import Session

from app.core.db import engine
from app.core.db import init_db
from app.core.db_models.budget_models import ExpBudget
from app.core.db_models.budget_models import IncBudget
from app.core.db_models.category_models import ExpCat
from app.core.db_models.category_models import ExpCatCreate
from app.core.db_models.category_models import ExpCatGroup
from app.core.db_models.category_models import ExpCatGroupCreate
from app.core.db_models.category_models import IncCat
from app.services import budget_service
from app.services import category_service
from app.tests.utils import faker
from app.tests.utils.faker import expense_categories
from app.tests.utils.faker import expense_category_groups


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db()
        yield session


@pytest.fixture(scope="session", autouse=True)
def expense_category(db: Session) -> ExpCat:
    return category_service.create_expense_category(session=db, new_category=ExpCatCreate(name=faker.random_expense_category()))


@pytest.fixture(scope="session", autouse=True)
def expense_category_group(db: Session) -> ExpCatGroup:
    return category_service.create_expense_category_group(
        session=db, new_category=ExpCatGroupCreate(name=faker.random_expense_category_group())
    )


@pytest.fixture(scope="session", autouse=True)
def expense_budget_item(db: Session, expense_category: ExpCat, expense_category_group: ExpCatGroup) -> ExpBudget:
    return budget_service.create_expense_budget_entry(
        session=db,
        month=datetime.today(),
        category_id=expense_category.id,
        group_id=expense_category_group.id,
        amount=faker.random_expense_amount(),
    )


@pytest.fixture(scope="session", autouse=True)
def monthly_budget(db: Session) -> list[ExpBudget]:
    groups = [
        category_service.create_expense_category_group(session=db, new_category=ExpCatGroupCreate(name=expense_category_groups[0])),
        category_service.create_expense_category_group(session=db, new_category=ExpCatGroupCreate(name=expense_category_groups[1])),
        category_service.create_expense_category_group(session=db, new_category=ExpCatGroupCreate(name=expense_category_groups[2])),
    ]
    monthly_b = []
    for i in range(len(expense_categories)):
        category = category_service.create_expense_category(session=db, new_category=ExpCatCreate(name=expense_categories[i]))
        current_group = random.choice(groups)
        monthly_b.append(
            budget_service.create_expense_budget_entry(
                session=db, month=datetime.today(), category_id=category.id, group_id=current_group.id, amount=faker.random_expense_amount()
            )
        )
    return monthly_b


@pytest.fixture(scope="session", autouse=True)
def income_category(db: Session) -> IncCat:
    return category_service.create_income_category(session=db, name=faker.random_income_category())


@pytest.fixture(scope="session", autouse=True)
def income_budget_item(db: Session, income_category: IncCat) -> IncBudget:
    return budget_service.create_income_budget_entry(
        session=db,
        month=datetime.today(),
        category_id=income_category.id,
        amount=faker.random_expense_amount(),
    )
