import email
import hashlib
import logging
from email.message import Message
from pathlib import Path
from typing import Optional, Tuple

from logger import get_logger
from model import Attachment, MsgMeta, RawMsg, db, pw

log = get_logger(__name__)


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

    log.info(
        'Processed message: m_uid=%s, from_=%s, to=%s, subject=%s',
        m_uid,
        from_,
        to,
        subject,
    )


def process_attachment(part: Message) -> Optional[Tuple[str, str, str]]:
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

    log.debug(
        'Attachment found: file_checksum=%s, filename=%s, content_type=%s',
        file_checksum,
        filename,
        content_type,
    )

    if file_path.is_file():
        log.info('Attachment file already exists for: %s, Skipping', file_checksum)
    else:
        log.info('Writing file: %s', file_checksum)
        file_path.write_bytes(payload)

    part.set_param(file_checksum, None, header='X-File-Checksum')
    part.set_payload(None)

    return file_checksum, filename, content_type
