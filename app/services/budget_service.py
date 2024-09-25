from datetime import date

from sqlmodel import Session

from app.core.db_models.budget_models import ExpBudget
from app.core.db_models.budget_models import IncBudget
from app.services.db_service import add_to_db


def create_expense_budget_entry(*, session: Session, month: date, group_id: int, category_id: int, amount: float) -> ExpBudget:
    db_obj = ExpBudget(month=month, category_id=category_id, category_group_id=group_id, amount=amount)
    return add_to_db(session, db_obj)


def create_income_budget_entry(*, session: Session, month: date, category_id: int, amount: float) -> IncBudget:
    db_obj = IncBudget(month=month, category_id=category_id, amount=amount)
    return add_to_db(session, db_obj)
