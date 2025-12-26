import ast
import subprocess

from mailboxdb.config import ConfigReader


def use_xoauth2(settings: ConfigReader) -> bool:
    raw = getattr(settings, 'use_xoauth2', False)
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def password_command(settings: ConfigReader) -> tuple[str, ...]:
    raw = getattr(settings, 'password_command', None)
    if raw is None:
        raise RuntimeError('password_command must be set when use_xoauth2 is enabled')
    if isinstance(raw, (list, tuple)):
        command = raw
    else:
        raw_str = str(raw).strip()
        try:
            command = ast.literal_eval(raw_str)
        except (ValueError, SyntaxError) as err:
            raise RuntimeError(
                'password_command must be a tuple like ("cmd", "arg")'
            ) from err
    if not isinstance(command, (list, tuple)) or not command:
        raise RuntimeError('password_command must be a non-empty tuple')
    return tuple(str(part) for part in command)


def command_token(command: tuple[str, ...]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def xoauth2_string(user: str, token: str) -> bytes:
    return f'user={user}\x01auth=Bearer {token}\x01\x01'.encode()


def authenticate_xoauth2(mbox, settings: ConfigReader) -> None:
    command = password_command(settings)
    token = command_token(command)
    mbox.authenticate('XOAUTH2', lambda _: xoauth2_string(settings.username, token))
