class TSBBaseException(Exception):
    """Base Tri Sphere Budget exception for all custom exceptions"""

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return f"{type(self).__name__}: {self.msg}"


class NotFoundException(TSBBaseException):
    """Raised exception for not found data"""


class DBException(TSBBaseException):
    """Raised exception for issues with actions in DB"""


class ConflictException(DBException):
    """Raised exception when data already exists in DB"""
