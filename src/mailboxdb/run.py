import argparse
import sys

from mailboxdb.config import ConfigReader
from mailboxdb.date_helper import utcnow
from mailboxdb.imap import Mbox
from mailboxdb.logger import get_logger, quiet_root_logger
from mailboxdb.migrations import rollback_migrations, run_migrations
from mailboxdb.model import Mailbox, db, pw
from mailboxdb.process import process_message

log = get_logger('Run')


def run(creds_file='credentials.ini'):
    settings = ConfigReader(creds_file)
    db.connect()
    mbox = Mbox(settings)
    mailbox = getattr(settings, 'mailbox', 'INBOX')
    mailbox_name = str(mailbox).strip() or 'INBOX'
    mailbox_row, _ = Mailbox.get_or_create(name=mailbox_name)
    log.info(
        'Mailbox sync start: mailbox=%s last_uid=%s', mailbox_name, mailbox_row.last_uid
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

    last_uid = max(int(uid) for uid in message_uids)
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


if __name__ == '__main__':
    main()
