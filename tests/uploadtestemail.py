from imaplib import IMAP4_SSL, Time2Internaldate
from time import time

from composeemail import compose_email

SERVER = 'localhost'
USERNAME = 'testuser'
PASSWORD = 'pass'
MAILBOX = 'INBOX'


def auth():
    mbox = IMAP4_SSL(SERVER)
    mbox.login(USERNAME, PASSWORD)
    return mbox


def populate_emails(count=5):
    mbox = auth()
    for m in range(count):
        msg = compose_email()
        mbox.append(MAILBOX, None, Time2Internaldate(time()), msg.as_bytes())
        # print(msg)
