import logging
from loguru import logger
from sys import stdout, _getframe

from backend_src.core.config import Settings


LOGGERS_TO_INTERCEPT = ("fastapi", )


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = _getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class BackendLoggerMixin:
    def setup_logging(self) -> None:
        logger.remove()

        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

        logger.add(
            stdout,
            enqueue=True,
            backtrace=True,
            diagnose=Settings.DEBUG,
            format=console_format,
            level="INFO",
        )

        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            enqueue=True,
            level="DEBUG",
            encoding="utf-8",
            diagnose=Settings.DEBUG,
        )

        logging.root.handlers = [InterceptHandler()]
        logging.root.setLevel(logging.INFO)

        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        for logger_name in LOGGERS_TO_INTERCEPT:
            mod_logger = logging.getLogger(logger_name)
            mod_logger.handlers = [InterceptHandler()]