#!/usr/bin/env python

import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logging.basicConfig()
log = logging.getLogger('compose-email')
log.setLevel(logging.INFO)


def compose_email(html_body):
    """
    Compose an email with MIME type multipart/alternative.
    """
    msg = MIMEMultipart('alternative')

    msg['Subject'] = 'Test email 1'
    msg['From'] = 'test1@example.org'
    msg['To'] = 'test@example.org'

    text = 'This is the plain text part of the email.'
    html_body = '<p>html email</p>'

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html_body, 'html')

    msg.attach(part1)
    msg.attach(part2)

    log.info('Msg body: ')
    log.info(msg)

    return msg
