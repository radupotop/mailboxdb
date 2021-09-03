import argparse
import email
import hashlib
import logging
from configparser import ConfigParser
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL
from pathlib import Path

from bootstrap import bootstrap
from imap import connect_mbox, fetch_all_messages, get_message_uids
from model import db, pw
from process import process_message

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def run():
    db.connect()
    mbox = connect_mbox()
    message_uids = get_message_uids(mbox)
    all_msg_gen = fetch_all_messages(mbox, message_uids)

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
    parser.add_argument('-c', '--config', action='store_true', help='Configure the db')
    parser.add_argument('-r', '--run', action='store_true', help='Run main loop')
    parser.add_argument(
        '-q', '--quiet', action='store_true', help='Do not output anything'
    )
    parser.add_argument('--debug', action='store_true', help='Output debug messages')
    args = parser.parse_args()

    if args.run:
        run()
    elif args.config:
        try:
            bootstrap()
        except pw.OperationalError as err:
            if 'already exists' in str(err):
                print('The database is already configured.')
            else:
                raise err
    else:
        parser.print_help()
