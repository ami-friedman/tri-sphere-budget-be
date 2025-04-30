from typing import TypedDict

from database.sql_mgr import SQLManager


class AppState(TypedDict):
    """
    Put here any object that Vortex needs access to across requests.
    Usually instantiated and destructed in lifespan
    """

    sql_manager: SQLManager
