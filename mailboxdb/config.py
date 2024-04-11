import configparser
from pathlib import Path


class INIConfigReader:
    def __init__(self, filename='credentials.ini'):
        if not Path(filename).is_file():
            raise RuntimeError(f'Config file not found {filename}')
        config = configparser.ConfigParser()
        config.read(filename)
        config_dict = config.defaults()
        for k, v in config_dict.items():
            setattr(self, str(k), v)


class ConfigReader(INIConfigReader):
    pass
