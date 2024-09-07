from datetime import datetime

from sqlmodel import Session

from app.services import budget_service
from app.services import category_service


class TestBudget:
    def test_add_budget_item(self, db: Session):
        category_group_name: str = 'cash'
        category_name: str = 'cleaner'
        budget_amount: int = 1000
        category_group = category_service.create_category_group(session=db, name=category_group_name)
        category = category_service.create_category(session=db, name=category_name)
        new_budget_entry = budget_service.create_budget_entry(
            session=db, month=datetime.today(), group_id=category_group.id, category_id=category.id, amount=budget_amount
        )
        assert new_budget_entry.category_group_id == category_group.id
        assert new_budget_entry.category_id == category.id
        assert new_budget_entry.amount == budget_amount
