# Mailboxdb

Fetch emails from a mailbox and store them in a db.  
Attachments are extracted and stored as separate files for simplified browsing and space efficiency.

## Code layout

Mailboxdb is a small Python utility that connects to an IMAP server, fetches messages, stores the raw email content in a
SQLite database, and extracts attachments to disk with metadata in the DB.

- Core flow lives in mailboxdb/run.py: it loads credentials, connects to IMAP, finds new UIDs after the latest stored
  message, fetches RFC822 messages, and hands each message to the processor.
- IMAP handling is in mailboxdb/imap.py: Mbox logs in via IMAP4_SSL, gets message UIDs (either all or from the latest UID),
  fetches each message, and yields parsed email objects plus a SHA-256 checksum.
- Processing is in mailboxdb/process.py: it deduplicates messages by checksum, extracts attachments (writes them to
  attachments/ by checksum), strips attachment payloads from the email, and stores:
    - raw message bytes in RawMsg
    - per-message metadata in MsgMeta (from/to/subject/date/uid/has_attachments)
    - attachment metadata in AttachmentMeta with a many-to-many link to the raw message
- The DB schema is defined in mailboxdb/model.py and uses Peewee with SQLite at database/messages.db. mailboxdb/bootstrap.py
  creates the tables.
- Logging is basic and configured in mailboxdb/logger.py.
- Test helpers in tests/ generate/upload sample emails; doc/docker-dovecot.md and docker-compose.yml support a local Dovecot
  IMAP instance for testing.

## Testing 

There’s no automated test suite. Testing is done via helper scripts and a Dockerized IMAP server to seed a mailbox with sample emails.

- tests/composeemail.py builds random multipart emails using tests/fixtures/lorem_ipsum.txt and random attachments from tests/fixtures/attachments/.
- tests/uploadtestemail.py connects to an IMAP server and appends those generated emails to a mailbox (defaults: localhost, testuser/pass, INBOX).
- docker-compose.yml spins up a Dovecot IMAP server and a test_fixtures container that runs tests/uploadtestemail.py (see docker/Dockerfile.test_fixtures).

Typical manual flow:

1. docker-compose up --build (starts IMAP and uploads test emails).
2. Run the app (e.g., python mailboxdb/run.py -b then python mailboxdb/run.py -r) to fetch and store those emails.


## Installing

    python -m venv env
    source env/bin/activate
    pip install -r requirements.txt


## Credentials file format

    [DEFAULT]
    server = imap.gmail.com
    username = user
    password = pass

## Todo

- use logging for info and debug
- use argparse to route between config, bootstrap, and run stages
- config opt to switch between db backends
- testing
- use classes


## Debugging

    docker-compose exec mail bash
    cd /srv/mail/testuser/Mail/mailboxes/INBOX/dbox-Mails
