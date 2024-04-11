import argparse

from bootstrap import bootstrap
from config import ConfigReader
from imap import Mbox
from logger import get_logger, quiet_root_logger
from model import db, pw
from process import process_message

log = get_logger('run')


def run(creds_file='credentials.ini'):
    settings = ConfigReader(creds_file)
    db.connect()
    mbox = Mbox(settings)
    message_uids = mbox.get_message_uids()
    all_msg_gen = mbox.fetch_all_messages(message_uids)

    # Accept that the first message might be a duplicate.
    # This is because IMAP fetch will always get the latest message from the mailbox,
    # even if the UID we specify is higher than the latest one.
    try:
        first_msg = next(all_msg_gen)
        process_message(*first_msg)
    except pw.IntegrityError as err:
        if 'UNIQUE constraint failed: rawmsg.checksum' in str(err):
            log.info('Duplicate first message, carry on.')
        else:
            raise err
    except StopIteration:
        log.info('No new messages.')

    for msg in all_msg_gen:
        process_message(*msg)

    mbox.logout()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b',
        '--bootstrap',
        action='store_true',
        help='Initialise the db',
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
    args = parser.parse_args()

    if args.quiet:
        quiet_root_logger()

    if args.run:
        run(args.creds)
    elif args.bootstrap:
        try:
            bootstrap()
        except pw.OperationalError as err:
            if 'already exists' in str(err):
                log.info('The database is already configured.')
            else:
                raise err
    else:
        parser.print_help()
