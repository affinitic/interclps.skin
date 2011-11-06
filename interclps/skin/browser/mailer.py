# File: mailer.py
#
# Copyright (c) 2007 by Affinitic
#
# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#

import smtplib
import MimeWriter, mimetools, cStringIO
import logging
logger = logging.getLogger("affinitic")

class Mailer:
    def __init__(self, mailhost ,sender):
        """ sender: sender's email
        """
        self.sender = sender
        self.mailhost = mailhost

    def setSubject(self, subject):
        self.subject = subject

    def getSubject(self):
        return self.subject

    def getRecipients(self):
        return self.recipients

    def setRecipients(self, recipients):
        recipients = recipients.split(',')
        self.recipients = recipients

    def createMail(self, recipient, text):
        """
        """
        txtin = cStringIO.StringIO("")
        htmlin = cStringIO.StringIO(text)
        out = cStringIO.StringIO()

        writer = MimeWriter.MimeWriter(out)
        writer.addheader("From", self.sender)
        writer.addheader("To", recipient)
        writer.addheader("Subject", self.subject)
        writer.addheader("MIME-Version", "1.0")
        writer.startmultipartbody("mixed")
        writer.flushheaders()
        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        pout = subpart.startbody("text/plain", [("charset", 'UTF-8')])
        mimetools.encode(txtin, pout, 'quoted-printable')
        txtin.close()

        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        pout = subpart.startbody("text/html", [("charset", 'UTF-8')])
        mimetools.encode(htmlin, pout, 'quoted-printable')
        htmlin.close()

        writer.lastpart()
        msg = out.getvalue()
        out.close()
        return msg

    def sendAllMail(self, text):
        server = smtplib.SMTP(self.mailhost)
        for recipient in self.getRecipients():
            logging.info("Sending to %s" % recipient)
            message = self.createMail(recipient, text)
            server.sendmail(self.sender, recipient, message)
        server.quit()

