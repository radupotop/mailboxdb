# mailboxdb

Fetch emails from mailbox and store them in a db.  
Attachments are extracted and stored as separate files for simplified browsing and space efficiency.


# Installing

    python -m venv env
    source env/bin/activate
    pip install -r requirements.txt


# Credentials file format

    [DEFAULT]
    server = imap.gmail.com
    username = user
    password = pass
