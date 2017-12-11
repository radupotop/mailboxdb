import email
import hashlib
import imaplib
import yaml

from model import RawMsg, MsgMeta


OK_STATUS = 'OK'

settings_yaml = open('credentials.yaml').read()
settings = yaml.load(settings_yaml)


mbox = imaplib.IMAP4_SSL(settings['server'])
mbox.login(settings['username'], settings['password'])
mbox.list()

mbox.select('INBOX', readonly=True)

box_status, box_data = mbox.uid('search', None, 'ALL')

if box_status == OK_STATUS:
    message_uids = box_data[0].split()

    for message in message_uids:
        msg_status, msg_data = mbox.uid('fetch', message, '(RFC822)')

        if msg_status == OK_STATUS:
            raw_email = msg_data[0][1]
            csum = hashlib.sha256(raw_email).hexdigest()

            email_msg = email.message_from_bytes(raw_email)

            rmsg = RawMsg.create(email_blob=raw_email, csum=csum, imap_uid=None)

            mmeta = MsgMeta.create(
                        date=email_msg.get('Date'), 
                        from_=email_msg.get('From'), 
                        to=email_msg.get('To'),
                        subject=email_msg.get('Subject'),
                        csum=csum
                    )
