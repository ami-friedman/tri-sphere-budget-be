import contextlib

from fastapi import FastAPI

from app.core.db import init_db


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
