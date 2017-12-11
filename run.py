import email
import hashlib
import imaplib
import yaml


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

    msg_status, msg_data = mbox.uid('fetch', message, '(RFC822)')

    if msg_status == OK_STATUS:
        """
        raw_msg schema:
        csum (uniq FK) | raw_email (data sqlite)

        msg schema:
        csum (uniq) | date | from | to | subject | has_attachment | fetch_date | imap_uid 
        """
        raw_email = msg_data[0][1]

        email_msg = emai.message_from_bytes(raw_email)
        email_msg.get('From')
        email_msg.get('Date')
        email_msg.get('Subject')

        csum = hashlib.sha1(raw_email).hexdigest()
