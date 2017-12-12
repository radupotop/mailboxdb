import email
import hashlib
import imaplib
from configparser import ConfigParser

from model import RawMsg, MsgMeta


OK_STATUS = 'OK'

config = ConfigParser()
config.read('credentials.ini')
settings = config.defaults()

mbox = imaplib.IMAP4_SSL(settings['server'])
mbox.login(settings['username'], settings['password'])
mbox.list()

mbox.select('INBOX', readonly=True)

box_status, box_data = mbox.uid('search', None, 'ALL')
# box_status, box_data = mbox.uid('search', None, 'UID', start_message_uid + ':*')

if box_status == OK_STATUS:
    message_uids = box_data[0].split()

    for m_uid in message_uids:
        msg_status, msg_data = mbox.uid('fetch', m_uid, '(RFC822)')

        if msg_status == OK_STATUS:
            raw_email = msg_data[0][1]
            checksum = hashlib.sha256(raw_email).hexdigest()

            email_msg = email.message_from_bytes(raw_email)
            from_ = email_msg.get('From')
            to = email_msg.get('To')
            subject = email_msg.get('Subject')
            date = email_msg.get('Date')

            rmsg = RawMsg.create(email_blob=raw_email, checksum=checksum)

            mmeta = MsgMeta.create(
                        imap_uid=m_uid,
                        checksum=checksum,
                        from_=from_,
                        to=to,
                        subject=subject,
                        date=date,
                    )

            print(m_uid, from_, to, subject)

mbox.logout()
