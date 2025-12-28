# src/logger/logger.py

from typing import Any
from os.path import join as os_path_join

from logging import basicConfig as logging_basicConfig
from logging import getLogger as logging_getLogger

from logging import debug as logging_debug
from logging import info as logging_info
from logging import warning as logging_warning
from logging import error as logging_error
from logging import critical as logging_critical


class LoggerBaseError(Exception):
    """Base exception for logger errors"""


class LoggerTypeError(TypeError):
    """Raised when a value is not of the expected type"""


class LoggerValueError(ValueError):
    """Raised when a value is not valid"""


class Logger:
    _config: Any = None  # Must be YamlConfigLoader

    @staticmethod
    def initialize(config_loader: Any, root_dir: str = ".") -> None:
        Logger._config = config_loader
        logging_basicConfig(
            filename=os_path_join(root_dir, Logger._config.get_required("logging.filename")),
            filemode=Logger._config.get_required("logging.filemode"),
            level=Logger._config.get_required("logging.level").upper(),
            format=Logger._config.get_required("logging.format"),
        )

    @staticmethod
    def log(level: str, module_name: str, message: str, exc_info: bool = False) -> None:
        """
        Log a message with optional exception information.

        Args:
            level: Log level (debug, info, warning, error, critical)
            module_name: Name of the module logging the message
            message: The log message
            exc_info: If True, include exception traceback (only when exception context exists)
        """
        if not isinstance(level, str) or not isinstance(message, str) or not isinstance(module_name, str):
            raise LoggerTypeError(
                "Level, module_name and message must be strings, but got: "
                f"level: {type(level)}, module_name: {type(module_name)}, message: {type(message)}"
            )

        level = level.lower()  # Non-case sensitive
        module_name = module_name.strip()  # Remove leading and trailing whitespace
        message = message.strip()

        if not level or not module_name or not message:
            raise LoggerValueError("Level, module_name and message can't be empty")

        if level not in ["debug", "info", "warning", "error", "critical"]:
            raise LoggerValueError(f"Invalid log level: {level}")

        # Add module name to the message for better readability and convenience of context understanding
        message = f"[[{module_name}]] {message}"

        if Logger._config.get_required("logging.enable"):
            if level == "debug":
                logging_debug(message)
            elif level == "info":
                logging_info(message)
            elif level == "warning":
                logging_warning(message)
            elif level == "error":
                # Only include exc_info if explicitly requested AND exception context exists
                if exc_info:
                    import sys

                    if sys.exc_info()[0] is not None:
                        logging_error(message, exc_info=True)
                    else:
                        logging_error(message)
                else:
                    logging_error(message)
            elif level == "critical":
                # Only include exc_info if explicitly requested AND exception context exists
                if exc_info:
                    import sys

                    if sys.exc_info()[0] is not None:
                        logging_critical(message, exc_info=True)
                    else:
                        logging_critical(message)
                else:
                    logging_critical(message)
            else:
                raise LoggerValueError(f"Unknown log level: {level}")
        else:
            return  # Do nothing if logging is disabled

    @staticmethod
    def close_handlers() -> None:
        """
        Close all logging handlers and flush their buffers.

        Should be called before copying log files to ensure all log data
        is written to disk and file handles are closed.

        Safe to call multiple times.
        """
        try:
            root_logger = logging_getLogger()
            for handler in root_logger.handlers[:]:  # Copy list to avoid modification during iteration
                try:
                    handler.flush()
                    handler.close()
                    root_logger.removeHandler(handler)
                except Exception:
                    # Ignore errors when closing handlers
                    pass
        except Exception:
            # Ignore all errors - this is cleanup, shouldn't break anything
            pass
