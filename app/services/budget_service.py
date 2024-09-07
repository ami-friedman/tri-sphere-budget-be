from datetime import date

from sqlmodel import Session

from app.core.models import ExpenseBudget


def create_budget_entry(*, session: Session, month: date, group_id: int, category_id: int, amount: float) -> ExpenseBudget:
    db_obj = ExpenseBudget(month=month, category_id=category_id, category_group_id=group_id, amount=amount)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj
