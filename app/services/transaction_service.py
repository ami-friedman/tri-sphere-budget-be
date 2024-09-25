from sqlmodel import Session

from app.core.db_models.transaction_models import ExpTransaction
from app.core.db_models.transaction_models import IncTransaction
from app.logger import logger
from app.services.db_service import add_to_db


def create_expense_transaction(*, session: Session, expense_budget_id: int, amount: float) -> ExpTransaction:
    logger.info(f'Adding new expense transaction: {expense_budget_id=} {amount=}')
    db_obj = ExpTransaction(expense_budget_id=expense_budget_id, amount=amount)
    return add_to_db(session, db_obj)


def create_income_transaction(*, session: Session, income_budget_id: int, amount: float) -> IncTransaction:
    logger.info(f'Adding new income transaction: {income_budget_id=} {amount=}')
    db_obj = IncTransaction(income_budget_id=income_budget_id, amount=amount)
    return add_to_db(session, db_obj)
