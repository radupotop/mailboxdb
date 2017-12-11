from datetime import datetime
import peewee as pw

db = pw.SqliteDatabase('messages.db')


class BaseModel(pw.Model):
    class Meta:
        database = db


class RawMsg(BaseModel):
    """
    Raw message as fetched from IMAP server.
    """
    checksum = pw.CharField(unique=True, index=True)
    email_blob = pw.BlobField()


class MsgMeta(BaseModel):
    """
    Metadata for messages.
    """
    imap_uid = pw.CharField(index=True)
    checksum = pw.ForeignKeyField(RawMsg, to_field='checksum')
    fetch_time = pw.DateTimeField(default=datetime.utcnow)
    
    from_ = pw.CharField(null=True)
    to = pw.CharField(null=True)
    subject = pw.CharField(null=True)
    date = pw.DateTimeField(null=True)
    has_attachment = pw.BooleanField(null=True)

db.connect()

if __name__ == '__main__':
    db.create_tables([RawMsg, MsgMeta])
