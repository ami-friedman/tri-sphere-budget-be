from datetime import date

from dependencies.services import budget_svc_dep
from fastapi import APIRouter

from app.core.db_models.budget_models import MonthlyBudgetRes

budget_router = APIRouter(prefix='/budget')


@budget_router.get('/expense')
async def get_budget(budget_svc: budget_svc_dep, month: date, category_id: int) -> MonthlyBudgetRes:
    return await budget_svc.get_budget_for_month(month, category_id)
