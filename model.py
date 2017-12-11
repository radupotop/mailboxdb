import datetime
import peewee as pw

db = pw.SqliteDatabase('msgs.db')


class MsgMeta(pw.Model):
    date = pw.DateTimeField()
    from = pw.CharField()
    to = pw.CharField()
    subject = pw.CharField()
    has_attachment = pw.BooleanField()
    csum = pw.ForeignKeyField(RawMsg, to_field='csum')

    class Meta:
        database = db


class RawMsg(pw.Model):
    email_blob = pw.BlobField()
    csum = pw.CharField(unique=True, index=True)
    imap_uid = pw.CharField(index=True)
    fetch_time = pw.DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
