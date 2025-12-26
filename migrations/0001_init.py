from mailboxdb.model import AttachmentMeta, MsgMeta, RawMsg, db


def migrate(db, migrator):
    db.create_tables(
        [
            RawMsg,
            MsgMeta,
            AttachmentMeta,
            AttachmentMeta.rawmsg.get_through_model(),
        ],
        safe=True,
    )


def rollback(db, migrator):
    return None
