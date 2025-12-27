import peewee as pw

from mailboxdb.date_helper import utcnow

db = pw.SqliteDatabase('database/messages.db')


class BaseModel(pw.Model):
    class Meta:
        database = db

    id = pw.AutoField()


class RawMsg(BaseModel):
    """
    Raw message as fetched from IMAP server.
    """

    email_body = pw.BlobField(help_text='Email body with attachments removed')
    original_checksum = pw.CharField(
        unique=True,
        help_text='Checksum of the original message from the server',
    )


class AttachmentMeta(BaseModel):
    rawmsg = pw.ManyToManyField(RawMsg, backref='attachments')
    file_checksum = pw.CharField(unique=True, help_text='Checksum of the file on disk')
    original_filename = pw.CharField(help_text='Original filename')
    content_type = pw.CharField(help_text='Original content type')


class Mailbox(BaseModel):
    """
    Sync state for a mailbox.
    """

    name = pw.CharField(unique=True)
    last_uid = pw.CharField(null=True)
    last_sync_at = pw.DateTimeField(null=True)

    @classmethod
    def get_latest_uid(cls, name: str) -> str | None:
        mailbox = cls.get_or_none(cls.name == name)
        return mailbox.last_uid if mailbox else None


class MsgMeta(BaseModel):
    """
    Metadata for messages.
    """

    rawmsg = pw.ForeignKeyField(RawMsg, backref='msgmeta')
    labels = pw.ManyToManyField(Mailbox, backref='messages')
    fetch_time = pw.DateTimeField(default=utcnow)

    from_ = pw.CharField(null=True)
    to = pw.CharField(null=True)
    subject = pw.CharField(null=True)
    date = pw.CharField(null=True)
    has_attachments = pw.BooleanField(null=True)

    def link_label(self, mailbox: Mailbox) -> None:
        through = MsgMeta.labels.get_through_model()
        through.get_or_create(msgmeta=self, mailbox=mailbox)


def schema_tables() -> list[pw.Model]:
    return [
        RawMsg,
        MsgMeta,
        AttachmentMeta,
        Mailbox,
        AttachmentMeta.rawmsg.get_through_model(),
        MsgMeta.labels.get_through_model(),
    ]
