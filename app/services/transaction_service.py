from sqlmodel import Session

from app.core.db_models.transaction_models import ExpTransaction
from app.core.db_models.transaction_models import ExpTransactionCreate
from app.core.db_models.transaction_models import IncTransaction
from app.core.db_models.transaction_models import IncTransactionCreate
from app.logger import logger
from app.services.db_service import add_to_db


def create_expense_transaction(*, session: Session, new_expense: ExpTransactionCreate) -> ExpTransaction:
    logger.info(f'Adding new expense transaction: {new_expense=}')
    db_obj = ExpTransaction.model_validate(new_expense)
    return add_to_db(session, db_obj)


def create_income_transaction(*, session: Session, new_income: IncTransactionCreate) -> IncTransaction:
    logger.info(f'Adding new income transaction: {new_income=}')
    db_obj = IncTransaction.model_validate(new_income)
    return add_to_db(session, db_obj)
