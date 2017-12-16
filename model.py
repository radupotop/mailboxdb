from datetime import datetime
import peewee as pw

db = pw.SqliteDatabase('messages.db')

# db = pw.PostgresqlDatabase(
#     'gmaildb',
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
    checksum = pw.CharField(unique=True, index=True, help="Checksum of the original message on the server")
    email_blob = pw.BlobField()


class Attachment(BaseModel):
    file_checksum = pw.CharField(index=True, help="Checksum of the binary file")
    rawmsg_checksum = pw.ForeignKeyField(RawMsg, to_field='checksum', related_name='attachments')
    filename = pw.CharField(null=True)
    content_type = pw.CharField(null=True)


class MsgMeta(BaseModel):
    """
    Metadata for messages.
    """
    imap_uid = pw.CharField(index=True)
    checksum = pw.ForeignKeyField(RawMsg, to_field='checksum', related_name='msgmeta')
    fetch_time = pw.DateTimeField(default=datetime.utcnow)
    
    from_ = pw.CharField(null=True)
    to = pw.CharField(null=True)
    subject = pw.CharField(null=True)
    date = pw.CharField(null=True)
    has_attachment = pw.BooleanField(null=True)

db.connect()

if __name__ == '__main__':
    db.create_tables([RawMsg, MsgMeta])
