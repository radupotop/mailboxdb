# Mailboxdb

Fetch emails from a mailbox and store them in a db.
Attachments are extracted and stored as separate files for simplified browsing and space efficiency.

See [DEVELOPMENT.md](DEVELOPMENT.md) for local development notes.

## Installing

    python -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    pip install -e .


## Credentials file format

    [DEFAULT]
    server = imap.gmail.com
    username = user
    password = pass
    # Optional: fetch from a specific mailbox (defaults to INBOX).
    # mailbox = "[Gmail]/All Mail"
    # Optional: use XOAUTH2 with a command that returns the access token.
    # use_xoauth2 = True
    # password_command = ("/usr/bin/oama", "access", "username@example.com")

## Migrations

Use the migration runner to create or update the schema:

    mailboxdb --migrate

Migrations live in `src/migrations/` and are applied in filename order (use 4-digit prefixes like `0001_`).
Applied migrations are tracked by SHA-256 checksum so renames don’t require DB changes.
If a migration file changes after being applied, it will be treated as a new migration.

Rollback the last migration (or N migrations):

    mailboxdb --rollback
    mailboxdb --rollback 2

Each migration can define an optional `rollback(db, migrator)` function.

## Todo

- use logging for info and debug
- use argparse to route between config, migrate, and run stages
- config opt to switch between db backends
- testing
- use classes


## Debugging

    docker-compose exec mail bash
    cd /srv/mail/testuser/Mail/mailboxes/INBOX/dbox-Mails
