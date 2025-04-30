from exceptions import ConflictException
from exceptions import DBException
from exceptions import NotFoundException
from fastapi import Request
from fastapi.applications import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from logger import log
from starlette import status
from starlette.responses import PlainTextResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    url = request.url.path
    method = request.method
    log.warning(f'{method} request to {url=} resulted with validation error', exc_info=exc)
    return await request_validation_exception_handler(request, exc)


async def db_error_exception_handler(request: Request, exc: DBException):
    """Return response for issues with storage DB"""
    url = request.url.path
    method = request.method
    log.error(f'{method} request to {url=} resulted with DB exception', exc_info=exc)
    return PlainTextResponse(exc.msg, status_code=status.HTTP_400_BAD_REQUEST)


async def conflict_error_exception_handler(request: Request, exc: ConflictException):
    """Return response for issues with conflict in db"""
    url = request.url.path
    method = request.method
    log.info(f'{method} request to {url=} resulted with not found exception', exc_info=exc)
    return PlainTextResponse(exc.msg, status_code=status.HTTP_409_CONFLICT)


async def not_found_error_exception_handler(request: Request, exc: NotFoundException):
    """Return response for issues with not found objects"""
    url = request.url.path
    method = request.method
    log.info(f'{method} request to {url=} resulted with not found exception', exc_info=exc)
    return PlainTextResponse(exc.msg, status_code=status.HTTP_404_NOT_FOUND)


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return response for any unhandled exceptions"""
    url = request.url.path
    method = request.method
    log.critical(f'{method} request to {url=} resulted with unhandled exception', exc_info=exc)
    return PlainTextResponse('An unexpected error occurred', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def add_handlers(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DBException, db_error_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_error_exception_handler)
    app.add_exception_handler(ConflictException, conflict_error_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
