"""
Methods for handling IMAP4 mailboxes.
"""

import email
import hashlib
import logging
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL
from types import ListUIDs
from typing import Optional

from config import parse_config
from logger import get_logger
from model import MsgMeta

log = get_logger(__name__)

OK_STATUS = 'OK'


def connect_mbox() -> IMAP4:
    """
    Connect to IMAP4 server.
    """
    settings = parse_config()
    mbox = IMAP4_SSL(settings['server'])
    mbox.login(settings['username'], settings['password'])
    log.info('Successfully logged in.')
    return mbox


def get_message_uids(mbox: IMAP4, label: str = 'INBOX') -> Optional[ListUIDs]:
    """
    Get all message UIDs to be fetched from server.
    Resume from the `latest UID` if there is one found.
    """
    mbox.select(label, readonly=True)
    # mbox.select('"[Gmail]/All mail"', readonly=True)

    latest_uid = MsgMeta.get_latest_uid()

    if latest_uid:
        box_status, box_data = mbox.uid('search', None, 'UID', latest_uid + ':*')
        log.info('Resuming from the latest UID: %s', latest_uid)
    else:
        box_status, box_data = mbox.uid('search', None, 'ALL')
        log.info('Fetching ALL messages.')

    if box_status != OK_STATUS:
        log.error('Mbox error: %s', box_status)
        return None

    # This will be a list of bytes
    message_uids = box_data[0].split()

    if latest_uid and latest_uid.encode() in message_uids:
        message_uids.remove(latest_uid.encode())

    log.info('Message count: %s', len(message_uids))

    return message_uids


def fetch_all_messages(mbox: IMAP4, message_uids: ListUIDs):
    """
    Fetch each eligible message in RFC822 format.
    Returns a generator.
    """
    for m_uid in message_uids:
        msg_status, msg_data = mbox.uid('fetch', m_uid, '(RFC822)')

        if msg_status != OK_STATUS:
            log.warning('Message UID %s was not OK', m_uid)
            yield None

        raw_email = msg_data[0][1]
        checksum = hashlib.sha256(raw_email).hexdigest()
        email_msg = email.message_from_bytes(raw_email)

        yield email_msg, checksum, m_uid
