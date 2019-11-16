from datetime import datetime
import peewee as pw

db = pw.SqliteDatabase('messages.db')

# db = pw.PostgresqlDatabase(
#     'mailboxdb',
#     user='postgres',
#     password='',
#     host='localhost',
# )

class BaseModel(pw.Model):
    class Meta:
        database = db


class RawMsg(BaseModel):
    """
    Raw message as fetched from IMAP server.
    """
    checksum = pw.CharField(unique=True, index=True, help_text='Checksum of the original message on the server')
    email_blob = pw.BlobField(help_text='Email blob with attachments removed')


class Attachment(BaseModel):
    rawmsg = pw.ManyToManyField(RawMsg, backref='attachments')
    file_checksum = pw.CharField(index=True, help_text='Checksum of the binary file on disk')
    filename = pw.CharField(null=True, help_text='Original filename')
    content_type = pw.CharField(null=True, help_text='Original content type')


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
        return cls.select(pw.fn.MAX(cls.imap_uid)).scalar()
