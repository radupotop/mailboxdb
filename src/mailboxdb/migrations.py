from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import NamedTuple

import peewee as pw
from playhouse.migrate import SqliteMigrator

from mailboxdb.date_helper import utcnow
from mailboxdb.logger import get_logger
from mailboxdb.model import db

log = get_logger('Migrations')


class SchemaMigration(pw.Model):
    name = pw.CharField(unique=True)
    checksum = pw.CharField(unique=True)
    applied_at = pw.DateTimeField(default=utcnow)

    class Meta:
        database = db
        table_name = 'schema_migrations'


def _default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / 'migrations'


class MigrationFile(NamedTuple):
    path: Path
    checksum: str

    @staticmethod
    def compute_checksum(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @classmethod
    def from_path(cls, path: Path) -> 'MigrationFile':
        return cls(path=path, checksum=cls.compute_checksum(path))

    @property
    def name(self) -> str:
        return self.path.name


def _list_migration_files(root: Path) -> list[MigrationFile]:
    paths = sorted(p for p in root.iterdir() if p.suffix == '.py')
    migrations = [MigrationFile.from_path(p) for p in paths]

    seen: dict[str, str] = {}
    for migration in migrations:
        if migration.checksum in seen:
            raise RuntimeError(
                'Duplicate migration checksum for '
                f'{migration.name} and {seen[migration.checksum]}'
            )
        seen[migration.checksum] = migration.name

    return migrations


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

    migration_files = _list_migration_files(root)
    applied_rows = list(SchemaMigration.select())
    applied_checksums = {row.checksum for row in applied_rows if row.checksum}

    pending = [m for m in migration_files if m.checksum not in applied_checksums]

    if not pending:
        log.info('No pending migrations.')
        return []

    migrator = SqliteMigrator(db)
    applied_now: list[str] = []

    for migration in pending:
        module = _load_migration(migration.path)
        log.info('Applying migration: %s', migration.name)
        with db.atomic():
            module.migrate(db, migrator)
            SchemaMigration.create(name=migration.name, checksum=migration.checksum)
        applied_now.append(migration.name)

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

    migration_files = _list_migration_files(root)
    files_by_checksum = {m.checksum: m.path for m in migration_files}

    all_rows = list(SchemaMigration.select())
    rows = list(SchemaMigration.select().order_by(SchemaMigration.id.desc()).limit(steps))
    if not rows:
        log.info('No migrations to rollback.')
        return []

    migrator = SqliteMigrator(db)
    rolled_back: list[str] = []

    for row in rows:
        if not row.checksum:
            raise RuntimeError(f'Migration {row.name} has no checksum')
        path = files_by_checksum.get(row.checksum)
        if path is None:
            raise RuntimeError(
                f'Migration file not found for checksum {row.checksum}: {row.name}'
            )
        module = _load_migration(path)
        if not hasattr(module, 'rollback'):
            raise RuntimeError(f'Migration {path.name} has no rollback(db, migrator)')
        log.info('Rolling back migration: %s', path.name)
        with db.atomic():
            module.rollback(db, migrator)
            row.delete_instance()
        rolled_back.append(path.name)

    return rolled_back
