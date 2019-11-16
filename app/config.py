from configparser import ConfigParser


def parse_config():
    """
    Read credentials from INI file.
    """
    config = ConfigParser()
    config.read('credentials.ini')
    return config.defaults()
