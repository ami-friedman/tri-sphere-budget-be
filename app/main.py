from logger import log
from settings import settings


def main():
    import uvicorn

    debug = 'debug' if settings.cfg_local_run else 'info'

    log.info('Starting Vortex BE')
    uvicorn.run('init_app:create_app', host='0.0.0.0', port=8000, log_level=debug, reload=settings.cfg_local_run, factory=True)


if __name__ == '__main__':
    main()
