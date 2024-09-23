from sqlmodel import Session

from app.core.models import ExpenseCategory
from app.core.models import ExpenseCategoryGroup
from app.core.models import IncomeCategory
from app.logger import logger
from app.services.db_service import add_to_db


def create_expense_category_group(*, session: Session, name: str) -> ExpenseCategoryGroup:
    logger.info(f'Creating expense category group {name=}')
    db_obj = ExpenseCategoryGroup(name=name)
    return add_to_db(session, db_obj)


def create_expense_category(*, session: Session, name: str) -> ExpenseCategory:
    logger.info(f'Creating expense category {name=}')
    db_obj = ExpenseCategory(name=name)
    return add_to_db(session, db_obj)


def create_income_category(*, session: Session, name: str) -> IncomeCategory:
    logger.info(f'Creating income category {name=}')
    db_obj = IncomeCategory(name=name)
    return add_to_db(session, db_obj)
