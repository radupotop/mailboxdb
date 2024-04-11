#!/usr/bin/env python
#
# Upload test emails to the local Dovecot instance
# using IMAP append.
#

import os
from email.message import EmailMessage
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from time import time

from tests.composeemail import compose_email

SERVER = os.getenv('IMAP_HOSTNAME', 'localhost')
USERNAME = os.getenv('USERNAME', 'testuser')
PASSWORD = os.getenv('PASSWORD', 'pass')
MAILBOX = os.getenv('MAILBOX', 'INBOX')


def _auth() -> IMAP4:
    mbox = IMAP4_SSL(SERVER)
    mbox.login(USERNAME, PASSWORD)
    return mbox


def append_email(mbox: IMAP4, msg: EmailMessage):
    return mbox.append(MAILBOX, None, Time2Internaldate(time()), msg.as_bytes())


def populate_emails(do_dupes=False, count=10):
    mbox = _auth()
    emails = [compose_email() for _ in range(count)]
    if do_dupes:
        emails += emails[: int(count / 2)]
    resp = tuple(append_email(mbox, eml) for eml in emails)
    return emails, resp


if __name__ == '__main__':
    from pprint import pprint

    pprint(populate_emails(do_dupes=True))
