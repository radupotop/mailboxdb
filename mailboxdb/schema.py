from collections.abc import Generator
from email.message import Message
from typing import NamedTuple

OK_STATUS = 'OK'
UID = bytes

ListUIDs = list[UID]


class MboxResults(NamedTuple):
    message: Message
    checksum: str
    uid: UID


MboxResultsGenerator = Generator[MboxResults | None, None, None]


class AttachmentProperties(NamedTuple):
    file_checksum: str
    filename: str
    content_type: str
