# Mailboxdb

Fetch emails from a mailbox and store them in a db.  
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

# Todo

- use logging for info and debug
- use argparse to route between config, bootstrap, and run stages
- config opt to switch between db backends
- testing
- use classes
