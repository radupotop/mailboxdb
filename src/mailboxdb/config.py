import configparser
from dataclasses import Field, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    server: str = 'localhost'
    username: str = 'testuser'
    password: str = 'pass'
    # Optional: fetch from a specific mailbox (defaults to INBOX).
    mailbox: str = 'INBOX'
    # Optional: use XOAUTH2 with a command that returns the access token.
    use_xoauth2: bool = False
    password_command: str = '/usr/bin/oama access username@example.com'

    @staticmethod
    def _coerce_value(field: Field, raw_value: str) -> Any:
        if field.type is bool:
            return raw_value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}
        if field.name.endswith('_command'):
            return tuple(raw_value.split())
        return raw_value

    @classmethod
    def from_ini(cls, filename: str = 'credentials.ini') -> 'Config':
        if not Path(filename).is_file():
            raise RuntimeError(f'Config file not found {filename}')

        parser = configparser.ConfigParser()
        parser.read(filename)
        ini_file = parser.defaults()
        config_dict = dict()

        for cf in fields(cls):
            raw_value = ini_file.get(cf.name)
            if raw_value:
                config_dict[cf.name] = cls._coerce_value(cf, raw_value)
        return cls(**config_dict)
