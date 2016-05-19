#! /usr/bin/env python

import sys
from email.Message import Message
from email.MIMEMultipart import MIMEMultipart
from email.MIMENonMultipart import MIMENonMultipart
from cStringIO import StringIO
from email.Utils import formataddr
from email.MIMEText import MIMEText
from email.Generator import Generator
from smtplib import SMTP, SMTP_PORT
from mimetypes import guess_type
import base64
import os
from html2text import html2text
import ConfigParser

class InvalidRecipientType(ValueError):
    def __init__(self, supplied_val, *args, **kwds):
        ValueError.__init__(self, *args, **kwds)
        self.supplied_val = supplied_val

    def __str__(self):
        return 'Invalid recipient type; expected either of %r; got %r' % (
            VALID_RECIPENT_TYPES, self.supplied_val
            )

class _TextNoAttachments(object):
    def __init__(self):
        self.sender_name = None
        self.sender_email = None
        self.subject = None
        self.text = None
        self.to_recipients = []
        self.cc_recipients = []
        self.bcc_recipients = []

    def add_recipient(self, email, name=None, type='To'):
        type = type.title()
        if type not in VALID_RECIPENT_TYPES:
            raise InvalidRecipientType(type)
        lists = {
            'To': self.to_recipients,
            'Cc': self.cc_recipients,
            'Bcc': self.bcc_recipients,
            }
        lists[type].append((name, email))

    def __str__(self):
        msg = MIMENonMultipart('text', 'plain', charset='us-ascii')
        _add_common_headers(msg, self.sender_name, self.sender_email,
                            self.to_recipients, self.cc_recipients,
                            self.bcc_recipients, self.subject)
        
        msg.set_payload(self.text)
        
        return _flatten(msg)

class _HTMLNoAttachments(_TextNoAttachments):
    def __init__(self):
        _TextNoAttachments.__init__(self)
        self._html = None

    def __str__(self):
        msg = MIMEMultipart('alternative')
        _add_common_headers(msg, self.sender_name, self.sender_email,
                            self.to_recipients, self.cc_recipients,
                            self.bcc_recipients, self.subject)
        msg.attach(MIMEText(self.text))
        msg.attach(MIMEText(self._html, 'html'))
        return _flatten(msg)

    def sethtml(self, value):

        self._html = value
        self.text = html2text(value)
        
    html = property(lambda self: self._html, sethtml)
    del sethtml

class _TextWithAttachments(_TextNoAttachments):
    def __init__(self):
        _TextNoAttachments.__init__(self)
        self._attachments = []

    def add_attachment(self, pth):
        basename = os.path.basename(pth)
        content_type, _ = guess_type(pth)
        if content_type is None: content_type = 'application/octet-stream'
        b = StringIO()
        f = open(pth, 'rb')
        base64.encode(f, b)
        f.close()
        attachment = Message()
        attachment.add_header('Content-type', content_type,
                              name=basename)
        attachment.add_header('Content-transfer-encoding', 'base64')
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=basename)
        attachment.set_payload(b.getvalue())
        b.close()
        self._attachments.append(attachment)

    def __str__(self):
        msg = MIMEMultipart()
        _add_common_headers(msg, self.sender_name, self.sender_email,
                            self.to_recipients, self.cc_recipients,
                            self.bcc_recipients, self.subject)
        msg.preamble = 'This is a multi-part message in MIME format.\n'
        msg.epilogue = ''
        
        msg.attach(MIMEText(self.text))
        
        for attachment in self._attachments:
            msg.attach(attachment)

        return _flatten(msg)

