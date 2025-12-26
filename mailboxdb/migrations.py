from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import peewee as pw
from playhouse.migrate import SqliteMigrator

from mailboxdb.logger import get_logger
from mailboxdb.model import db

log = get_logger('Migrations')


class SchemaMigration(pw.Model):
    name = pw.CharField(unique=True)
    applied_at = pw.DateTimeField(default=datetime.utcnow)

    class Meta:
        database = db
        table_name = 'schema_migrations'


def _default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[1] / 'migrations'


def _load_migration(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Failed to load migration {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'migrate'):
        raise RuntimeError(f'Migration {path.name} has no migrate(db, migrator)')
    return module


def run_migrations(migrations_dir: Path | str | None = None) -> list[str]:
    if db.is_closed():
        db.connect()

    db.create_tables([SchemaMigration], safe=True)

    root = Path(migrations_dir) if migrations_dir else _default_migrations_dir()
    if not root.is_dir():
        raise RuntimeError(f'Migrations directory not found: {root}')

    applied = {row.name for row in SchemaMigration.select()}
    paths = sorted(p for p in root.iterdir() if p.suffix == '.py')
    pending = [p for p in paths if p.name not in applied]

    if not pending:
        log.info('No pending migrations.')
        return []

    migrator = SqliteMigrator(db)
    applied_now: list[str] = []

    for path in pending:
        module = _load_migration(path)
        log.info('Applying migration: %s', path.name)
        with db.atomic():
            module.migrate(db, migrator)
            SchemaMigration.create(name=path.name)
        applied_now.append(path.name)

    return applied_now


def rollback_migrations(
    steps: int = 1,
    migrations_dir: Path | str | None = None,
) -> list[str]:
    if steps < 1:
        return []

    if db.is_closed():
        db.connect()

    db.create_tables([SchemaMigration], safe=True)

    root = Path(migrations_dir) if migrations_dir else _default_migrations_dir()
    if not root.is_dir():
        raise RuntimeError(f'Migrations directory not found: {root}')

    rows = list(SchemaMigration.select().order_by(SchemaMigration.id.desc()).limit(steps))
    if not rows:
        log.info('No migrations to rollback.')
        return []

    migrator = SqliteMigrator(db)
    rolled_back: list[str] = []

    for row in rows:
        path = root / row.name
        if not path.is_file():
            raise RuntimeError(f'Migration file not found: {path}')
        module = _load_migration(path)
        if not hasattr(module, 'rollback'):
            raise RuntimeError(f'Migration {path.name} has no rollback(db, migrator)')
        log.info('Rolling back migration: %s', path.name)
        with db.atomic():
            module.rollback(db, migrator)
            row.delete_instance()
        rolled_back.append(path.name)

    return rolled_back
