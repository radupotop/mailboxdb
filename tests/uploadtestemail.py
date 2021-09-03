from email.message import EmailMessage
from imaplib import IMAP4, IMAP4_SSL, Time2Internaldate
from time import time

from tests.composeemail import compose_email

SERVER = 'localhost'
USERNAME = 'testuser'
PASSWORD = 'pass'
MAILBOX = 'INBOX'


def _auth() -> IMAP4:
    mbox = IMAP4_SSL(SERVER)
    mbox.login(USERNAME, PASSWORD)
    return mbox


def append_email(mbox: IMAP4, msg: EmailMessage):
    return mbox.append(MAILBOX, None, Time2Internaldate(time()), msg.as_bytes())


def populate_emails(count=5):
    mbox = _auth()
    emails = tuple(compose_email() for _ in range(count))
    resp = tuple(append_email(mbox, eml) for eml in emails)
    return emails, resp
