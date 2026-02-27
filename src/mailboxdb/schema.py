from collections.abc import Generator
from email.message import Message
from typing import Any, NamedTuple, TypeAlias, cast

NO_CHARSET = cast(Any, None)
OK_STATUS = 'OK'
UID: TypeAlias = bytes
ListUIDs: TypeAlias = list[UID]


class MboxResults(NamedTuple):
    message: Message
    checksum: str
    uid: UID


MboxResultsGenerator: TypeAlias = Generator[MboxResults]


class AttachmentProperties(NamedTuple):
    file_checksum: str
    filename: str
    content_type: str
