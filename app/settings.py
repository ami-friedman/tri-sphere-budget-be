from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cfg_local_run: bool = False

    class SQLDB(BaseSettings):
        cfg_db_host: str = 'localhost'
        cfg_db_user: str = 'root'
        cfg_db_password: str
        cfg_db_port: int = 3306
        cfg_db_name: str
        cfg_db_engine: str = 'mysql+mysqlconnector'
        cfg_async_db_engine: str = 'mysql+aiomysql'

    sqldb: SQLDB = SQLDB()


settings = Settings()
