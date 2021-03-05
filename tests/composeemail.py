#!/usr/bin/env python
#
# Test helper for composing emails.

import logging
import random
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logging.basicConfig()
log = logging.getLogger('compose-email')
log.setLevel(logging.INFO)

ATTACHMENT_PATH = 'tests/fixtures/attachments/'
LOREM_IMPSUM_PATH = 'tests/fixtures/lorem_ipsum.txt'
LF = '\n'


def read_lipsum() -> str:
    lipsum = Path(LOREM_IMPSUM_PATH)
    assert lipsum.is_file
    lipsum_list = lipsum.read_text().split(LF)
    rnd_line = random.randint(0, len(lipsum_list) - 1)
    return lipsum_list[rnd_line]


def read_attach() -> tuple(bytes, str):
    att_path = Path(ATTACHMENT_PATH)
    assert att_path.is_dir
    file_list = list(att_path.iterdir())
    rnd_idx = random.randint(0, len(file_list) - 1)
    rnd_file = file_list[rnd_idx]
    return rnd_file.read_bytes(), rnd_file.name


def compose_alternative():
    """
    Compose an email with multipart/alternative MIME type.
    """
    now = datetime.utcnow()
    msg = MIMEMultipart('alternative')

    msg['Subject'] = f'Test Email Alternative {now}'
    msg['From'] = 'test1@localhost'
    msg['To'] = 'test2@localhost'

    text = read_lipsum()
    html_body = f'<strong><em>{text}</em></strong>'

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    return msg


def _build_attachment_part():
    bin_attach, filename = read_attach()
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(bin_attach)
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename={filename}',
    )
    return part


def compose_attachment():
    """
    Compose a multipart/mixed email message with:
    - a multipart/alternative part
    - an encoded attachment part
    """
    now = datetime.utcnow()
    msg = MIMEMultipart()  # mixed

    msg['Subject'] = f'Test Email Attachment {now}'
    msg['From'] = 'test3@localhost'
    msg['To'] = 'test4@localhost'

    msg.attach(compose_alternative())
    msg.attach(_build_attachment_part())
    return msg
