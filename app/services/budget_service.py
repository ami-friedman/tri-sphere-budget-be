from datetime import date

from sqlmodel import Session

from app.core.models import ExpenseBudget
from app.core.models import IncomeBudget
from app.services.db_service import add_to_db


def create_expense_budget_entry(*, session: Session, month: date, group_id: int, category_id: int, amount: float) -> ExpenseBudget:
    db_obj = ExpenseBudget(month=month, category_id=category_id, category_group_id=group_id, amount=amount)
    return add_to_db(session, db_obj)


def create_income_budget_entry(*, session: Session, month: date, category_id: int, amount: float) -> IncomeBudget:
    db_obj = IncomeBudget(month=month, category_id=category_id, amount=amount)
    return add_to_db(session, db_obj)
