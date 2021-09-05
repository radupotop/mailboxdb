from model import Attachment, MsgMeta, RawMsg, db


def bootstrap():
    db.connect()
    db.create_tables([RawMsg, MsgMeta, Attachment, Attachment.rawmsg.get_through_model()])
