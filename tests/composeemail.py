#!/usr/bin/env python
#
# This is only used to build test emails.

import logging
import mimetypes
import random
from datetime import datetime
from email import encoders
from email.headerregistry import Address
from email.message import EmailMessage
from pathlib import Path
from typing import Tuple, Union

logging.basicConfig()
log = logging.getLogger('compose-email')
log.setLevel(logging.INFO)

ATTACHMENT_PATH = 'tests/fixtures/attachments/'
LOREM_IMPSUM_PATH = 'tests/fixtures/lorem_ipsum.txt'
LF = '\n'


def _read_lipsum() -> str:
    lipsum = Path(LOREM_IMPSUM_PATH)
    assert lipsum.is_file
    lipsum_list = lipsum.read_text().split(LF)
    rnd_line = random.randint(0, len(lipsum_list) - 1)
    return lipsum_list[rnd_line]


def _read_attach() -> Path:
    att_path = Path(ATTACHMENT_PATH)
    assert att_path.is_dir
    file_list = list(att_path.iterdir())
    rnd_idx = random.randint(0, len(file_list) - 1)
    rnd_file = file_list[rnd_idx]
    assert rnd_file.is_file
    return rnd_file


def _guess_mime(file_path: Union[Path, str]) -> Tuple[str, str]:
    ctype, _ = mimetypes.guess_type(str(file_path))
    if isinstance(ctype, str):
        maintype, subtype = ctype.split('/', 1)
    else:
        maintype, subtype = 'application', 'octet-stream'
    return maintype, subtype


def compose_email(has_attachment: bool = True, save_output: bool = False) -> EmailMessage:
    now = datetime.utcnow().isoformat()

    eml = EmailMessage()
    eml['Subject'] = f'Test Email Attachment {has_attachment}, Datetime {now}'
    eml['From'] = Address('Test1', 'test1', 'example.org')
    eml['To'] = Address('Test2', 'test2', 'example.org')
    eml.preamble = 'Preamble'

    text = _read_lipsum()
    html_body = f'<blockquote><strong><em>{text}</em></strong></blockquote>'

    eml.set_content(text)
    eml.add_alternative(html_body, subtype='html')

    if has_attachment:
        att = _read_attach()
        maintype, subtype = _guess_mime(att)
        eml.add_attachment(
            att.read_bytes(), filename=att.name, maintype=maintype, subtype=subtype
        )
        if save_output:
            Path(f'test_email_{now}.eml').write_bytes(eml.as_bytes())

    return eml
