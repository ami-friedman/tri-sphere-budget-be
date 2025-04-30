import contextlib
from typing import AsyncIterator

from app_state import AppState
from database.sql_mgr import SQLManager
from exception_handlers import add_handlers
from fastapi import FastAPI
from features.budget.budget_router import budget_router
from settings import settings


def load_app_state() -> AppState:
    db_uri = (
        f'{settings.sqldb.cfg_db_user}:{settings.sqldb.cfg_db_password}'  # noqa: E231
        f'@{settings.sqldb.cfg_db_host}:{settings.sqldb.cfg_db_port}/{settings.sqldb.cfg_db_name}'  # noqa: E231
    )
    sql_manager = SQLManager(
        db_uri=db_uri, sync_engine_uri=settings.sqldb.cfg_db_engine, async_engine_uri=settings.sqldb.cfg_async_db_engine
    )
    return AppState(sql_manager=sql_manager)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[AppState]:
    yield load_app_state()


def create_app() -> FastAPI:
    """
    Following the "factory" pattern: https://www.uvicorn.org/#application-factories
    """
    app = FastAPI(lifespan=lifespan)
    app.include_router(budget_router)
    add_handlers(app)

    return app
