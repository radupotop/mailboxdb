import email
import hashlib
from imaplib import IMAP4_SSL
from typing import Generator, List

from config import ConfigReader
from logger import get_logger
from model import MsgMeta

log = get_logger(__name__)

ListUIDs = List[bytes]
OK_STATUS = 'OK'


class Mbox:
    """
    Methods for handling IMAP4 mailboxes.
    """

    def __init__(self, settings: ConfigReader):
        """
        Connect to IMAP4 server.
        """
        self.mbox = IMAP4_SSL(settings.server)
        self.mbox.login(settings.username, settings.password)
        log.info('Successfully logged in.')

    def get_message_uids(self, label: str = 'INBOX') -> ListUIDs | None:
        """
        Get all message UIDs to be fetched from server.
        Resume from the `latest UID` if there is one found.
        """
        self.mbox.select(label, readonly=True)
        # self.mbox.select('"[Gmail]/All mail"', readonly=True)

        latest_uid = MsgMeta.get_latest_uid()

        if latest_uid:
            box_status, box_data = self.mbox.uid('search', None, 'UID', f'{latest_uid}:*')
            log.info('Resuming from the latest UID: %s', latest_uid)
        else:
            box_status, box_data = self.mbox.uid('search', None, 'ALL')
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

    def fetch_all_messages(self, message_uids: ListUIDs) -> Generator:
        """
        Fetch each eligible message in RFC822 format.
        Returns a generator.
        """
        for m_uid in message_uids:
            msg_status, msg_data = self.mbox.uid('fetch', m_uid, '(RFC822)')

            if msg_status != OK_STATUS:
                log.warning('Message UID %s was not OK', m_uid)
                yield None

            raw_email = msg_data[0][1]
            checksum = hashlib.sha256(raw_email).hexdigest()
            email_msg = email.message_from_bytes(raw_email)

            yield email_msg, checksum, m_uid

    def logout(self):
        self.mbox.logout()
