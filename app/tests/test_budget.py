from datetime import datetime

from sqlmodel import Session

from app.core.db_models.budget_models import ExpBudget
from app.core.db_models.budget_models import MonthlyBudgetRes
from app.core.db_models.category_models import ExpCatCreate
from app.core.db_models.category_models import ExpCatGroupCreate
from app.services import budget_service
from app.services import category_service


class TestBudget:
    def test_add_expense_budget_item(self, db: Session):
        category_group_name: str = 'cash'
        category_name: str = 'cleaner'
        budget_amount: int = 1000
        category_group = category_service.create_expense_category_group(
            session=db, new_category=ExpCatGroupCreate(name=category_group_name)
        )
        category = category_service.create_expense_category(session=db, new_category=ExpCatCreate(name=category_name))
        new_budget_entry = budget_service.create_expense_budget_entry(
            session=db, month=datetime.today(), group_id=category_group.id, category_id=category.id, amount=budget_amount
        )
        assert new_budget_entry.category_group_id == category_group.id
        assert new_budget_entry.category_id == category.id
        assert new_budget_entry.amount == budget_amount

    def test_add_income_budget_item(self, db: Session):
        category_name: str = 'Amichai Salary'
        budget_amount: int = 10_000
        category = category_service.create_income_category(session=db, name=category_name)
        new_budget_entry = budget_service.create_income_budget_entry(
            session=db, month=datetime.today(), category_id=category.id, amount=budget_amount
        )
        assert new_budget_entry.category_id == category.id
        assert new_budget_entry.amount == budget_amount

    def test_get_budget_for_month(self, db: Session, monthly_budget: list[ExpBudget]):
        group_id_to_get = monthly_budget[0].category_group_id
        expected_total_for_month = sum((m.amount for m in monthly_budget if m.category_group_id == group_id_to_get))
        budget_for_month: MonthlyBudgetRes = budget_service.get_budget_for_month(db, monthly_budget[0].month, group_id_to_get)
        assert budget_for_month.total == expected_total_for_month
