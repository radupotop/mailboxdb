import email
import hashlib
from base64 import decodebytes
from configparser import ConfigParser
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL

from model import Attachment, MsgMeta, RawMsg


OK_STATUS = 'OK'


def _parse_config():
    config = ConfigParser()
    config.read('credentials.ini')
    return config.defaults()

def connect():
    settings = _parse_config()
    mbox = IMAP4_SSL(settings['server'])
    mbox.login(settings['username'], settings['password'])
    return mbox

def get_message_uids(mbox: IMAP4, label='INBOX'):
    mbox.select(label, readonly=True)
    # mbox.select('"[Gmail]/All Mail"', readonly=True)

    box_status, box_data = mbox.uid('search', None, 'ALL')
    # box_status, box_data = mbox.uid('search', None, 'UID', start_message_uid + ':*')
    
    if box_status != OK_STATUS:
        return

    message_uids = box_data[0].split()
    return message_uids

def fetch_all_messages(message_uids: list):
    for m_uid in message_uids:
        msg_status, msg_data = mbox.uid('fetch', m_uid, '(RFC822)')

        if msg_status != OK_STATUS:
            print('Message {} not OK'.format(m_uid))
            yield False

        raw_email = msg_data[0][1]
        checksum = hashlib.sha256(raw_email).hexdigest()
        email_msg = email.message_from_bytes(raw_email)

        yield email_msg, checksum, m_uid

def process_message(email_msg: Message, checksum: str, m_uid: str):

        for part in email_msg.walk():
            process_attachment(part, checksum)

        rmsg = RawMsg.create(email_blob=email_msg.as_bytes(), checksum=checksum)

        # Parse metadata
        from_ = email_msg.get('From')
        to = email_msg.get('To')
        subject = email_msg.get('Subject')
        date = email.utils.parsedate_to_datetime(email_msg.get('Date'))

        mmeta = MsgMeta.create(
                    imap_uid=m_uid,
                    checksum=checksum,
                    from_=from_,
                    to=to,
                    subject=subject,
                    date=date,
                )

        print(m_uid, from_, to, subject)

def process_attachment(part: Message, checksum: str):

    filename = part.get_filename()
    if not filename:
        return

    content_type = part.get_content_type()
    payload = part.get_payload().encode()
    file_checksum = hashlib.sha256(payload).hexdigest()

    Attachment.create(
        file_checksum=file_checksum,
        rawmsg_checksum=checksum,
        filename=filename,
        content_type=content_type,
    )

    part.set_param(file_checksum, None, header='X-File-Checksum')
    part.set_payload(None)

    fp = open('attachments/' + file_checksum, 'wb')
    fp.write(decodebytes(payload))
    fp.close()

    return file_checksum




mbox = connect()
message_uids = get_message_uids(mbox)
all_msg_gen = fetch_all_messages(message_uids)

for msg in all_msg_gen:
    process_message(*msg)


mbox.logout()
