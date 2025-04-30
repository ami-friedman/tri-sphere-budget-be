from typing import Annotated

from fastapi import Depends
from fastapi import Request

from app.features.budget.budget_service import BudgetService


async def get_budget_svc(request: Request) -> BudgetService:
    return BudgetService(sql_manager=request.state.sql_manager)


budget_svc_dep = Annotated[BudgetService, Depends(get_budget_svc)]
