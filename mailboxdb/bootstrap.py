from mailboxdb.model import AttachmentMeta, MsgMeta, RawMsg, db


def bootstrap():
    db.connect()
    db.create_tables(
        [
            RawMsg,
            MsgMeta,
            AttachmentMeta,
            AttachmentMeta.rawmsg.get_through_model(),
        ]
    )
