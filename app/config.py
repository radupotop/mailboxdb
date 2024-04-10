from configparser import ConfigParser


class INIConfigReader:
    def __init__(self, filename='credentials.ini'):
        config = ConfigParser()
        config.read(filename)
        config_dict = config.defaults()
        for k, v in config_dict.items():
            setattr(self, str(k), v)
