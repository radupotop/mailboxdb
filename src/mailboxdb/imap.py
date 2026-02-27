from imaplib import IMAP4_SSL

from mailboxdb.config import Config
from mailboxdb.helpers import email_from_bytes, sha256sum
from mailboxdb.imap_xoauth import authenticate_xoauth2, use_xoauth2
from mailboxdb.logger import get_logger
from mailboxdb.schema import (
    NO_CHARSET,
    OK_STATUS,
    ListUIDs,
    MboxResults,
    MboxResultsGenerator,
)


class Mbox:
    """
    Methods for handling IMAP4 mailboxes.
    """

    def __init__(self, settings: Config):
        """
        Connect to IMAP4 server.
        """
        self.log = get_logger(self.__class__.__name__)
        self.mbox = IMAP4_SSL(settings.server)
        if use_xoauth2(settings):
            authenticate_xoauth2(self.mbox, settings)
        else:
            self.mbox.login(settings.username, settings.password)
        self.log.info('Successfully logged in.')

    def get_message_uids(
        self, latest_uid: str | None, label: str = 'INBOX'
    ) -> ListUIDs | None:
        """
        Get all message UIDs to be fetched from server.
        Resume from the `latest UID` if there is one found.
        """
        self.mbox.select(label, readonly=True)
        # self.mbox.select('"[Gmail]/All mail"', readonly=True)

        if latest_uid:
            box_status, box_data = self.mbox.uid(
                'search', NO_CHARSET, 'UID', f'{latest_uid}:*'
            )
            self.log.info('Resuming from the latest UID: %s', latest_uid)
        else:
            box_status, box_data = self.mbox.uid('search', NO_CHARSET, 'ALL')
            self.log.info('Fetching ALL messages.')

        if box_status != OK_STATUS:
            self.log.error('Mbox error: %s', box_status)
            return None

        # This will be a list of bytes
        message_uids = box_data[0].split()

        if latest_uid and latest_uid.encode() in message_uids:
            message_uids.remove(latest_uid.encode())

        self.log.info('Message count: %s', len(message_uids))

        return message_uids

    def fetch_all_messages(self, message_uids: ListUIDs) -> MboxResultsGenerator:
        """
        Fetch each eligible message in RFC822 format.
        Returns a generator.
        """
        for m_uid in message_uids:
            msg_status, msg_data = self.mbox.uid('fetch', m_uid.decode(), '(RFC822)')

            if msg_status != OK_STATUS:
                self.log.warning('Message UID is not OK: %s', m_uid)
                continue  # skip

            raw_email: bytes = msg_data[0][1]
            checksum = sha256sum(raw_email)
            email_msg = email_from_bytes(raw_email)

            yield MboxResults(email_msg, checksum, m_uid)

    def logout(self):
        self.mbox.logout()
        self.log.info('Logged out')
