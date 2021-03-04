#!/usr/bin/env python

import logging
import random
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logging.basicConfig()
log = logging.getLogger('compose-email')
log.setLevel(logging.INFO)

LOREM_IMPSUM_PATH = 'tests/fixtures/lorem_ipsum.txt'
LF = '\n'


def read_lipsum():
    lipsum = Path(LOREM_IMPSUM_PATH)
    lipsum_list = lipsum.read_text().split(LF)
    rnd_line = random.randint(0, len(lipsum_list) - 1)
    return lipsum_list[rnd_line]


def compose_email():
    """
    Compose an email with MIME type multipart/alternative.
    """
    now = datetime.utcnow()
    msg = MIMEMultipart('alternative')

    msg['Subject'] = f'Test Email {now}'
    msg['From'] = 'test@localhost'
    msg['To'] = 'test2@localhost'

    text = read_lipsum()
    html_body = f'<strong><em>{text}</em></strong>'

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html_body, 'html')

    msg.attach(part1)
    msg.attach(part2)

    return msg
