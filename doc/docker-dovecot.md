# Instructions

This image comes with default configuration which accepts any user with password `pass`.
To customize the image, mount `/etc/dovecot` and `/srv/mail` volumes.

## Listeners

 - POP3 on 110, SSL 995
 - IMAP on 143, SSL 993
 - Submission on 587
 - LMTP on 24
 - ManageSieve on 4190

## Support

Note that these images are not intended for production use and come with absolutely no warranty or support.
For questions and feedback send email to dovecot@dovecot.org.
