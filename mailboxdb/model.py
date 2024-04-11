from datetime import datetime

import peewee as pw

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


class MsgMeta(BaseModel):
    """
    Metadata for messages.
    """

    rawmsg = pw.ForeignKeyField(RawMsg, backref='msgmeta')
    imap_uid = pw.CharField(index=True)
    fetch_time = pw.DateTimeField(default=datetime.utcnow)

    from_ = pw.CharField(null=True)
    to = pw.CharField(null=True)
    subject = pw.CharField(null=True)
    date = pw.CharField(null=True)
    has_attachments = pw.BooleanField(null=True)

    @classmethod
    def get_latest_uid(cls):
        return cls.select(cls.imap_uid, pw.fn.MAX(cls.id)).scalar()
