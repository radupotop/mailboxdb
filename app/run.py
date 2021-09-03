import argparse
import email
import hashlib
import logging
from configparser import ConfigParser
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL
from pathlib import Path

from imap import connect_mbox, fetch_all_messages, get_message_uids
from model import Attachment, MsgMeta, RawMsg, db, pw

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

OK_STATUS = 'OK'


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
    date = (
        email.utils.parsedate_to_datetime(email_msg.get('Date'))
        if email_msg.get('Date')
        else None
    )

    with db.atomic():
        rmsg = RawMsg.create(email_blob=email_msg.as_bytes(), original_checksum=checksum)

        if has_attachments:
            for file_checksum, filename, content_type in attachments:
                log.debug(file_checksum, filename, content_type)
                att = Attachment.create(
                    file_checksum=file_checksum,
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

    log.debug(m_uid, from_, to, subject)


def process_attachment(part: Message):
    """
    Remove attachments from email messages and save them as files.
    The message will be altered.
    """

    filename = part.get_filename()
    if not filename:
        return None

    content_type = part.get_content_type()
    payload = part.get_payload(decode=True)  # decode from base64
    file_checksum = hashlib.sha256(payload).hexdigest()
    file_path = Path(f'attachments/{file_checksum}')

    if file_path.is_file():
        log.info('Attachment file already exists for: %s', file_checksum)
        log.info('Probably from a previous message. Skipping.')
    else:
        file_path.write_bytes(payload)

    part.set_param(file_checksum, None, header='X-File-Checksum')
    part.set_payload(None)

    return file_checksum, filename, content_type


def run():
    db.connect()
    mbox = connect_mbox()
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
            log.info('Duplicate first message, carry on.')
        else:
            raise err
    except StopIteration:
        log.info('No new messages.')

    for msg in all_msg_gen:
        process_message(*msg)

    mbox.logout()


def bootstrap():
    db.connect()
    db.create_tables([RawMsg, MsgMeta, Attachment, Attachment.rawmsg.get_through_model()])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', action='store_true', help='Configure the db')
    parser.add_argument('-r', '--run', action='store_true', help='Run main loop')
    parser.add_argument(
        '-q', '--quiet', action='store_true', help='Do not output anything'
    )
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
