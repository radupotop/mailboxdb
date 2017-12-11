import datetime
import peewee as pw

db = pw.SqliteDatabase('msgs.db')


class MsgLog(pw.Model):
    date = pw.DateTimeField()
    from = pw.CharField()
    to = pw.CharField()
    subject = pw.CharField()
    has_attachment = pw.BooleanField()
    fetch_time = pw.DateTimeField(default=datetime.datetime.now)
    imap_uid = pw.CharField(index=True)
    csum = pw.CharField(unique=True, index=True)

    class Meta:
        database = db


class RawMsg(pw.Model):
    csum = pw.ForeignKeyField(MsgLog, to_field='csum')
    email_blob = pw.BlobField()

    class Meta:
        database = db
