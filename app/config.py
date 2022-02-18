import os
from configparser import ConfigParser

CONFIG_FILE = os.getenv('CONFIG_FILE', 'credentials.ini')


def parse_config():
    """
    Read credentials from INI file.
    """
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return config.defaults()
