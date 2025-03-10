from fastapi import FastAPI

from app import lifespan
from app.api.budget_api import budget_router

app = FastAPI(lifespan=lifespan)
app.include_router(budget_router)
