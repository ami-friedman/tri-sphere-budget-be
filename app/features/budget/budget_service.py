from datetime import date

from sqlalchemy import func
from sqlmodel import select
from sqlmodel import Session

from app.core.db_models.budget_models import ExpBudget
from app.core.db_models.budget_models import ExpBudgetPub
from app.core.db_models.budget_models import IncBudget
from app.core.db_models.budget_models import MonthlyBudgetRes
from app.core.db_models.category_models import ExpCat
from app.core.db_models.category_models import ExpCatGroup
from app.database.sql_mgr import SQLManager
from app.services.db_service import add_to_db


class BudgetService:
    def __init__(self, sql_manager: SQLManager):
        self.sql_manager = sql_manager

    async def get_budget_for_month(self, month: date, category_group_id: int) -> MonthlyBudgetRes:
        statement = (
            select(ExpBudget, ExpCat, ExpCatGroup)
            .join(ExpCat)
            .join(ExpCatGroup)
            .where(ExpBudget.month == month, ExpBudget.category_group_id == category_group_id)
        )

        results = await self.sql_manager.exec(statement)
        breakdown: list[ExpBudgetPub] = [
            ExpBudgetPub(
                id=budget.id,
                name=category.name,
                month=budget.month,
                amount=budget.amount,
                category_id=category.id,
                category_group_id=budget.category_group_id,
                category_group=category_group.name,
            )
            for budget, category, category_group in results
        ]
        total = await self.get_total_budget_for_month(month, category_group_id)

        return MonthlyBudgetRes(breakdown=breakdown, total=total, category_group_id=category_group_id)

    async def get_total_budget_for_month(self, month: date, category_group_id: int) -> int:
        statement = (
            select(func.sum(ExpBudget.amount).label('total_amount'))
            .where(ExpBudget.month == month, ExpBudget.category_group_id == category_group_id)
            .group_by(ExpBudget.category_group_id)
        )
        results = await self.sql_manager.exec(statement)

        return results.first() or 0


def create_expense_budget_entry(*, session: Session, month: date, group_id: int, category_id: int, amount: float) -> ExpBudget:
    db_obj = ExpBudget(month=month, category_id=category_id, category_group_id=group_id, amount=amount)
    return add_to_db(session, db_obj)


def create_income_budget_entry(*, session: Session, month: date, category_id: int, amount: float) -> IncBudget:
    db_obj = IncBudget(month=month, category_id=category_id, amount=amount)
    return add_to_db(session, db_obj)
