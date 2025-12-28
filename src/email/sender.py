from __future__ import annotations

import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.exception_wrapper import exception_wrapper
from .exceptions import (
    AttachmentError,
    EmailConfigurationError,
    SMTPAuthenticationError,
    SMTPConnectionError,
    SMTPDataError,
    SMTPMailboxFullError,
    SMTPMessageSizeError,
    SMTPRecipientRefusedError,
    SMTPSenderRefusedError,
)


class EmailSender:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.smtp_host: str = config.get("smtp_host", "localhost")
        self.smtp_port: int = config.get("smtp_port", 587)
        self.username: str = config.get("username", "")
        self.password: str = config.get("password", "")
        self.from_email: str = config.get("from_email", "")
        self.to_email: str = config.get("to_email", "")
        self.use_tls: bool = config.get("use_tls", True)
        self.use_ssl: bool = config.get("use_ssl", False)
        self.timeout: int = config.get("timeout", 30)
        self.max_attachment_size_mb: int = config.get("max_attachment_size_mb", 25)

        self._validate_config()

    def _validate_config(self) -> None:
        if not self.smtp_host:
            raise EmailConfigurationError("SMTP host is required")

        if not self.from_email:
            raise EmailConfigurationError("From email is required")

        if not self.to_email:
            raise EmailConfigurationError("To email is required")

        if self.smtp_port < 1 or self.smtp_port > 65535:
            raise EmailConfigurationError(f"Invalid SMTP port: {self.smtp_port}")

        if self.use_tls and self.use_ssl:
            raise EmailConfigurationError("Cannot use both TLS and SSL simultaneously")

    def _create_server(self) -> smtplib.SMTP:
        from typing import Union

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server: Union[smtplib.SMTP, smtplib.SMTP_SSL] = smtplib.SMTP_SSL(
                    self.smtp_host, self.smtp_port, timeout=self.timeout, context=context
                )
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout)

                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)

            return server

        except smtplib.SMTPConnectError as e:
            raise SMTPConnectionError(
                f"Failed to connect to SMTP server {self.smtp_host}:{self.smtp_port}. " f"Error: {e}"
            ) from e
        except smtplib.SMTPServerDisconnected as e:
            raise SMTPConnectionError(f"SMTP server disconnected unexpectedly. Error: {e}") from e
        except (OSError, TimeoutError) as e:
            raise SMTPConnectionError(f"Network error connecting to SMTP server: {e}") from e

    def _authenticate(self, server: smtplib.SMTP) -> None:
        if not self.username or not self.password:
            return

        try:
            server.login(self.username, self.password)
        except smtplib.SMTPAuthenticationError as e:
            error_msg = (
                e.smtp_error.decode("utf-8", errors="replace") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
            )
            raise SMTPAuthenticationError(
                f"SMTP authentication failed for user '{self.username}'. "
                f"Please check credentials. Error code: {e.smtp_code}, Message: {error_msg}"
            ) from e
        except smtplib.SMTPException as e:
            raise SMTPAuthenticationError(f"Authentication error: {e}") from e

    def _attach_files(self, msg: MIMEMultipart, attachments: List[Path]) -> None:
        max_size_bytes = self.max_attachment_size_mb * 1024 * 1024

        for attachment_path in attachments:
            attachment_path = Path(attachment_path)

            if not attachment_path.exists():
                raise AttachmentError(f"Attachment file does not exist: {attachment_path}")

            if not attachment_path.is_file():
                raise AttachmentError(f"Attachment path is not a file: {attachment_path}")

            file_size = attachment_path.stat().st_size
            if file_size > max_size_bytes:
                raise AttachmentError(
                    f"Attachment file too large: {attachment_path}. "
                    f"Size: {file_size / 1024 / 1024:.2f} MB, "
                    f"Max allowed: {self.max_attachment_size_mb} MB"
                )

            try:
                with open(attachment_path, "rb") as f:
                    file_data = f.read()

                part = MIMEApplication(file_data, Name=attachment_path.name)
                part["Content-Disposition"] = f'attachment; filename="{attachment_path.name}"'
                msg.attach(part)

            except PermissionError as e:
                raise AttachmentError(f"Permission denied reading attachment: {attachment_path}") from e
            except OSError as e:
                raise AttachmentError(f"Error reading attachment {attachment_path}: {e}") from e

    @exception_wrapper()
    def send_email(
        self,
        subject: str,
        body: str,
        attachments: Optional[List[Path]] = None,
    ) -> None:
        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = self.to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if attachments:
            self._attach_files(msg, attachments)

        server = None
        try:
            server = self._create_server()
            self._authenticate(server)

            try:
                server.sendmail(self.from_email, self.to_email, msg.as_string())

            except smtplib.SMTPRecipientsRefused as e:
                raise SMTPRecipientRefusedError(
                    f"Recipient refused: {self.to_email}. "
                    f"The recipient's mail server rejected this email. "
                    f"Details: {e.recipients}"
                ) from e

            except smtplib.SMTPSenderRefused as e:
                error_message = e.smtp_error.decode("utf-8") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                raise SMTPSenderRefusedError(
                    f"Sender refused: {self.from_email}. Error code: {e.smtp_code}, Message: {error_message}"
                ) from e

            except smtplib.SMTPDataError as e:
                error_message = e.smtp_error.decode("utf-8") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                if e.smtp_code == 552:
                    raise SMTPMailboxFullError(
                        f"Recipient mailbox is full: {self.to_email}. "
                        f"The recipient needs to free up space. "
                        f"Error code: {e.smtp_code}"
                    ) from e
                elif e.smtp_code == 552 or "message too large" in error_message.lower():
                    raise SMTPMessageSizeError(
                        f"Message size exceeds server limit. Error code: {e.smtp_code}, Message: {error_message}"
                    ) from e
                else:
                    raise SMTPDataError(f"SMTP data error: Error code: {e.smtp_code}, Message: {error_message}") from e

            except smtplib.SMTPException as e:
                raise SMTPDataError(f"SMTP error while sending email: {e}") from e

        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
