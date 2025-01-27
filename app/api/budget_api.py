from datetime import date

from fastapi import APIRouter

from app.core.db_models.budget_models import MonthlyBudgetRes
from app.dependencies.db_session import DbSession
from app.services.budget_service import get_budget_for_month

budget_router = APIRouter(prefix='/budget')


@budget_router.get('/expense')
async def get_budget(month: date, category_id: int, session: DbSession) -> MonthlyBudgetRes:
    return get_budget_for_month(session, month, category_id)
