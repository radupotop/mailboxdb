from mailboxdb.model import schema_tables


def migrate(db, migrator):
    db.create_tables(schema_tables(), safe=True)


def rollback(db, migrator):
    return None
