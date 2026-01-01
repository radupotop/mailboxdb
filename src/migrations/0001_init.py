import peewee as pw
from playhouse.migrate import SqliteMigrator

from mailboxdb.model import schema_tables


def migrate(db: pw.Database, migrator: SqliteMigrator):
    db.create_tables(schema_tables(), safe=True)


def rollback(db: pw.Database, migrator: SqliteMigrator):
    return None
