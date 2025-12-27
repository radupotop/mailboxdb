## Code layout

Mailboxdb is a small Python utility that connects to an IMAP server, fetches messages, stores the raw email content in a
SQLite database, and extracts attachments to disk with metadata in the DB.

- Core flow lives in mailboxdb/run.py: it loads credentials, connects to IMAP, finds new UIDs after the latest stored
  mailbox UID, fetches RFC822 messages, and hands each message to the processor.
- IMAP handling is in mailboxdb/imap.py: Mbox logs in via IMAP4_SSL, gets message UIDs (either all or from the latest UID),
  fetches each message, and yields parsed email objects plus a SHA-256 checksum.
- Processing is in mailboxdb/process.py: it deduplicates messages by checksum, extracts attachments (writes them to
  attachments/ by checksum), strips attachment payloads from the email, and stores:
    - raw message bytes in RawMsg
    - per-message metadata in MsgMeta (from/to/subject/date/num_attachments)
    - attachment metadata in AttachmentMeta with a many-to-many link to the raw message
- The DB schema is defined in mailboxdb/model.py and uses Peewee with SQLite at database/messages.db. Migrations live in
  migrations/ and are applied via mailboxdb/run.py --migrate.
- Logging is basic and configured in mailboxdb/logger.py.
- Test helpers in tests/ generate/upload sample emails; doc/docker-dovecot.md and docker-compose.yml support a local Dovecot
  IMAP instance for testing.

## DB schema

- RawMsg stores the normalized email body (attachments stripped) and a unique original_checksum of the raw message; one row
  per fetched message body. mailboxdb/model.py.
- Mailbox stores sync state (name, last_uid, last_sync_at). mailboxdb/model.py.
- MsgMeta stores per-message metadata (fetch_time, from_, to, subject, date, num_attachments, message_id, in_reply_to) and links back to
  RawMsg via a FK; labels are linked via a many-to-many relation. mailboxdb/model.py.
- AttachmentMeta stores attachment metadata (file_checksum, original_filename, content_type) and links to RawMsg via a
  many‑to‑many join table that Peewee creates implicitly; this models “many attachments per message” and allows reuse if the
  same attachment appears across messages. mailboxdb/model.py.
- SchemaMigration tracks applied migrations with name, checksum, and applied_at; used by the migration runner. mailboxdb/
  migrations.py.


## Testing

There’s no automated test suite. Testing is done via helper scripts and a Dockerized IMAP server to seed a mailbox with sample emails.

- tests/composeemail.py builds random multipart emails using tests/fixtures/lorem_ipsum.txt and random attachments from tests/fixtures/attachments/.
- tests/uploadtestemail.py connects to an IMAP server and appends those generated emails to a mailbox (defaults: localhost, testuser/pass, INBOX).
- docker-compose.yml spins up a Dovecot IMAP server and a test_fixtures container that runs tests/uploadtestemail.py (see docker/Dockerfile.test_fixtures).

Typical manual flow:

1. docker-compose up --build (starts IMAP and uploads test emails).
2. Run the app (e.g., python mailboxdb/run.py --migrate then python mailboxdb/run.py -r) to fetch and store those emails.
