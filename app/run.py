import argparse
import email
import hashlib
from configparser import ConfigParser
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL

from model import Attachment, MsgMeta, RawMsg, db, pw


OK_STATUS = 'OK'


def _parse_config():
    """
    Read credentials from INI file.
    """
    config = ConfigParser()
    config.read('credentials.ini')
    return config.defaults()

def connect():
    """
    Connect to IMAP4 server.
    """
    settings = _parse_config()
    mbox = IMAP4_SSL(settings['server'])
    mbox.login(settings['username'], settings['password'])
    return mbox

def get_message_uids(mbox: IMAP4, label='INBOX'):
    """
    Get all message UIDs to be fetched from server.
    Resume from the `latest UID` if there is one found.
    """
    mbox.select(label, readonly=True)
    # mbox.select('"[Gmail]/All Mail"', readonly=True)

    latest_uid = MsgMeta.get_latest_uid()

    if latest_uid:
        box_status, box_data = mbox.uid('search', None, 'UID', latest_uid + ':*')
    else:
        box_status, box_data = mbox.uid('search', None, 'ALL')

    if box_status != OK_STATUS:
        return

    # This will be a list of bytes
    message_uids = box_data[0].split()

    if latest_uid and latest_uid.encode() in message_uids:
        message_uids.remove(latest_uid.encode())

    print(latest_uid)
    print(len(message_uids))

    return message_uids

def fetch_all_messages(mbox: IMAP4, message_uids: list):
    """
    Fetch each eligible message in RFC822 format.
    Returns a generator.
    """
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
    """
    Process an entire message object.

    Split attachment files from rawmsg, create db entries for
    each rawmsg, message meta and attachment.
    """

    # We need to parse attachments first.
    # They are extracted and removed from messages.
    _attachments = [process_attachment(part) for part in email_msg.walk()]
    attachments = list(filter(None, _attachments))
    has_attachments = len(attachments) > 0

    # Parse metadata
    from_ = email_msg.get('From')
    to = email_msg.get('To')
    subject = email_msg.get('Subject')
    date = email.utils.parsedate_to_datetime(email_msg.get('Date')) if email_msg.get('Date') else None

    with db.atomic():
        rmsg = RawMsg.create(email_blob=email_msg.as_bytes(), original_checksum=checksum)

        if has_attachments:
            for file_checksum, filename, content_type in attachments:
                print(file_checksum, filename, content_type)
                att = Attachment.create(
                    checksum=file_checksum,
                    original_filename=filename,
                    content_type=content_type,
                )
                rmsg.attachments.add(att)

        mmeta = MsgMeta.create(
                    rawmsg=rmsg,
                    imap_uid=m_uid,
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
    payload = part.get_payload(decode=True) # decode from base64
    file_checksum = hashlib.sha256(payload).hexdigest()

    fp = open('attachments/' + file_checksum, 'wb')
    fp.write(payload)
    fp.close()

    part.set_param(file_checksum, None, header='X-File-Checksum')
    part.set_payload(None)

    return file_checksum, filename, content_type


def run():
    db.connect()
    mbox = connect()
    message_uids = get_message_uids(mbox)
    all_msg_gen = fetch_all_messages(mbox, message_uids)

    # Accept that the first message might be a duplicate.
    # This is because IMAP fetch will always get the latest message from the mailbox,
    # even if the UID we specify is higher than the latest one.
    try:
        first_msg = next(all_msg_gen)
        process_message(*first_msg)
    except pw.IntegrityError as err:
        if 'UNIQUE constraint failed: rawmsg.checksum' in str(err):
            print('Duplicate first message, carry on.')
        else:
            raise err
    except StopIteration:
        print('No new messages.')

    for msg in all_msg_gen:
        process_message(*msg)

    mbox.logout()


def bootstrap():
    db.connect()
    db.create_tables([
        RawMsg, MsgMeta, Attachment,
        Attachment.rawmsg.get_through_model()
    ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', action='store_true', help='Configure the db')
    parser.add_argument('-r', '--run', action='store_true', help='Run main loop')
    parser.add_argument('-q', '--quiet', action='store_true', help='Do not output anything')
    parser.add_argument('--debug', action='store_true', help='Output debug messages')
    args = parser.parse_args()

    if args.run:
        run()
    elif args.config:
        try:
            bootstrap()
        except pw.OperationalError as err:
            if 'already exists' in str(err):
                print('The database is already configured.')
            else:
                raise err
    else:
        parser.print_help()
