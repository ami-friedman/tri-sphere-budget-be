from sqlmodel import Session

from app.core.db_models.category_models import ExpenseTransaction
from app.core.db_models.category_models import IncomeTransaction
from app.logger import logger
from app.services.db_service import add_to_db


def create_expense_transaction(*, session: Session, expense_budget_id: int, amount: float) -> ExpenseTransaction:
    logger.info(f'Adding new expense transaction: {expense_budget_id=} {amount=}')
    db_obj = ExpenseTransaction(expense_budget_id=expense_budget_id, amount=amount)
    return add_to_db(session, db_obj)


def create_income_transaction(*, session: Session, income_budget_id: int, amount: float) -> IncomeTransaction:
    logger.info(f'Adding new income transaction: {income_budget_id=} {amount=}')
    db_obj = IncomeTransaction(income_budget_id=income_budget_id, amount=amount)
    return add_to_db(session, db_obj)
