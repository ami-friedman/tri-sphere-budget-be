from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.core.db import engine


async def get_session() -> Session:
    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]
