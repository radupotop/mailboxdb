from datetime import datetime
import peewee as pw

db = pw.SqliteDatabase('messages.db')


class BaseModel(pw.Model):
    class Meta:
        database = db


class RawMsg(BaseModel):
    email_blob = pw.BlobField()
    csum = pw.CharField(unique=True, index=True)
    imap_uid = pw.CharField(index=True, null=True)
    fetch_time = pw.DateTimeField(default=datetime.utcnow)


class MsgMeta(BaseModel):
    """
    Metadata for messages, 
    these can be filled-in after the initial download of raw messages.
    """
    date = pw.DateTimeField(null=True)
    from_ = pw.CharField(null=True)
    to = pw.CharField(null=True)
    subject = pw.CharField(null=True)
    has_attachment = pw.BooleanField(null=True)
    csum = pw.ForeignKeyField(RawMsg, to_field='csum')

db.connect()

if __name__ == '__main__':
    db.create_tables([RawMsg, MsgMeta])
