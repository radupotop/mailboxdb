import logging


def configure_root_logger(level=logging.INFO):
    logging.basicConfig()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    return root_logger


def get_logger(name: str):
    return logging.getLogger(name)


def quiet_root_logger():
    configure_root_logger(logging.ERROR)


configure_root_logger()
