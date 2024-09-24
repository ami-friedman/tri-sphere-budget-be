from sqlmodel import select
from sqlmodel import Session

from app.core.db_models.category_models import ExpenseCategory
from app.core.db_models.category_models import ExpenseCategoryCreate
from app.core.db_models.category_models import ExpenseCategoryGroup
from app.core.db_models.category_models import ExpenseCategoryGroupCreate
from app.core.db_models.category_models import IncomeCategory
from app.logger import logger
from app.services.db_service import add_to_db


def create_expense_category_group(*, session: Session, new_category: ExpenseCategoryGroupCreate) -> ExpenseCategoryGroup:
    db_category_group = ExpenseCategoryGroup.model_validate(new_category)
    logger.info(f'Creating expense category group {new_category=}')
    return add_to_db(session, db_category_group)


def update_expense_category_group(*, session: Session, group_id: int, update: ExpenseCategoryGroupCreate) -> ExpenseCategoryGroup:
    name = update.get('name')
    logger.info(f'Updating expense category group {group_id=} with {name=}')
    category_group = session.exec(select(ExpenseCategoryGroup).where(ExpenseCategoryGroup.id == group_id)).first()
    category_group.name = name
    return add_to_db(session, category_group)


def create_expense_category(*, session: Session, new_category: ExpenseCategoryCreate) -> ExpenseCategory:
    db_category = ExpenseCategory.model_validate(new_category)
    logger.info(f'Creating expense category {db_category=}')
    return add_to_db(session, db_category)


def update_expense_category(*, session: Session, category_id: int, update: dict) -> ExpenseCategory:
    name = update.get('name')
    logger.info(f'Updating expense category {category_id=} with {name=}')
    category = session.exec(select(ExpenseCategory).where(ExpenseCategory.id == category_id)).first()
    category.name = name
    return add_to_db(session, category)


def create_income_category(*, session: Session, name: str) -> IncomeCategory:
    logger.info(f'Creating income category {name=}')
    db_obj = IncomeCategory(name=name)
    return add_to_db(session, db_obj)


def update_income_category(*, session: Session, category_id: int, update: dict) -> IncomeCategory:
    name = update.get('name')
    logger.info(f'Updating income category {category_id=} with {name=}')
    category = session.exec(select(IncomeCategory).where(IncomeCategory.id == category_id)).first()
    category.name = name
    return add_to_db(session, category)