class _HTMLWithAttachments(_TextWithAttachments, _HTMLNoAttachments):
    
    def __init__(self):
        _TextWithAttachments.__init__(self)
        _HTMLNoAttachments.__init__(self)
    
    def __str__(self):
        msg = MIMEMultipart()
        _add_common_headers(msg, self.sender_name, self.sender_email,
                            self.to_recipients, self.cc_recipients,
                            self.bcc_recipients, self.subject)
        msg.preamble = 'This is a multi-part message in MIME format.\n'
        msg.epilogue = ''

        body = MIMEMultipart('alternative')        
        body.attach(MIMEText(self.text))
        body.attach(MIMEText(self._html, 'html'))
        msg.attach(body)
        
        for attachment in self._attachments:
            msg.attach(attachment)

        return _flatten(msg)

_CONSTRUCTORS = {
    (False, False): _TextNoAttachments,
    (True, False): _HTMLNoAttachments,
    (False, True): _TextWithAttachments,
    (True, True): _HTMLWithAttachments,
    }

class MyMessage(_HTMLWithAttachments):
    def __str__(self):
        key = (bool(self._html), bool(self._attachments))
        constructor = _CONSTRUCTORS[key]()
        constructor.sender_name = self.sender_name 
        constructor.sender_email = self.sender_email 
        constructor.subject = self.subject 
        constructor.text = self.text 
        constructor.to_recipients = self.to_recipients 
        constructor.cc_recipients = self.cc_recipients 
        constructor.bcc_recipients = self.bcc_recipients

        if self._attachments: constructor._attachments = self._attachments
        if self._html: constructor._html = self._html
        
        return str(constructor)

def _format_addresses(addresses):
    return ', '.join(map(formataddr, addresses))

def _flatten(msg):
    b = StringIO()

    return b.getvalue()

class _NullWriter(object):
    def write(self, *args, **kwds): pass
    def writelines(self, *args, **kwds): pass

class MySMTP(SMTP):

    def __init__(self, log=_NullWriter()):
        SMTP.__init__(self)
        
        self.set_debuglevel(0)
        self.log = log

    def connect(self, host='smtp.office365.com', port=SMTP_PORT):
        remember = sys.stdout
        sys.stdout = self.log
        try:
            SMTP.connect(self, host, port)
        finally:
            sys.stdout = remember

    def quit(self):
        remember = sys.stdout
        sys.stdout = self.log
        try:
            SMTP.quit(self)
        finally:
            sys.stdout = remember

    def send_message(self, msg):
        from_addr =  formataddr((msg.sender_name, msg.sender_email))
        recipients = []
        recipients.extend(map(formataddr, msg.to_recipients))
        recipients.extend(map(formataddr, msg.cc_recipients))
        recipients.extend(map(formataddr, msg.bcc_recipients))
        
        remember = sys.stdout
        sys.stdout = self.log
        try:
            return self.sendmail(from_addr, recipients, str(msg))
        finally:
            sys.stdout = remember

class SMTPConn(MySMTP ):

    def __init__(self, smtpserver, *args, **kwds):
        MySMTP.__init__(self, *args, **kwds)
        self.smtpserver = smtpserver

    def connect(self, host=None, port=SMTP_PORT):
        if host is None: host = self.smtpserver
        MySMTP.connect(self, host, port)

    def __repr__(self):
        return '<%s.%s instance for %r>' % (
            self.__module__, self.__class__.__name__, self.smtpserver
            )

def test_mailer():
    myMsg=_HTMLWithAttachments()
    myMsg.add_recipient(to_address, None, 'To')
    myMsg.add_recipient(cc_address, None, 'Cc')
    myMsg.sender_name='Monitoring System Notification'
    myMsg.sender_email=from_address
    myMsg.subject=subject
    myMsg.add_attachment(attachment)
    myMsg.html=file(message_body).read()
    try:
        host=SMTPConn(mailserver, port)
        #host.set_debuglevel(1)
        host.connect(mailserver, port)
        host.ehlo()
        if host.has_extn('STARTTLS'):
            host.starttls()
        host.login(from_address, password)
        host.send_message(myMsg)
        #os.remove(tempfile)
    
    except Exception, oO:
        print oO
    
    finally:
        host.quit()
   

if __name__ == '__main__':

    test_mailer()    