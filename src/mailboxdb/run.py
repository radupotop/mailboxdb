import argparse
import sys
from pathlib import Path

from mailboxdb.config import ConfigReader
from mailboxdb.helpers import email_from_bytes, sha256sum, utcnow
from mailboxdb.imap import Mbox
from mailboxdb.logger import get_logger, quiet_root_logger
from mailboxdb.migrations import rollback_migrations, run_migrations
from mailboxdb.model import Mailbox, db, pw
from mailboxdb.process import process_message
from mailboxdb.schema import MboxResults

log = get_logger('Run')


def run(creds_file='credentials.ini'):
    settings = ConfigReader(creds_file)
    db.connect()
    mbox = Mbox(settings)
    mailbox_name = getattr(settings, 'mailbox', 'INBOX')
    mailbox_row, _ = Mailbox.get_or_create(name=mailbox_name)
    log.info(
        'Mailbox sync start: mailbox=%s last_uid=%s',
        mailbox_name,
        mailbox_row.last_uid,
    )
    message_uids = mbox.get_message_uids(
        latest_uid=mailbox_row.last_uid,
        label=mailbox_name,
    )
    if not message_uids:
        log.warning('No new message UIDs found for mailbox %s', mailbox_name)
        mbox.logout()
        sys.exit(0)

    all_msg_gen = mbox.fetch_all_messages(message_uids)
    # The first message can be a duplicate.
    # This is because IMAP fetch will always get the latest message from the mailbox,
    # even if the UID we specify is higher than the latest one.
    for msg in all_msg_gen:
        process_message(msg, mailbox_row)

    last_uid = max(map(int, message_uids))
    mailbox_row.last_uid = str(last_uid)
    mailbox_row.last_sync_at = utcnow()
    mailbox_row.save()
    log.info(
        'Mailbox sync complete: mailbox=%s last_uid=%s synced_at=%s',
        mailbox_name,
        mailbox_row.last_uid,
        mailbox_row.last_sync_at,
    )

    mbox.logout()


def run_file(email_folder: str):
    db.connect()
    folder = Path(email_folder)
    if not folder.is_dir():
        raise RuntimeError(f'Email folder not found or not a directory: {folder}')

    mailbox_name = f'FILE:{folder}'
    mailbox_row, _ = Mailbox.get_or_create(name=mailbox_name)
    log.info('File ingest start: folder=%s', folder)

    all_msg_paths: list[Path] = sorted(folder.glob('*.eml'))
    if not len(all_msg_paths):
        log.warning('No .eml files found in folder %s', folder)
        sys.exit(0)

    for path in all_msg_paths:
        raw_email = path.read_bytes()
        checksum = sha256sum(raw_email)
        email_msg = email_from_bytes(raw_email)
        process_message(
            MboxResults(email_msg, checksum, path.name.encode()),
            mailbox_row,
        )

    mailbox_row.last_uid = all_msg_paths[-1].name
    mailbox_row.last_sync_at = utcnow()
    mailbox_row.save()

    log.info(
        'File ingest complete: folder=%s last_uid=%s synced_at=%s',
        folder,
        mailbox_row.last_uid,
        mailbox_row.last_sync_at,
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m',
        '--migrate',
        action='store_true',
        help='Apply database migrations',
    )
    parser.add_argument(
        '-R',
        '--rollback',
        nargs='?',
        const=1,
        type=int,
        help='Rollback the last N migrations (default: 1)',
    )
    parser.add_argument(
        '-r',
        '--run',
        action='store_true',
        help='Fetch outstanding emails',
    )
    parser.add_argument(
        '-c',
        '--creds',
        type=str,
        default='credentials.ini',
        help='Credentials INI file to use',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='Do not output info messages',
    )
    args = parser.parse_args(argv)

    if args.quiet:
        quiet_root_logger()

    did_action = False

    if args.rollback:
        try:
            rollback_migrations(args.rollback)
        except pw.OperationalError as err:
            if 'no such table' in str(err).lower():
                log.info('No migrations have been applied yet.')
            else:
                raise err
        did_action = True

    if args.migrate:
        try:
            run_migrations()
        except pw.OperationalError as err:
            if 'already exists' in str(err):
                log.info('The database is already configured.')
            else:
                raise err
        did_action = True

    if args.run:
        run(args.creds)
        did_action = True

    if not did_action:
        parser.print_help()


def main_file(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'email_folder',
        type=str,
        help='Folder containing .eml files',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='Do not output info messages',
    )
    args = parser.parse_args(argv)

    if args.quiet:
        quiet_root_logger()

    run_file(args.email_folder)


if __name__ == '__main__':
    main()
