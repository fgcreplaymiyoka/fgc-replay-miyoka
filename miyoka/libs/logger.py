import logging
from logging import Logger
import os
from pythonjsonlogger import jsonlogger

formatter = jsonlogger.JsonFormatter()


def setup_logger(
    name: str,
    dir_path: str,
    file_name: str,
    clear_everytime: bool,
    file_output: bool,
    standard_output: bool,
    level=logging.INFO,
) -> Logger:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    log_path = os.path.join(dir_path, file_name)

    if os.path.exists(log_path) and clear_everytime:
        os.remove(log_path)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if file_output:
        fh = logging.FileHandler(log_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if standard_output:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
