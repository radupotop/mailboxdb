import datetime
import peewee as pw

db = pw.SqliteDatabase('messages.db')


class BaseModel(pw.Model):
    class Meta:
        database = db


class RawMsg(BaseModel):
    email_blob = pw.BlobField()
    csum = pw.CharField(unique=True, index=True)
    imap_uid = pw.CharField(index=True)
    fetch_time = pw.DateTimeField(default=datetime.datetime.now)


class MsgMeta(BaseModel):
    date = pw.DateTimeField()
    from_ = pw.CharField(db_column='from')
    to = pw.CharField()
    subject = pw.CharField()
    has_attachment = pw.BooleanField(default=False)
    csum = pw.ForeignKeyField(RawMsg, to_field='csum')


db.connect()
db.create_tables([RawMsg, MsgMeta])
