from sqlmodel import select
from sqlmodel import Session

from app.core.db_models.category_models import ExpCat
from app.core.db_models.category_models import ExpCatCreate
from app.core.db_models.category_models import ExpCatGroup
from app.core.db_models.category_models import ExpCatGroupCreate
from app.core.db_models.category_models import ExpCatGroupPub
from app.core.db_models.category_models import ExpCatPub
from app.core.db_models.category_models import IncCat
from app.core.db_models.category_models import IncCatPub
from app.logger import logger
from app.services.db_service import add_to_db


def create_expense_category_group(*, session: Session, new_category: ExpCatGroupCreate) -> ExpCatGroupPub:
    db_category_group = ExpCatGroup.model_validate(new_category)
    logger.info(f'Creating expense category group {new_category=}')
    return add_to_db(session, db_category_group)


def update_expense_category_group(*, session: Session, update: ExpCatGroupPub) -> ExpCatGroupPub:
    logger.info(f'Updating expense category group: to {update=}')
    category_group = session.exec(select(ExpCatGroup).where(ExpCatGroup.id == update.id)).first()
    category_group.name = update.name
    return add_to_db(session, category_group)


def create_expense_category(*, session: Session, new_category: ExpCatCreate) -> ExpCatPub:
    db_category = ExpCat.model_validate(new_category)
    logger.info(f'Creating expense category {db_category=}')
    return add_to_db(session, db_category)


def update_expense_category(*, session: Session, update: ExpCatPub) -> ExpCatPub:
    logger.info(f'Updating expense category to {update=}')
    category = session.exec(select(ExpCat).where(ExpCat.id == update.id)).first()
    category.name = update.name
    return add_to_db(session, category)


def create_income_category(*, session: Session, name: str) -> IncCat:
    logger.info(f'Creating income category {name=}')
    db_obj = IncCat(name=name)
    return add_to_db(session, db_obj)


def update_income_category(*, session: Session, update: IncCatPub) -> IncCat:
    logger.info(f'Updating income category to {update=}')
    category = session.exec(select(IncCat).where(IncCat.id == update.id)).first()
    category.name = update.name
    return add_to_db(session, category)
