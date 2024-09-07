from sqlmodel import Session

from app.core.models import ExpenseCategory
from app.core.models import ExpenseCategoryGroup


def create_category_group(*, session: Session, name: str) -> ExpenseCategoryGroup:
    db_obj = ExpenseCategoryGroup(name=name)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def create_category(*, session: Session, name: str) -> ExpenseCategory:
    db_obj = ExpenseCategory(name=name)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj
