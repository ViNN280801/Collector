from __future__ import annotations


class EmailException(Exception):
    pass


class SMTPConnectionError(EmailException):
    pass


class SMTPAuthenticationError(EmailException):
    pass


class SMTPMailboxFullError(EmailException):
    pass


class SMTPMessageSizeError(EmailException):
    pass


class SMTPRecipientRefusedError(EmailException):
    pass


class SMTPSenderRefusedError(EmailException):
    pass


class SMTPDataError(EmailException):
    pass


class EmailConfigurationError(EmailException):
    pass


class AttachmentError(EmailException):
    pass
