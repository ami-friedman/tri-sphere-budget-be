import logging
import sys


class Logger:
    log_name = 'Tri-Sphere-Budget'

    def __init__(self):
        self.log = logging.getLogger(self.log_name)
        self.log.setLevel('INFO')
        self._add_log_handlers()

    def _add_log_handlers(self):
        """
        Configure logger's handler based on the environment.
        Allows to output logs to Google Cloud Logging when deployed in Kubernetes or to the console for local run.
        """
        handler = self._get_console_handler()
        self.log.addHandler(handler)
        self.log.propagate = False
        self._stream_logs_to_current_logger(logger_to_stream="waitress")  # stream waitress logs

    @staticmethod
    def _get_console_handler() -> logging.Handler:
        console_handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter('%(asctime)s : %(name)-13s : %(levelname)s :: %(message)s')
        console_handler.setFormatter(formatter)
        return console_handler

    def _stream_logs_to_current_logger(self, logger_to_stream: str, logger_to_stream_level=logging.WARNING):
        """Sets up a stream handler for a specified logger to redirect logs to current logger"""

        class StreamHandler(logging.Handler):
            def __init__(self, my_logger):
                super().__init__()
                self.logger = my_logger

            def emit(self, record):
                log_msg = self.format(record)
                log_msg = f'{logger_to_stream}: {log_msg}'
                self.logger.log.log(record.levelno, log_msg)

        streamed_logger = logging.getLogger(logger_to_stream)
        streamed_logger.setLevel(logger_to_stream_level)
        streamed_logger.propagate = False
        streamed_logger.addHandler(StreamHandler(my_logger=self))


logger = Logger().log
