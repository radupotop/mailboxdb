import logging


def configure_root_logger(level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def quiet_root_logger():
    configure_root_logger(logging.ERROR)


configure_root_logger()
