from functools import wraps
from typing import Any
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists
from sqlmodel import SQLModel

from app.exceptions import ConflictException
from app.exceptions import DBException


class SQLManager:
    def __init__(self, sync_engine_uri: str, async_engine_uri: str, db_uri: str):
        self.db_uri = db_uri
        self.engine: AsyncEngine = create_async_engine(f'{async_engine_uri}://{db_uri}')  # noqa: E231
        self._verify_database_and_tables_exist(f'{sync_engine_uri}://{db_uri}')  # noqa: E231
        self.session = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    @staticmethod
    def db_action(msg: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                async with self.session() as session:
                    try:
                        return await func(self, session, *args, **kwargs)
                    except IntegrityError:
                        await session.rollback()
                        raise ConflictException('The item already exists in database')
                    except Exception as e:
                        await session.rollback()
                        raise DBException(f'{msg}. exception: {e}')

            return wrapper

        return decorator

    @db_action(msg="Failed updating object")
    async def exec(self, session, statement) -> Any:
        return await session.scalars(statement)

    @db_action(msg="Failed updating object")
    async def update_row(self, session, obj) -> Any:
        """Add or update a row at the DB"""
        merged_obj = await session.merge(obj)
        await session.commit()
        await session.refresh(merged_obj)
        return merged_obj

    @db_action(msg="Failed getting all rows")
    async def get_all_rows(self, session, orm, statement) -> list[SQLModel]:
        results = await session.scalars(statement)
        return [orm.model_validate(row) for row in results.all()]

    @db_action(msg="Failed getting row")
    async def get_single_row(self, session, orm, statement) -> Optional[SQLModel]:
        results = await session.scalars(statement)
        if not (row := results.first()):
            return None
        return orm.model_validate(row)

    @db_action(msg="Failed deleting row")
    async def delete_row(self, session, obj, orm):
        db_object = orm.model_validate(obj)
        merged_obj = await session.merge(db_object)
        await session.delete(merged_obj)
        await session.commit()

    @staticmethod
    def _verify_database_and_tables_exist(db_uri: str):
        if not database_exists(db_uri):
            create_database(db_uri)
        SQLModel.metadata.create_all(create_engine(db_uri))
