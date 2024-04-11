import email
import hashlib
from email.message import Message
from pathlib import Path

from mailboxdb.imap import MboxResults
from mailboxdb.logger import get_logger
from mailboxdb.model import Attachment, MsgMeta, RawMsg, db

log = get_logger(__name__)

AttachmentProperties = tuple[str, str, str]


def process_message(result: MboxResults):
    """
    Process an entire message object.

    Split attachment files from rawmsg, create db entries for
    each rawmsg, message meta and attachment.
    """
    email_msg, checksum, m_uid = result

    # We need to parse attachments first.
    # They are extracted and removed from messages.
    _attachments = [process_attachment(part) for part in email_msg.walk()]
    attachments: list[AttachmentProperties] = list(filter(None, _attachments))
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

        MsgMeta.create(
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


def process_attachment(part: Message) -> AttachmentProperties | None:
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
    file_path = Path('attachments/', file_checksum)

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
