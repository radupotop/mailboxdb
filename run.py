import email
import hashlib
from configparser import ConfigParser
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL

from model import Attachment, MsgMeta, RawMsg, get_latest_uid


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

    latest_uid = get_latest_uid()

    if latest_uid:
        box_status, box_data = mbox.uid('search', None, 'UID', latest_uid + ':*')
    else:
        box_status, box_data = mbox.uid('search', None, 'ALL')
    
    if box_status != OK_STATUS:
        return

    message_uids = box_data[0].split()

    if latest_uid:
        message_uids.remove(latest_uid.encode())

    print(latest_uid)
    print(len(message_uids))

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
        
        # We need to parse attachments first.
        # They are extracted and removed from messages.
        _attachments = [process_attachment(part) for part in email_msg.walk()]
        attachments = list(filter(None, _attachments))
        has_attachments = len(attachments) > 0

        rmsg = RawMsg.create(email_blob=email_msg.as_bytes(), checksum=checksum)

        if has_attachments:
            for file_checksum, filename, content_type in attachments:
                print(file_checksum, filename, content_type)
                Attachment.create(
                    file_checksum=file_checksum,
                    rawmsg_checksum=checksum,
                    filename=filename,
                    content_type=content_type,
                )

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
                    has_attachments=has_attachments,
                )

        print(m_uid, from_, to, subject)

def process_attachment(part: Message):
    """
    Remove attachments from email messages and save them as files.
    The message will be altered.
    """

    filename = part.get_filename()
    if not filename:
        return

    content_type = part.get_content_type()
    payload = part.get_payload(decode=True)
    file_checksum = hashlib.sha256(payload).hexdigest()

    fp = open('attachments/' + file_checksum, 'wb')
    fp.write(payload)
    fp.close()
    
    part.set_param(file_checksum, None, header='X-File-Checksum')
    part.set_payload(None)

    return file_checksum, filename, content_type



mbox = connect()
message_uids = get_message_uids(mbox)
all_msg_gen = fetch_all_messages(message_uids)

for msg in all_msg_gen:
    process_message(*msg)


mbox.logout()
