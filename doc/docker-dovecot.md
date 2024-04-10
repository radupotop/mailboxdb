# Instructions

This image comes with default configuration which accepts any user with password `pass`.
To customize the image, mount `/etc/dovecot` and `/srv/mail` volumes.
Since 2.3.20, you can also mount `/etc/dovecot/conf.d` for overrides and new configuration,
make sure the files end up with `.conf`.

## Listeners

 - POP3 on 110, TLS 995
 - IMAP on 143, TLS 993
 - Submission on 587
 - LMTP on 24
 - ManageSieve on 4190

## Support

Note that these images are not intended for production use and come with absolutely no warranty or support.
For questions and feedback send email to dovecot@dovecot.org.
