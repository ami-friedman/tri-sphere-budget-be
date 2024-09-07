from typing import Generator

import pytest
from sqlmodel import Session

from app.core.db import engine
from app.core.db import init_db


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db()
        yield session
